# LLM Configuration Management Scripts

This directory contains scripts for managing LLM configurations, templates, and migrations for the PurposePath AI Coaching Service.

## Overview

The LLM configuration system uses a three-tier architecture:

1. **Code Registries** (Immutable): `llm_interactions.py` and `llm_models.py` define available interactions and models
2. **Database** (Mutable): DynamoDB stores configuration records linking interactions to templates and models
3. **S3 Templates** (Versioned): Jinja2 templates stored in S3 with metadata in DynamoDB

## Scripts

### 1. `seed_templates.py`
Uploads Jinja2 templates to S3 and creates metadata records in DynamoDB.

**Usage:**
```bash
python scripts/llm_config/seed_templates.py \
    --templates-dir ./templates \
    --bucket purposepath-prompts-dev \
    --environment dev
```

**Features:**
- Validates templates exist for all interactions
- Validates Jinja2 syntax
- Extracts and validates template parameters
- Uploads to S3 with versioning
- Creates metadata records

### 2. `seed_configurations.py`
Creates LLM configuration records in DynamoDB.

**Usage:**
```bash
python scripts/llm_config/seed_configurations.py \
    --config-file ./configs/llm_configs_dev.yaml \
    --environment dev
```

**Features:**
- Validates interaction codes against INTERACTION_REGISTRY
- Validates model codes against MODEL_REGISTRY
- Validates template IDs exist in database
- Ensures only one active config per interaction+tier
- Deactivates previous configurations
- Reports estimated costs

### 3. `migrate_existing_configs.py`
Scans codebase for hardcoded configurations and generates migration YAML.

**Usage:**
```bash
python scripts/llm_config/migrate_existing_configs.py \
    --scan-dir ./coaching/src \
    --output-file ./configs/migration_configs.yaml
```

**Features:**
- Scans for hardcoded model IDs
- Identifies DEFAULT_LLM_MODELS usage
- Generates migration YAML file
- Reports missing interactions

### 4. `validate_configuration.py`
Performs comprehensive validation of the entire LLM configuration system.

**Usage:**
```bash
python scripts/llm_config/validate_configuration.py \
    --environment dev \
    --bucket purposepath-prompts-dev
```

**Validation Checks:**
1. ✅ Code registries populated
2. ✅ All interactions have templates
3. ✅ All interactions have active configurations
4. ✅ All templates accessible in S3
5. ✅ All config references valid
6. ✅ No orphaned records
7. ✅ End-to-end template rendering tests

### 5. `rollback_configuration.py`
Manages configuration snapshots and rollbacks.

**Usage:**
```bash
# Create snapshot
python scripts/llm_config/rollback_configuration.py \
    --action snapshot \
    --environment dev \
    --snapshot-name "pre-production-update"

# List snapshots
python scripts/llm_config/rollback_configuration.py \
    --action list \
    --environment dev

# Rollback
python scripts/llm_config/rollback_configuration.py \
    --action rollback \
    --environment dev \
    --snapshot-name "pre-production-update"
```

### 6. `seed_all.ps1` (Master Script)
Orchestrates the complete seeding process.

**Usage:**
```powershell
.\scripts\llm_config\seed_all.ps1 -Environment dev

# With custom paths
.\scripts\llm_config\seed_all.ps1 `
    -Environment dev `
    -TemplatesDir .\templates `
    -Bucket purposepath-prompts-dev `
    -ConfigFile .\configs\llm_configs_dev.yaml
```

**Steps:**
1. Validates code registries
2. Seeds templates to S3
3. Seeds configurations to DynamoDB
4. Validates entire system

## Configuration Files

### Sample Configuration
See `configs/llm_configs_sample.yaml` for a complete example with all 14 interactions.

**Required Fields:**
- `interaction_code`: Must exist in INTERACTION_REGISTRY
- `template_id`: Must exist in template metadata table
- `model_code`: Must exist in MODEL_REGISTRY
- `temperature`: Float (0.0 - 2.0)
- `max_tokens`: Integer > 0

**Optional Fields:**
- `tier`: Subscription tier (null = all tiers)
- `top_p`: Float (0.0 - 1.0)
- `frequency_penalty`: Float (-2.0 - 2.0)
- `presence_penalty`: Float (-2.0 - 2.0)

### Template Files
Templates should be placed in `./templates/` with naming convention:
```
{INTERACTION_CODE}.jinja2
```

Example:
```
templates/
├── ALIGNMENT_ANALYSIS.jinja2
├── COACHING_RESPONSE.jinja2
├── STRATEGY_ANALYSIS.jinja2
└── ...
```

## Workflow

### Initial Setup (First Time)
```bash
# 1. Activate venv
.\.venv\Scripts\Activate.ps1

# 2. Create templates directory
mkdir templates

# 3. Create template files for all 14 interactions
# (Use sample templates or create custom ones)

# 4. Create configuration file
cp configs\llm_configs_sample.yaml configs\llm_configs_dev.yaml

# 5. Run master script
.\scripts\llm_config\seed_all.ps1 -Environment dev

# 6. Verify
python scripts/llm_config/validate_configuration.py --environment dev --bucket purposepath-prompts-dev
```

