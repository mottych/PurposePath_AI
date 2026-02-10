"""Check what models are actually configured in DynamoDB for troubleshooting."""

import boto3
import json
from datetime import datetime, timezone

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("purposepath-coaching-sessions-dev")

# Scan for recent conversation configs to see what models are being used
response = table.scan(
    FilterExpression="begins_with(pk, :pk_prefix)",
    ExpressionAttributeValues={":pk_prefix": "TENANT#"},
    Limit=20,
)

print("Recent coaching configurations:")
print("=" * 80)

conversations_found = 0
configs_by_model = {}

for item in response.get("Items", []):
    # Check if this is a conversation or topic config
    if "topic_id" in item or "additional_config" in item:
        conversations_found += 1
        
        # Extract model info
        basic_model = item.get("basic_model_code", "N/A")
        premium_model = item.get("premium_model_code", "N/A")
        extraction_model = None
        
        if "additional_config" in item and isinstance(item["additional_config"], dict):
            extraction_model = item["additional_config"].get("extraction_model_code", "N/A")
        
        print(f"\nTopic ID: {item.get('topic_id', 'N/A')}")
        print(f"  Basic Model: {basic_model}")
        print(f"  Premium Model: {premium_model}")
        print(f"  Extraction Model: {extraction_model}")
        
        # Track which models are in use
        for model in [basic_model, premium_model, extraction_model]:
            if model and model != "N/A":
                configs_by_model[model] = configs_by_model.get(model, 0) + 1

print("\n" + "=" * 80)
print("Model Usage Summary:")
print("=" * 80)
for model, count in sorted(configs_by_model.items(), key=lambda x: x[1], reverse=True):
    print(f"  {model}: {count} configurations")

print(f"\nTotal conversations/topics found: {conversations_found}")

# Also check if there are any MODEL_REGISTRY references
print("\n" + "=" * 80)
print("Checking MODEL_REGISTRY for CLAUDE_3_5_HAIKU...")
print("=" * 80)

from coaching.src.core.llm_models import MODEL_REGISTRY

haiku_models = {k: v for k, v in MODEL_REGISTRY.items() if "HAIKU" in k}
print(f"Available Haiku models in registry:")
for code, model in haiku_models.items():
    print(f"  {code}: {model.model_name}")

if "CLAUDE_3_5_HAIKU" not in MODEL_REGISTRY:
    print("\n⚠️  WARNING: CLAUDE_3_5_HAIKU is NOT in MODEL_REGISTRY!")
    print("   This will cause ModelNotFoundError when extracting results.")
    print("   The code references CLAUDE_3_5_HAIKU but only CLAUDE_3_HAIKU exists.")
