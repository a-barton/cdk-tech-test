import os
import json

import aws_cdk as cdk

from app_ecosystem.stacks.common_infra import CommonInfraStack
from app_ecosystem.stacks.standard_app import StandardAppStack

cdk_app = cdk.App()

network_config_path = os.path.join(
    os.path.dirname(__file__), "app_ecosystem", "config", "network.json"
)
network_config = json.load(open(network_config_path))
common_infra = CommonInfraStack(
    cdk_app, construct_id="CommonInfraStack", network_config=network_config
)

app_configs_json_path = os.path.join(
    os.path.dirname(__file__), "app_ecosystem", "config", "apps.json"
)
app_configs = json.load(open(app_configs_json_path))
for app_config in app_configs["apps"]:
    app_stack = StandardAppStack(
        cdk_app,
        construct_id=f"{app_config['name'].title()}Stack",
        app_config=app_config,
        common_infra=common_infra,
    )

cdk_app.synth()
