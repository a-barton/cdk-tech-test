from aws_cdk import (
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_elasticloadbalancingv2_targets as elbv2_targets,
    aws_route53 as route53,
)
from constructs import Construct

ECS_TASK_PORT = 8000  # Default port for ECS tasks
RDS_PORT = 5432  # Default port for PostgreSQL RDS
EXISTING_ACM_CERTIFICATE_ARN = "<SOME_CERTIFICATE_ARN_HERE>"
INBOUND_VPN_TRAFFIC_CIDR = "10.0.0.0/16"  # Example CIDR for inbound VPN traffic
S3_VPC_ENDPOINT_IPS = {
    "10.128.0.1": "ap-southeast-2a",
    "10.128.1.1": "ap-southeast-2b",
}  # Example IPs for S3 VPC endpoint in a specific region


class CommonNetworkingConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        domain_name: str = "app-ecosystem.example.com",
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        self.ecs_task_port = ECS_TASK_PORT
        self.rds_port = RDS_PORT

        self.vpc = self.create_vpc()

        self.create_security_groups()
        self.configure_security_groups()

        self.alb = self.create_alb()

        self.rule_priority_bands = {}  # To avoid listener rule priority collisions

        self.http_listener, self.https_listener = self.create_listeners()

        self.hosted_zone = route53.HostedZone(self, "HostedZone", zone_name=domain_name)

        self.s3_vpc_endpoint_target_group = self.create_s3_vpc_endpoint_tg()

    def get_rule_priority_for_band(self, band_start: int) -> int:
        """Get the next available rule priority for a given band."""
        if band_start not in self.rule_priority_bands:
            self.rule_priority_bands[band_start] = band_start
        else:
            self.rule_priority_bands[band_start] += 1
        return self.rule_priority_bands[band_start]

    def create_vpc(self) -> ec2.Vpc:
        # VPC with 1 public subnet and 2 private subnets
        return ec2.Vpc(
            self,
            "Vpc",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Web", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Core",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="DB", subnet_type=ec2.SubnetType.PRIVATE_ISOLATED, cidr_mask=28
                ),
            ],
        )

    def create_security_groups(self):
        # Create security groups for ALB, RDS cluster and ECS services
        self.alb_sg = ec2.SecurityGroup(
            self,
            "ALBSecurityGroup",
            vpc=self.vpc,
            allow_all_outbound=False,
            description="Security group for Application Load Balancer",
        )

        self.db_sg = ec2.SecurityGroup(
            self,
            "DatabaseSecurityGroup",
            vpc=self.vpc,
            allow_all_outbound=False,
            description="Security group for RDS database",
        )

        self.ecs_sg = ec2.SecurityGroup(
            self,
            "ECSSecurityGroup",
            vpc=self.vpc,
            allow_all_outbound=False,
            description="Security group for ECS tasks",
        )

    def configure_security_groups(self):
        # Allow inbound traffic to ALB from VPN CIDR
        self.alb_sg.connections.allow_from(
            ec2.Peer.ipv4(INBOUND_VPN_TRAFFIC_CIDR),
            ec2.Port.tcp(443),
            "Allow inbound VPN traffic to ALB",
        )

        # Allow outbound traffic from ALB to S3 VPC endpoint
        for ip, az in S3_VPC_ENDPOINT_IPS.items():
            self.alb_sg.connections.allow_to(
                ec2.Peer.ipv4(ip + "/32"),
                ec2.Port.tcp(443),
                f"Allow ALB to access S3 VPC endpoint in {az}",
            )

        # Allow outbound traffic from ALB to ECS tasks
        self.alb_sg.connections.allow_to(
            self.ecs_sg,
            ec2.Port.tcp(self.ecs_task_port),
            "Allow ALB to forward traffic to ECS tasks",
        )

        # Allow inbound traffic to ECS tasks from ALB
        self.ecs_sg.connections.allow_from(
            self.alb_sg,
            ec2.Port.tcp(self.ecs_task_port),
            "Allow ECS tasks to receive traffic from ALB",
        )

        # Allow ECS tasks to connect to RDS database
        self.ecs_sg.connections.allow_to(
            self.db_sg,
            ec2.Port.tcp(self.rds_port),
            "Allow ECS tasks to connect to RDS database",
        )

        # Allow RDS database to accept connections from ECS tasks
        self.db_sg.connections.allow_from(
            self.ecs_sg,
            ec2.Port.tcp(self.rds_port),
            "Allow RDS database to accept connections from ECS tasks",
        )

    def create_alb(self) -> elbv2.ApplicationLoadBalancer:
        # Internal Application Load Balancer
        alb = elbv2.ApplicationLoadBalancer(
            self,
            "InternalALB",
            vpc=self.vpc,
            internet_facing=False,
            vpc_subnets=ec2.SubnetSelection(subnet_group_name="Web"),
            security_group=self.alb_sg,
        )

        alb.connections.allow_from(
            ec2.Peer.ipv4(INBOUND_VPN_TRAFFIC_CIDR),
            ec2.Port.tcp(443),
            "Allow inbound VPN traffic to ALB",
        )

        return alb

    def create_listeners(
        self,
    ) -> tuple[elbv2.ApplicationListener, elbv2.ApplicationListener]:
        # HTTPS Listener (port 443)
        self.https_listener = self.alb.add_listener(
            "HttpsListener",
            protocol=elbv2.ApplicationProtocol.HTTPS,
            port=443,
            open=True,
            certificates=[
                elbv2.ListenerCertificate.from_arn(EXISTING_ACM_CERTIFICATE_ARN)
            ],
            default_action=elbv2.ListenerAction.fixed_response(
                status_code=503,
                content_type="text/plain",
                message_body="Service Unavailable",
            ),
        )

        # HTTP Listener (port 80) with redirect to HTTPS
        self.http_listener = self.alb.add_listener(
            "HttpListener",
            port=80,
            open=True,
            default_action=elbv2.ListenerAction.redirect(protocol="HTTPS", port="443"),
        )

        return self.http_listener, self.https_listener

    def create_s3_vpc_endpoint_tg(self) -> elbv2.ApplicationTargetGroup:
        # Allow outbound traffic from ALB to S3 VPC endpoint
        for ip, az in S3_VPC_ENDPOINT_IPS.items():
            self.alb.connections.allow_to(
                ec2.Peer.ipv4(ip + "/32"),
                ec2.Port.tcp(443),
                f"Allow ALB to access S3 VPC endpoint in {az}",
            )

        # Target group for S3 VPC endpoint
        return elbv2.ApplicationTargetGroup(
            self,
            "S3VPCEndpointTargetGroup",
            vpc=self.vpc,
            port=443,
            target_type=elbv2.TargetType.IP,
            targets=[
                elbv2_targets.IpTarget(ip_address=ip)
                for ip in S3_VPC_ENDPOINT_IPS.keys()
            ],
        )
