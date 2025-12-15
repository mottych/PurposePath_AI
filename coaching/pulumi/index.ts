import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

// Table naming convention: purposepath-{table}-{stage}
const stage = "dev";
const accountId = "380276784420";
const region = "us-east-1";

const lambdaRole = new aws.iam.Role("coaching-lambda-role", {
    assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [{ Action: "sts:AssumeRole", Principal: { Service: "lambda.amazonaws.com" }, Effect: "Allow" }],
    }),
});

new aws.iam.RolePolicyAttachment("coaching-lambda-basic", {
    role: lambdaRole.name,
    policyArn: "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
});

new aws.iam.RolePolicy("coaching-dynamo-policy", {
    role: lambdaRole.id,
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [{
            Effect: "Allow",
            Action: ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:DeleteItem", "dynamodb:Query", "dynamodb:Scan"],
            Resource: [
                `arn:aws:dynamodb:${region}:${accountId}:table/purposepath-*`,
                `arn:aws:dynamodb:${region}:${accountId}:table/purposepath-*/index/*`,
            ],
        }],
    }),
});

// Bedrock access for LLM
new aws.iam.RolePolicy("coaching-bedrock-policy", {
    role: lambdaRole.id,
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [{
            Effect: "Allow",
            Action: ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
            Resource: "*",
        }],
    }),
});

// Python Lambda function
const coachingLambda = new aws.lambda.Function("coaching-api", {
    runtime: "python3.11",
    handler: "lambda_handler.handler",
    role: lambdaRole.arn,
    code: new pulumi.asset.FileArchive(".."),  // Package entire coaching directory
    timeout: 300,  // 5 minutes for LLM calls
    memorySize: 1024,
    environment: {
        variables: {
            // Table names are computed in code from STAGE: purposepath-{table}-{stage}
            STAGE: "dev",
        },
    },
});

const api = new aws.apigatewayv2.Api("coaching-api", {
    protocolType: "HTTP",
    corsConfiguration: {
        allowOrigins: ["*"],
        allowMethods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allowHeaders: ["*"],
        maxAge: 300,
    },
});

const integration = new aws.apigatewayv2.Integration("coaching-integration", {
    apiId: api.id,
    integrationType: "AWS_PROXY",
    integrationUri: coachingLambda.arn,
    payloadFormatVersion: "2.0",
});

new aws.apigatewayv2.Route("coaching-route", {
    apiId: api.id,
    routeKey: "$default",
    target: pulumi.interpolate`integrations/${integration.id}`,
});

new aws.apigatewayv2.Stage("coaching-stage", {
    apiId: api.id,
    name: "$default",
    autoDeploy: true,
});

new aws.lambda.Permission("coaching-api-permission", {
    action: "lambda:InvokeFunction",
    function: coachingLambda.name,
    principal: "apigateway.amazonaws.com",
    sourceArn: pulumi.interpolate`${api.executionArn}/*/*`,
});

const customDomain = aws.apigatewayv2.DomainName.get("existing-custom-domain", "api.dev.purposepath.app");

new aws.apigatewayv2.ApiMapping("coaching-api-mapping", {
    apiId: api.id,
    domainName: customDomain.id,
    stage: "$default",
    apiMappingKey: "coaching",
});

export const apiId = api.id;
export const customDomainUrl = "https://api.dev.purposepath.app/coaching";
export const lambdaArn = coachingLambda.arn;
