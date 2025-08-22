
# CDK Tech Test

This is a toy example AWS CDK (for Python) codebase designed for the purposes of testing proficiency with AWS CDK, Python and AWS cloud infrastructure in general.

### Disclaimer
The CDK codebase in this repo is **NOT** intended to be a fully functional, deployable and standalone AWS cloud solution. It is purely for the purposes of testing AWS CDK proficiency, with the 'solution' to each exercise merely requiring that the `cdk synth` command succeeds, not that any actual cloud resources are deployed.

## Requirements/Dependencies
You must already have the following installed and available:
- Python
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- NodeJS (required to use the CDK CLI) - using [nvm](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating) to install NodeJS is recommend 
- [npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) (required to install CDK CLI) 
- [AWS CDK (Cloud Development Kit) CLI](https://docs.aws.amazon.com/cdk/v2/guide/cli.html)

## Setup
Assuming the abovementioned dependencies are installed, you can initialise this repo as follows:

### Sync local Python virtual environment with uv lockfile
```bash
uv sync
```

### Activate the Python virtual environment

On Linux/MacOS:
```bash
source .venv/bin/activate
```

On Windows:
```cmd
.venv\Scripts\activate.bat
```

### Confirm `cdk synth` command now works

You should now be able to use the CDK CLI to synthesise the CDK codebase into CloudFormation templates (synthesised template files will be emitted to a `cdk.out` directory):
```bash
cdk synth
```

## About CDK (AWS docs)

The `cdk.json` file tells the CDK Toolkit how to execute your app.

### Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

## Architecture

