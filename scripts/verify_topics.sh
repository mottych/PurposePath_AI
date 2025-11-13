#!/bin/bash
# Verify coaching topics were seeded correctly
# Usage: ./scripts/verify_topics.sh [environment]

set -e

ENV=${1:-dev}

echo "==========================================================================="
echo "Verifying Coaching Topics"
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

# Run verification script
echo "Running verification..."
python -m src.scripts.verify_coaching_topics

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "==========================================================================="
    echo "✓ All topics verified successfully"
    echo "==========================================================================="
else
    echo ""
    echo "==========================================================================="
    echo "✗ Verification failed"
    echo "==========================================================================="
    exit $EXIT_CODE
fi
