from aws_cdk import (
    RemovalPolicy,
    aws_s3 as s3,
)
from constructs import Construct

from app_ecosystem.stacks.common_infra import CommonInfraStack


class AppSpecificStorageConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        common_infra: CommonInfraStack,
        app_config: dict,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        self.app_config = app_config

        # S3 bucket to host static assets for frontend of application
        # The bucket name must match the URL that serves the frontend
        self.static_assets_bucket = s3.Bucket(
            self,
            f"{self.app_config['name'].title()}StaticAssetsBucket",
            bucket_name=f"{self.app_config['name']}.{common_infra.networking.hosted_zone.zone_name}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
