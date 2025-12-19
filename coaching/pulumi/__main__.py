import datetime
import json

import pulumi_aws as aws
import pulumi_docker as docker

import pulumi

# Get current stack
stack = pulumi.get_stack()

# Configuration based on stack
config = {
    "dev": {
        "infra_stack": "mottych/purposepath-infrastructure/dev",
        "coaching_infra_stack": "mottych/purposepath-coaching-infrastructure/dev",
        "api_domain": "api.dev.purposepath.app",
        "certificate_output": "apiDev",
        "jwt_secret": "purposepath-jwt-secret-dev",
        "jwt_issuer": "https://api.dev.purposepath.app",
        "jwt_audience": "https://dev.purposepath.app",
        "topics_table": "purposepath-topics-dev",
        "log_level": "INFO",
    },
    "staging": {
        "infra_stack": "mottych/purposepath-infrastructure/staging",
        "coaching_infra_stack": "mottych/purposepath-coaching-infrastructure/staging",
        "api_domain": "api.staging.purposepath.app",
        "certificate_output": "apiStaging",
        "jwt_secret": "purposepath-jwt-secret-staging",
        "jwt_issuer": "https://api.staging.purposepath.app",
        "jwt_audience": "https://staging.purposepath.app",
        "topics_table": "purposepath-topics-staging",
        "log_level": "INFO",
    },
    "prod": {
        "infra_stack": "mottych/purposepath-infrastructure/prod",
        "coaching_infra_stack": "mottych/purposepath-coaching-infrastructure/prod",
        "api_domain": "api.purposepath.app",
        "certificate_output": "apiProd",
        "jwt_secret": "purposepath-jwt-secret-prod",
        "jwt_issuer": "https://api.purposepath.app",
        "jwt_audience": "https://purposepath.app",
        "topics_table": "purposepath-topics-prod",
        "log_level": "WARNING",
    },
}

# Get stack specific config or default to dev if not found (safety fallback)
stack_config = config.get(stack, config["dev"])

# AI Jobs table name (for async execution)
ai_jobs_table = f"purposepath-ai-jobs-{stack}"

# Reference infrastructure stacks
infra = pulumi.StackReference(stack_config["infra_stack"])
coaching_infra = pulumi.StackReference(stack_config["coaching_infra_stack"])

# Certificate ARN from infrastructure stack
certificate_arn = infra.get_output("certificates").apply(
    lambda c: c.get(stack_config["certificate_output"])
)
prompts_bucket = coaching_infra.get_output("promptsBucket")

# IAM Role for Lambda
lambda_role = aws.iam.Role(
    "coaching-lambda-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Effect": "Allow",
                }
            ],
        }
    ),
)

aws.iam.RolePolicyAttachment(
    "coaching-lambda-basic",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
)

# DynamoDB table for AI jobs (async execution)
ai_jobs_dynamodb_table = aws.dynamodb.Table(
    "ai-jobs-table",
    name=ai_jobs_table,
    billing_mode="PAY_PER_REQUEST",
    hash_key="job_id",
    attributes=[
        aws.dynamodb.TableAttributeArgs(name="job_id", type="S"),
        aws.dynamodb.TableAttributeArgs(name="tenant_id", type="S"),
        aws.dynamodb.TableAttributeArgs(name="created_at", type="S"),
    ],
    global_secondary_indexes=[
        aws.dynamodb.TableGlobalSecondaryIndexArgs(
            name="tenant-user-index",
            hash_key="tenant_id",
            range_key="created_at",
            projection_type="ALL",
        ),
    ],
    ttl=aws.dynamodb.TableTtlArgs(
        attribute_name="ttl",
        enabled=True,
    ),
    tags={"Environment": stack, "Service": "coaching-ai"},
)

# DynamoDB access for all purposepath tables
# Table naming convention: purposepath-{table}-{stage}
aws.iam.RolePolicy(
    "coaching-dynamo-policy",
    role=lambda_role.id,
    policy=pulumi.Output.all(aws.get_caller_identity().account_id).apply(
        lambda args: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "dynamodb:GetItem",
                            "dynamodb:PutItem",
                            "dynamodb:UpdateItem",
                            "dynamodb:DeleteItem",
                            "dynamodb:Query",
                            "dynamodb:Scan",
                        ],
                        "Resource": [
                            f"arn:aws:dynamodb:us-east-1:{args[0]}:table/purposepath-*",
                            f"arn:aws:dynamodb:us-east-1:{args[0]}:table/purposepath-*/index/*",
                        ],
                    }
                ],
            }
        )
    ),
)

# Bedrock access for LLM
aws.iam.RolePolicy(
    "coaching-bedrock-policy",
    role=lambda_role.id,
    policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                    "Resource": "*",
                }
            ],
        }
    ),
)

# EventBridge access for publishing AI job events
aws.iam.RolePolicy(
    "coaching-eventbridge-policy",
    role=lambda_role.id,
    policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["events:PutEvents"],
                    "Resource": ["arn:aws:events:us-east-1:*:event-bus/default"],
                }
            ],
        }
    ),
)

# S3 access for prompts
aws.iam.RolePolicy(
    "coaching-s3-policy",
    role=lambda_role.id,
    policy=prompts_bucket.apply(
        lambda bucket: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
                        "Resource": [f"arn:aws:s3:::{bucket}", f"arn:aws:s3:::{bucket}/*"],
                    }
                ],
            }
        )
    ),
)

# Secrets Manager access for JWT secret and API keys
aws.iam.RolePolicy(
    "coaching-secrets-policy",
    role=lambda_role.id,
    policy=pulumi.Output.all(
        aws.get_caller_identity().account_id, stack_config["jwt_secret"]
    ).apply(
        lambda args: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["secretsmanager:GetSecretValue"],
                        "Resource": [
                            f"arn:aws:secretsmanager:us-east-1:{args[0]}:secret:{args[1]}-*",
                            f"arn:aws:secretsmanager:us-east-1:{args[0]}:secret:purposepath/*",
                        ],
                    }
                ],
            }
        )
    ),
)

