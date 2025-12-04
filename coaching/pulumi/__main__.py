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

aws.iam.RolePolicy(
    "coaching-dynamo-policy",
    role=lambda_role.id,
    policy=pulumi.Output.all(
        aws.get_caller_identity().account_id, stack_config["topics_table"]
    ).apply(
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
                            f"arn:aws:dynamodb:us-east-1:{args[0]}:table/coaching_conversations",
                            f"arn:aws:dynamodb:us-east-1:{args[0]}:table/coaching_conversations/index/*",
                            f"arn:aws:dynamodb:us-east-1:{args[0]}:table/coaching_sessions",
                            f"arn:aws:dynamodb:us-east-1:{args[0]}:table/coaching_sessions/index/*",
                            f"arn:aws:dynamodb:us-east-1:{args[0]}:table/llm_prompts",
                            f"arn:aws:dynamodb:us-east-1:{args[0]}:table/llm_prompts/index/*",
                            f"arn:aws:dynamodb:us-east-1:{args[0]}:table/{args[1]}",
                            f"arn:aws:dynamodb:us-east-1:{args[0]}:table/{args[1]}/index/*",
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

image = docker.Image(
    "coaching-image",
    build=docker.DockerBuildArgs(
        context="../..",  # pp_ai directory
        dockerfile="../Dockerfile",
        platform="linux/amd64",
    ),
    image_name=pulumi.Output.concat(ecr_repo.repository_url, ":", stack),
    registry=docker.RegistryArgs(
        server=ecr_repo.repository_url, username=auth_token.user_name, password=auth_token.password
    ),
)

# Python Lambda function with Docker
coaching_lambda = aws.lambda_.Function(
    "coaching-api",
    package_type="Image",
    role=lambda_role.arn,
    image_uri=image.image_name,
    timeout=300,
    memory_size=1024,
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "CONVERSATIONS_TABLE": "coaching_conversations",
            "COACHING_SESSIONS_TABLE": "coaching_sessions",
            "LLM_PROMPTS_TABLE": "llm_prompts",
            "TOPICS_TABLE": stack_config["topics_table"],
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
