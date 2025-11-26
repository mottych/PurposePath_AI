import json

import pulumi_aws as aws
import pulumi_docker as docker

import pulumi

# Reference infrastructure stacks
infra = pulumi.StackReference("mottych/purposepath-infrastructure/dev")
coaching_infra = pulumi.StackReference("mottych/purposepath-coaching-infrastructure/dev")

jwt_secret_arn = infra.get_output("certificates").apply(lambda c: c["apiDev"])
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
    policy=json.dumps(
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
                        "arn:aws:dynamodb:us-east-1:380276784420:table/coaching_conversations",
                        "arn:aws:dynamodb:us-east-1:380276784420:table/coaching_conversations/index/*",
                        "arn:aws:dynamodb:us-east-1:380276784420:table/coaching_sessions",
                        "arn:aws:dynamodb:us-east-1:380276784420:table/coaching_sessions/index/*",
                        "arn:aws:dynamodb:us-east-1:380276784420:table/llm_prompts",
                        "arn:aws:dynamodb:us-east-1:380276784420:table/llm_prompts/index/*",
                    ],
                }
            ],
        }
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
    image_name=pulumi.Output.concat(ecr_repo.repository_url, ":latest"),
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
            "PROMPTS_BUCKET": prompts_bucket,
            "STAGE": "dev",
            "LOG_LEVEL": "INFO",
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

# Use existing custom domain
custom_domain = aws.apigatewayv2.DomainName.get("existing-custom-domain", "api.dev.purposepath.app")

aws.apigatewayv2.ApiMapping(
    "coaching-api-mapping",
    api_id=api.id,
    domain_name=custom_domain.id,
    stage=stage.name,
    api_mapping_key="coaching",
)

pulumi.export("apiId", api.id)
pulumi.export("customDomainUrl", "https://api.dev.purposepath.app/coaching")
pulumi.export("lambdaArn", coaching_lambda.arn)
