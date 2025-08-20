from aws_cdk import (
    aws_ecs as ecs,
    aws_ec2 as ec2,
)
from constructs import Construct

from app_ecosystem.stacks.common_infra import CommonInfraStack


class AppSpecificComputeConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        common_infra: CommonInfraStack,
        app_config: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.app_config = app_config

        self.ecs_task_definition = ecs.FargateTaskDefinition(
            self,
            f"{self.app_config['name'].title()}ECSTaskDefinition",
            memory_limit_mib=self.app_config["total_task_memory"],
            cpu=self.app_config["total_task_cpu"],
        )

        self.ecs_task_definition.add_container(
            f"{self.app_config['name'].title()}ECSTaskContainer",
            image=ecs.ContainerImage.from_registry(
                self.app_config["backend_docker_image"]
            ),
            logging=ecs.LogDrivers.aws_logs(stream_prefix=self.app_config["name"]),
            port_mappings=[
                ecs.PortMapping(container_port=common_infra.networking.ecs_task_port)
            ],
            secrets={
                "DB_CREDS": ecs.Secret.from_secrets_manager(
                    common_infra.storage.db_creds_secret  # Creds to allow app backends to access RDS cluster
                ),
            },
        )

        self.ecs_service = ecs.FargateService(
            self,
            f"{self.app_config['name'].title()}ECSService",
            cluster=common_infra.compute.ecs_cluster,
            task_definition=self.ecs_task_definition,
            vpc_subnets=ec2.SubnetSelection(
                subnets=common_infra.networking.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets,
            ),
            security_groups=[common_infra.networking.ecs_sg],
            min_healthy_percent=0,
        )
