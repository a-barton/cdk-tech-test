from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    Duration,
    RemovalPolicy,
)
from constructs import Construct

from app_ecosystem.constructs.common.networking import CommonNetworkingConstruct


class CommonStorageConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        common_networking: CommonNetworkingConstruct,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        # DB Credentials Secret
        self.db_creds_secret = rds.DatabaseSecret(
            self,
            "AppDatabaseCredentials",
            username="appuser",
            dbname="appdb",
        )

        # RDS Serverless Database Cluster
        self.db_cluster = rds.DatabaseCluster(
            self,
            "AppDatabaseCluster",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_17_5
            ),
            vpc=common_networking.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=common_networking.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
                ).subnets,
            ),
            security_groups=[common_networking.db_sg],
            credentials=rds.Credentials.from_secret(
                self.db_creds_secret,
            ),
            default_database_name="appdb",
            serverless_v2_min_capacity=0,
            serverless_v2_max_capacity=2,
            serverless_v2_auto_pause_duration=Duration.minutes(5),
            removal_policy=RemovalPolicy.DESTROY,
            writer=rds.ClusterInstance.serverless_v2("AppDatabaseWriter"),
        )