### Production Deployment
```bash
# 1. Create snapshot before changes
python scripts/llm_config/rollback_configuration.py \
    --action snapshot \
    --environment production \
    --snapshot-name "pre-v2-update" \
    --description "Before major config update"

# 2. Run seeding
.\scripts\llm_config\seed_all.ps1 -Environment production

# 3. Validate
python scripts/llm_config/validate_configuration.py \
    --environment production \
    --bucket purposepath-prompts-production

# 4. If issues, rollback
python scripts/llm_config/rollback_configuration.py \
    --action rollback \
    --environment production \
    --snapshot-name "pre-v2-update"
```

### Updating Configurations
```bash
# 1. Modify configs/llm_configs_dev.yaml

# 2. Seed only configs (skip templates)
.\scripts\llm_config\seed_all.ps1 -Environment dev -SkipTemplates

# 3. Validate
python scripts/llm_config/validate_configuration.py --environment dev --bucket purposepath-prompts-dev
```

## Code Registries

### Interactions Registry
Location: `coaching/src/core/llm_interactions.py`

**All 14 Supported Interactions:**
- ALIGNMENT_ANALYSIS
- STRATEGY_ANALYSIS
- KPI_ANALYSIS
- COACHING_RESPONSE
- ALIGNMENT_EXPLANATION
- ALIGNMENT_SUGGESTIONS
- STRATEGIC_ALIGNMENT
- ROOT_CAUSE_ANALYSIS
- ACTION_SUGGESTIONS
- PRIORITIZATION_SUGGESTIONS
- SCHEDULING_SUGGESTIONS
- INSIGHTS_GENERATION
- ONBOARDING_SUGGESTIONS
- WEBSITE_SCAN

### Models Registry
Location: `coaching/src/core/llm_models.py`

**Supported Models:**
- CLAUDE_3_5_SONNET (Best quality)
- CLAUDE_3_SONNET (Balanced)
- CLAUDE_3_HAIKU (Fast & cheap)

## Validation & Testing

### Pre-Commit Checks
```bash
# Linting
python -m ruff check scripts/llm_config/

# Type checking
python -m mypy scripts/llm_config/ --explicit-package-bases

# Formatting
python -m ruff format scripts/llm_config/
```

### Integration Testing
```bash
# Run validation script
python scripts/llm_config/validate_configuration.py \
    --environment dev \
    --bucket purposepath-prompts-dev

# Check all validations pass:
# ✅ Code Registries
# ✅ Interactions Have Templates
# ✅ Interactions Have Configurations
# ✅ Templates Accessible in S3
# ✅ Configuration References Valid
# ✅ No Orphaned Records
# ✅ End-to-End Template Rendering
```

## Troubleshooting

### Templates Not Found
**Error:** `Template file not found: templates/ALIGNMENT_ANALYSIS.jinja2`

**Solution:**
1. Create template file with proper naming
2. Ensure file has `.jinja2` extension
3. Verify file contains valid Jinja2 syntax

### Configuration Validation Failed
**Error:** `Invalid interaction_code: 'UNKNOWN_CODE'`

**Solution:**
1. Check `coaching/src/core/llm_interactions.py`
2. Use exact interaction code from INTERACTION_REGISTRY
3. Add new interaction to registry if needed (requires code deployment)

### Template Not Found in Database
**Error:** `Template not found: 'ALIGNMENT_ANALYSIS_V1_DEV'`

**Solution:**
1. Run `seed_templates.py` first
2. Verify template ID matches convention
3. Check DynamoDB table `prompt_templates_metadata`

### S3 Access Denied
**Error:** `Access Denied for s3://bucket/key`

**Solution:**
1. Verify AWS credentials configured
2. Check bucket exists and has correct permissions
3. Verify IAM role has S3 read/write access

## Environment Variables

The scripts use standard AWS configuration:
- `AWS_PROFILE`: AWS profile to use
- `AWS_REGION`: AWS region (default: us-east-1)
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key

## Best Practices

1. **Always create snapshots** before production changes
2. **Validate after seeding** using validation script
3. **Use tier-based configs** for premium features
4. **Test in dev** before deploying to production
5. **Version templates** when making major changes
6. **Document changes** in snapshot descriptions
7. **Monitor costs** using estimated cost reports
8. **Keep registries in sync** between environments

## Support

For issues or questions:
1. Check this README first
2. Review script help: `python script.py --help`
3. Check validation report for specific errors
4. Review code registries for available options

## Related Documentation

- Issue #73: Seeding & Management Scripts
- Issue #68: Code Registries & DynamoDB Tables
- Issue #69: Repositories Implementation
- `docs/Design/LLM_SERVICE_CONFIGURATION_INTEGRATION.md`: System architecture
