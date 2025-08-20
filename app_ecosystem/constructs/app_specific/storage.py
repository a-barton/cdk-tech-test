from aws_cdk import (
    RemovalPolicy,
    aws_s3 as s3,
    aws_iam as iam,
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
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Allow S3 VPC Endpoint to access the bucket
        self.static_assets_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                principals=[iam.AnyPrincipal()],
                actions=["s3:GetObject"],
                resources=[
                    self.static_assets_bucket.bucket_arn,
                    self.static_assets_bucket.arn_for_objects("*"),
                ],
                conditions={
                    "StringEquals": {
                        "aws:SourceVpce": common_infra.networking.s3_vpc_endpoint_id
                    }
                },
            )
        )
