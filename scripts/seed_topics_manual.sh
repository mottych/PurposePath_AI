#!/bin/bash
# Manually seed coaching topics (use for local testing or manual deployment)
# Usage: ./scripts/seed_topics_manual.sh [environment]

set -e

ENV=${1:-dev}

echo "==========================================================================="
echo "Seeding Coaching Topics"
echo "==========================================================================="
echo "Environment: $ENV"
echo ""

# Set environment variables
export AWS_PROFILE=purposepath-$ENV
export LLM_PROMPTS_TABLE=purposepath-llm-prompts-$ENV
export PROMPTS_BUCKET=purposepath-coaching-prompts-$ENV
export AWS_REGION=us-east-1
export STAGE=$ENV

echo "Configuration:"
echo "  AWS Profile: $AWS_PROFILE"
echo "  DynamoDB Table: $LLM_PROMPTS_TABLE"
echo "  S3 Bucket: $PROMPTS_BUCKET"
echo "  Region: $AWS_REGION"
echo ""

# Change to coaching directory
cd "$(dirname "$0")/../coaching"

# Run seed script
echo "Running seed script..."
python -m src.scripts.seed_coaching_topics

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "==========================================================================="
    echo "✓ Seeding completed successfully"
    echo "==========================================================================="
    echo ""
    echo "Next steps:"
    echo "  1. Run verification: ./scripts/verify_topics.sh $ENV"
    echo "  2. Check DynamoDB: aws dynamodb scan --table-name $LLM_PROMPTS_TABLE"
    echo "  3. Check S3: aws s3 ls s3://$PROMPTS_BUCKET/prompts/ --recursive"
else
    echo ""
    echo "==========================================================================="
    echo "✗ Seeding failed with exit code $EXIT_CODE"
    echo "==========================================================================="
    exit $EXIT_CODE
fi
