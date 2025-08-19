from aws_cdk import (
    aws_cognito as cognito,
)
from constructs import Construct


class AppSpecificAuthConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        app_config: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.app_config = app_config

        self.user_pool = cognito.UserPool(
            self,
            f"{self.app_config['name'].title()}UserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
        )

        self.user_pool_client = cognito.UserPoolClient(
            self,
            f"{self.app_config['name'].title()}UserPoolClient",
            user_pool=self.user_pool,
            generate_secret=True,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                admin_user_password=True,
            ),
        )

        self.user_pool_domain = cognito.UserPoolDomain(
            self,
            f"{self.app_config['name'].title()}UserPoolDomain",
            user_pool=self.user_pool,
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f"{self.app_config['name']}-auth"
            ),
        )
