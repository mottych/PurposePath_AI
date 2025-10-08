#!/usr/bin/env python3
"""Seed the tiers and tenant overrides tables with initial data.

Usage:
  python scripts/seed_tiers.py --stage dev --region us-east-1

Environment variables (override):
  TIERS_TABLE, TENANT_OVERRIDES_TABLE
"""
import argparse
import json
import os
from pathlib import Path

import boto3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", default=os.environ.get("STAGE", "dev"))
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", "us-east-1"))
    args = parser.parse_args()

    tiers_table = os.environ.get("TIERS_TABLE") or f"purposepath-tiers-{args.stage}"
    overrides_table = os.environ.get("TENANT_OVERRIDES_TABLE") or f"purposepath-tenant-overrides-{args.stage}"

    with Path("scripts/seed_data/tiers.json").open("r", encoding="utf-8") as f:
        data = json.load(f)

    ddb = boto3.resource("dynamodb", region_name=args.region)  # type: ignore[misc]
    tiers = ddb.Table(tiers_table)

    for item in data["tiers"]:
        tiers.put_item(Item=item)
        print(f"Upserted tier: {item['tier']}")

    # Optionally seed overrides if present
    overrides = data.get("tenant_overrides", [])
    if overrides:
        ov_table = ddb.Table(overrides_table)
        for item in overrides:
            ov_table.put_item(Item=item)
            print(f"Upserted override for tenant: {item['tenant_id']}")

    print("Done.")


if __name__ == "__main__":
    main()

