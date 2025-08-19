from aws_cdk import (
    aws_ecs as ecs,
)
from constructs import Construct

from app_ecosystem.constructs.common.networking import CommonNetworkingConstruct


class CommonComputeConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        common_networking: CommonNetworkingConstruct,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # Common ECS Cluster to host all application backends as separate ECS services
        self.ecs_cluster = ecs.Cluster(
            self,
            "AppECSCluster",
            vpc=common_networking.vpc,
            enable_fargate_capacity_providers=True,
        )
