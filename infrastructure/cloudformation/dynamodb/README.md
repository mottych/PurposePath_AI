# LLM Configuration DynamoDB Tables

Single CloudFormation template that creates both LLM configuration tables for any environment.

## Tables Created

1. **`prompt_templates_metadata_{environment}`** - Metadata for LLM prompt templates stored in S3
2. **`llm_configurations_{environment}`** - Active configuration mappings with tier support

## Deployment

### Deploy to Development
```bash
aws cloudformation deploy \
  --template-file llm-configuration-tables.yaml \
  --stack-name llm-config-tables-dev \
  --parameter-overrides Environment=dev \
  --region us-east-1
```

### Deploy to Staging
```bash
aws cloudformation deploy \
  --template-file llm-configuration-tables.yaml \
  --stack-name llm-config-tables-staging \
  --parameter-overrides Environment=staging \
  --region us-east-1
```

### Deploy to Production
```bash
aws cloudformation deploy \
  --template-file llm-configuration-tables.yaml \
  --stack-name llm-config-tables-production \
  --parameter-overrides Environment=production \
  --region us-east-1
```

## Table Details

### Prompt Templates Metadata Table

**Primary Key**: `template_id` (String)

**Global Secondary Indexes**:
- `interaction-index` - Query by `interaction_code`
- `code-index` - Query by `template_code`
- `active-index` - Query active templates

**Features**:
- Pay-per-request billing
- Point-in-time recovery enabled
- Server-side encryption (KMS)
- DynamoDB Streams enabled

### LLM Configurations Table

**Primary Key**: `config_id` (String)

**Global Secondary Indexes**:
- `interaction-tier-index` - Query by `interaction_code` + `tier` (supports tier-based lookup)
- `active-index` - Query active configurations

**Features**:
- Pay-per-request billing
- Point-in-time recovery enabled
- Server-side encryption (KMS)
- DynamoDB Streams enabled

## Stack Outputs

Each deployment exports the following:
- `{StackName}-PromptTemplatesTableName`
- `{StackName}-PromptTemplatesTableArn`
- `{StackName}-PromptTemplatesStreamArn`
- `{StackName}-ConfigurationsTableName`
- `{StackName}-ConfigurationsTableArn`
- `{StackName}-ConfigurationsStreamArn`
- `{StackName}-Environment`

## Updating Stacks

To update existing stacks:
```bash
aws cloudformation deploy \
  --template-file llm-configuration-tables.yaml \
  --stack-name llm-config-tables-{env} \
  --parameter-overrides Environment={env}
```

CloudFormation will automatically detect and apply only the necessary changes.

## Deleting Stacks

**WARNING**: This will delete all data in the tables!

```bash
aws cloudformation delete-stack --stack-name llm-config-tables-{env}
```
