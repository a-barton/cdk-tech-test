from aws_cdk import (
    Stack,
)
from constructs import Construct

from app_ecosystem.stacks.common_infra import CommonInfraStack

from app_ecosystem.constructs.app_specific.auth import AppSpecificAuthConstruct
from app_ecosystem.constructs.app_specific.storage import AppSpecificStorageConstruct
from app_ecosystem.constructs.app_specific.compute import AppSpecificComputeConstruct
from app_ecosystem.constructs.app_specific.networking import (
    AppSpecificNetworkingConstruct,
)


class StandardAppStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_config: dict,
        common_infra: CommonInfraStack,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.app_config = app_config

        self.auth = AppSpecificAuthConstruct(
            self,
            f"{self.app_config['name'].title()}AppAuth",
            app_config=self.app_config,
        )

        self.storage = AppSpecificStorageConstruct(
            self,
            f"{self.app_config['name'].title()}AppStorage",
            common_infra=common_infra,
            app_config=self.app_config,
        )

        self.compute = AppSpecificComputeConstruct(
            self,
            f"{self.app_config['name'].title()}AppCompute",
            common_infra=common_infra,
            app_config=self.app_config,
        )

        self.networking = AppSpecificNetworkingConstruct(
            self,
            f"{self.app_config['name'].title()}AppNetworking",
            common_infra=common_infra,
            app_compute=self.compute,
            app_auth=self.auth,
            app_config=self.app_config,
        )
