from aws_cdk import (
    Stack,
)
from constructs import Construct

from app_ecosystem.constructs.common.networking import CommonNetworkingConstruct
from app_ecosystem.constructs.common.storage import CommonStorageConstruct
from app_ecosystem.constructs.common.compute import CommonComputeConstruct


class CommonInfraStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.networking = CommonNetworkingConstruct(
            self,
            "CommonNetworking",
            domain_name="app-ecosystem.example.com",
        )

        self.storage = CommonStorageConstruct(
            self,
            "CommonStorage",
            common_networking=self.networking,
        )

        self.compute = CommonComputeConstruct(
            self,
            "CommonCompute",
            common_networking=self.networking,
        )
