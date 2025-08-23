# CDK Tech Test
Below you will find a series of exercises to be completed as part of this tech test.

## Housekeeping

### Solution Submission
The exact mechanism of how you submit your solution(s) to this tech test is open to your preference. The main options would be:
- You fork the original repo into your own GitHub (or other code collaboration platform) repo
    - If you make the forked repo public, you can just share a direct link to it as your submission
    - If you make the forked repo private, you will need to share access somehow
- You create a git bundle of your version of the repo (with your exercise solutions implemented) and submit the bundle file itself

### Exercise Separation
Please ensure each exercise solution is implemented separately, the mechanism of how is up to you, e.g.:
- Separate branches (relevantly named)
- Separate pull requests, opened within abovementioned GitHub (or other code collaboration platform) repo of your own

### Solution Expectation
- Your solution to each exercise should be able to successfully synthesise the CDK codebase into CloudFormation templates - i.e. running `cdk synth` should succeed on the given branch.
- Don't worry about attempting to DEPLOY any of the synthesised CloudFormation templates.

## Exercise 1 - Implement validation of CPU and memory values specified for each app ECS task
### Motivation
AWS ECS Fargate task definitions [only support specific combinations of CPU/memory](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html) configurations, but CDK itself will not enforce this at synthesis time. This means we could accidentally set invalid CPU/memory configurations for our app backend ECS tasks (within `app_ecosystem/config/apps.json`) and we would only encounter the error when we try to deploy the synthesised CloudFormation templates.

### Task
Implement validation logic that checks the specified ECS task CPU/memory values in each app config, and ensures they align with the officially supported CPU and memory combinations from the AWS docs page mentioned above.

### Requirements
- The validation logic should throw an exception if any of the app configs specify an invalid CPU/memory configuration
- The exception thrown should contain a meaningful error message that mentions the offending app name and the offending CPU/memory values
- The acceptable CPU/memory configurations should be defined in such a way as to be easily modifiable/extendable in the future (if and when AWS changes them)

## Exercise 2 - Support multiple containers per app backend ECS task
### Motivation
Suppose our backend developers want to implement a sidecar container for each app backend, such as an [OpenTelemetry collector](https://opentelemetry.io/docs/collector/) for logs & metrics.

Or perhaps the sidecar container would be for task scheduling functionality (using something like the [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html) Python package). 

Currently the CDK codebase only supports defining a singular Docker container for each app backend's ECS task.

### Task

Extend the CDK codebase to support defining MULTIPLE containers for each app backend's ECS task.

Replace the existing content of `app_ecosystem/config/apps.json` with the following, which now includes a `containers` key for each app config that specifies a list/array of container definitions (note the docker image URI is no longer present at the parent level of the app config, but is now instead in each container definition):

```json
{
    "apps": [
        {
            "name": "daedalus",
            "alb_priority_band": 100,
            "total_task_cpu": 512,
            "total_task_memory": 1024,
            "containers": [
                {
                    "container_name": "daedalus-backend",
                    "docker_image": "docker.io/strm/helloworld-http:latest",
                    "container_cpu": 512,
                    "container_memory": 1024
                }
            ]
        },
        {
            "name": "icarus",
            "alb_priority_band": 200,
            "total_task_cpu": 1024,
            "total_task_memory": 2048,
            "containers": [
                {
                    "container_name": "icarus-backend",
                    "docker_image": "docker.io/strm/helloworld-http:latest",
                    "container_cpu": 512,
                    "container_memory": 1024
                },
                {
                    "container_name": "icarus-otel-collector",
                    "docker_image": "docker.io/otel/opentelemetry-collector-contrib:latest",
                    "container_cpu": 512,
                    "container_memory": 1024
                },
            ]
        },
        {
            "name": "theseus",
            "alb_priority_band": 300,
            "total_task_cpu": 512,
            "total_task_memory": 1024,
            "containers": [
                {
                    "container_name": "theseus-backend",
                    "docker_image": "docker.io/strm/helloworld-http:latest",
                    "container_cpu": 512,
                    "container_memory": 1024
                }
            ]
        }
    ]
}
```

### Requirements
- The solution should still support app configs that only specify one container, as well as those that specify multiple containers.
- The first container in the list should be considered the 'primary' container (the main application backend) and should be assigned the main ECS task port.
- Each subsequent container should be assigned an incremental port number so they don't collide.


## Exercise 3 - Add a common Valkey cache cluster
### Motivation
Suppose we have decided to build caching functionality into each of the apps, and therefore we'd like each of the app backend ECS tasks to have access to a cache. 

We have decided to go with Valkey as the cache solution, and we would like to use a managed serverless offering - an AWS Elasticache Valkey serverless cluster. 

Rather than deploying and paying for entirely separate Valkey caches for each app, we would like to try deploying a single shared Valkey cache cluster that all app backends can utilise.

### Task
Extend the existing CDK codebase to define an AWS Elasticache Valkey serverless cluster (using the [CfnServerlessCache](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_elasticache.CfnServerlessCache.html) CDK construct), and enable each of the app backend ECS tasks to access said cache cluster.

### Requirements
- The cache cluster must only be privately accesible within the existing VPC.
- The cache cluster must have its own security group - all security groups must be configured correctly to facilitate traffic FROM the app backend ECS tasks TO the cache cluster.
- Traffic to the cache cluster must be over port 6379.
- The app backend ECS tasks need to be provided with the cache cluster's endpoint address, such that each application backend knows how to reach the cache - the exact mechanism of how is up to you.

## Exercise 4 - Any suggestions or critique?
Do you think this IaC approach could be improved, optimised or potentially even completely reworked?

If so, please document your suggestions/critique (e.g. within a new markdown file at the root of the repo).

For each suggestion/critique please include:
- Your rationale for why the current approach is problematic or lacking.
- A description of how exactly you would suggest it be modified or reworked.
- Your rationale for why your proposed change would improve the approach.