# Create ECR repository
ecr_repo = aws.ecr.Repository(
    "coaching-repo",
    name="purposepath-coaching",
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=True
    ),
    force_delete=True,
)

# Build and push Docker image
auth_token = aws.ecr.get_authorization_token()

# Cache-busting: use timestamp to force rebuild
build_timestamp = datetime.datetime.utcnow().isoformat()

image = docker.Image(
    "coaching-image",
    build=docker.DockerBuildArgs(
        context="../..",  # pp_ai directory
        dockerfile="../Dockerfile",
        platform="linux/amd64",
        args={
            "BUILD_TIMESTAMP": build_timestamp,  # Force rebuild with timestamp
        },
    ),
    image_name=pulumi.Output.concat(ecr_repo.repository_url, ":", stack),
    registry=docker.RegistryArgs(
        server=ecr_repo.repository_url, username=auth_token.user_name, password=auth_token.password
    ),
    skip_push=False,
)

# Python Lambda function with Docker
# NOTE: Using repo_digest instead of image_name to ensure Lambda updates when image changes.
# image_name uses the tag (e.g., :dev) which doesn't change, so Pulumi doesn't detect updates.
# repo_digest uses the SHA256 digest which changes with each new image push.
coaching_lambda = aws.lambda_.Function(
    "coaching-api",
    package_type="Image",
    role=lambda_role.arn,
    image_uri=image.repo_digest,
    timeout=300,
    memory_size=1024,
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "CONVERSATIONS_TABLE": "coaching_conversations",
            "COACHING_SESSIONS_TABLE": "coaching_sessions",
            "TOPICS_TABLE": stack_config["topics_table"],
            "AI_JOBS_TABLE": ai_jobs_table,
            "PROMPTS_BUCKET": prompts_bucket,
            "STAGE": stack,
            "LOG_LEVEL": stack_config["log_level"],
            "JWT_SECRET_NAME": stack_config["jwt_secret"],
            "JWT_ISSUER": stack_config["jwt_issuer"],
            "JWT_AUDIENCE": stack_config["jwt_audience"],
        }
    ),
)

# API Gateway HTTP API
api = aws.apigatewayv2.Api(
    "coaching-api",
    protocol_type="HTTP",
    cors_configuration=aws.apigatewayv2.ApiCorsConfigurationArgs(
        allow_origins=["*"],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        max_age=300,
    ),
)

integration = aws.apigatewayv2.Integration(
    "coaching-integration",
    api_id=api.id,
    integration_type="AWS_PROXY",
    integration_uri=coaching_lambda.arn,
    payload_format_version="2.0",
    timeout_milliseconds=30000,  # Max 30 seconds for HTTP API (API Gateway limit)
)

aws.apigatewayv2.Route(
    "coaching-route",
    api_id=api.id,
    route_key="$default",
    target=integration.id.apply(lambda id: f"integrations/{id}"),
)

stage = aws.apigatewayv2.Stage("coaching-stage", api_id=api.id, name="$default", auto_deploy=True)

aws.lambda_.Permission(
    "coaching-api-permission",
    action="lambda:InvokeFunction",
    function=coaching_lambda.name,
    principal="apigateway.amazonaws.com",
    source_arn=api.execution_arn.apply(lambda arn: f"{arn}/*/*"),
)

# EventBridge rule to trigger job execution on ai.job.created events
# This enables reliable async execution by triggering a new Lambda invocation
# instead of using in-process asyncio.create_task() which doesn't survive handler completion
ai_job_executor_rule = aws.cloudwatch.EventRule(
    "ai-job-executor-rule",
    name=f"ai-job-executor-{stack}",
    description="Triggers AI job execution when ai.job.created events are published",
    event_bus_name="default",
    event_pattern=json.dumps(
        {
            "source": ["purposepath.ai"],
            "detail-type": ["ai.job.created"],
        }
    ),
    tags={"Environment": stack, "Service": "coaching-ai"},
)

# Target: invoke the coaching Lambda when ai.job.created event is received
aws.cloudwatch.EventTarget(
    "ai-job-executor-target",
    rule=ai_job_executor_rule.name,
    arn=coaching_lambda.arn,
    event_bus_name="default",
)

# Permission for EventBridge to invoke the Lambda
aws.lambda_.Permission(
    "eventbridge-invoke-permission",
    action="lambda:InvokeFunction",
    function=coaching_lambda.name,
    principal="events.amazonaws.com",
    source_arn=ai_job_executor_rule.arn,
)

# Use existing custom domain from infrastructure stack
# Domain: api.{stack}.purposepath.app (created by mottych/purposepath-infrastructure/{stack})
# Certificate: Already attached to domain
# This creates the API mapping at path: /coaching
custom_domain = aws.apigatewayv2.DomainName.get(
    "existing-custom-domain", stack_config["api_domain"]
)

aws.apigatewayv2.ApiMapping(
    "coaching-api-mapping",
    api_id=api.id,
    domain_name=custom_domain.id,
    stage=stage.name,
    api_mapping_key="coaching",  # Creates path: https://{api_domain}/coaching
)

pulumi.export("apiId", api.id)
pulumi.export(
    "customDomainUrl", pulumi.Output.concat("https://", stack_config["api_domain"], "/coaching")
)
pulumi.export("lambdaArn", coaching_lambda.arn)
pulumi.export("aiJobsTable", ai_jobs_dynamodb_table.name)
pulumi.export("aiJobsTableArn", ai_jobs_dynamodb_table.arn)
