from aws_cdk import (
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_elasticloadbalancingv2_targets as elbv2_targets,
    aws_route53 as route53,
    aws_certificatemanager as acm,
)
from constructs import Construct


class CommonNetworkingConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        network_config: dict,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        self.network_config = network_config
        self.ecs_task_port = network_config.get("ecs_task_port", 8000)

        self.vpc = self.create_vpc()

        self.hosted_zone = route53.PrivateHostedZone(
            self,
            "HostedZone",
            zone_name=self.network_config["domain_name"],
            vpc=self.vpc,
        )

        self.acm_certificate = acm.Certificate(
            self,
            "AcmCertificate",
            domain_name=self.network_config["domain_name"],
            validation=acm.CertificateValidation.from_dns(self.hosted_zone),
            subject_alternative_names=[f"*.{self.network_config['domain_name']}"],
        )

        self.create_security_groups()
        self.configure_security_groups()

        self.alb = self.create_alb()

        self.rule_priority_bands = {}  # To avoid listener rule priority collisions

        self.http_listener, self.https_listener = self.create_listeners()

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
            ip_addresses=ec2.IpAddresses.cidr(self.network_config["vpc_cidr"]),
            restrict_default_security_group=True,
            max_azs=2,
            nat_gateways=1,
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
            ec2.Peer.ipv4(self.network_config["inbound_vpn_traffic_cidr"]),
            ec2.Port.tcp(443),
            "Allow inbound VPN traffic to ALB",
        )

        # Allow outbound traffic from ALB to S3 VPC endpoint
        for ip in self.network_config["s3_vpc_endpoint_ips"]:
            self.alb_sg.connections.allow_to(
                ec2.Peer.ipv4(ip + "/32"),
                ec2.Port.tcp(443),
                f"Allow ALB to access S3 VPC endpoint IP {ip}",
            )

        # Allow outbound traffic from ALB to ECS tasks
        self.alb_sg.connections.allow_to(
            self.ecs_sg,
            ec2.Port.tcp(self.network_config["ecs_task_port"]),
            "Allow ALB to forward traffic to ECS tasks",
        )

        # Allow inbound traffic to ECS tasks from ALB
        self.ecs_sg.connections.allow_from(
            self.alb_sg,
            ec2.Port.tcp(self.network_config["ecs_task_port"]),
            "Allow ECS tasks to receive traffic from ALB",
        )

        # Allow ECS tasks to connect to RDS database
        self.ecs_sg.connections.allow_to(
            self.db_sg,
            ec2.Port.tcp(self.network_config["rds_port"]),
            "Allow ECS tasks to connect to RDS database",
        )

        # Allow RDS database to accept connections from ECS tasks
        self.db_sg.connections.allow_from(
            self.ecs_sg,
            ec2.Port.tcp(self.network_config["rds_port"]),
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
            ec2.Peer.ipv4(self.network_config["inbound_vpn_traffic_cidr"]),
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
            certificates=[self.acm_certificate],
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
        for ip in self.network_config["s3_vpc_endpoint_ips"]:
            self.alb.connections.allow_to(
                ec2.Peer.ipv4(ip + "/32"),
                ec2.Port.tcp(443),
                f"Allow ALB to access S3 VPC endpoint IP {ip}",
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
                for ip in self.network_config["s3_vpc_endpoint_ips"]
            ],
        )
