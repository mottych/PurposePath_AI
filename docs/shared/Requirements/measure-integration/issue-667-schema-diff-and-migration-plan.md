# Issue #667 - Schema Diff and Migration/Backfill Plan

## Scope
This document captures the implemented schema/model delta for #667 and the migration/backfill approach for existing records.

## 1) Schema Diff (Existing -> Target)

### MeasureCatalog
- Added `business_definition` (nullable)
  - Domain: `MeasureCatalog.BusinessDefinition`
  - Data model: `MeasureCatalogDataModel.BusinessDefinition`

### Measure
- Added `business_definition_override` (nullable)
  - Domain: `Measure.BusinessDefinitionOverride`
  - Data model: `MeasureDataModel.BusinessDefinitionOverride`

### MeasureIntegration
- Added SQL lifecycle metadata (all nullable unless noted):
  - `definition_version`
  - `definition_hash`
  - `previous_definition_version`
  - `previous_definition_hash`
  - `requires_template_regeneration` (bool, default false)
  - `regeneration_reason_code`
  - `sql_template_hash`
  - `query_artifact_ref`
  - `sql_template_generation_status` (string enum, default `Pending`)
  - `last_sql_template_generated_at`
  - `last_generation_error_code`
  - `last_generation_error_stage`
  - `last_generation_error_message`

### ConnectionConfiguration
- Added external reference model fields:
  - `external_provider`
  - `external_connection_id`
  - `workspace_context`
- Added validation diagnostics:
  - `last_validation_error`

### SystemMeasureConfig
- Added intent/constraint metadata:
  - `ai_topic`
  - `system_constraints_json`

## 2) Index/GSI Impact Assessment
- No new query paths were introduced in #667 that require immediate GSI additions.
- Existing GSIs remain valid:
  - `purposepath-system-measure-configs`: `system-index`, `measure-catalog-index`
  - `purposepath-connection-configurations`: `tenant-index`, `system-index`
  - `purposepath-measure-integrations`: `measure-index`, `connection-index`, `tenant-index`
- Pulumi updates are **not required** for this slice because DynamoDB is schemaless for non-key attributes and no new key/index access patterns were added.

## 3) Migration and Backfill Plan

### 3.1 Safety
- Do not delete or rewrite legacy credential fields in-place.
- Keep old fields readable while new external-reference fields are populated.
- Run migration in idempotent batches by tenant.

### 3.2 Backfill Steps
1. `MeasureCatalog`
   - For records with empty `business_definition`, leave null.
   - Optional enrichment can be done later from curated catalog metadata.

2. `Measure`
   - Set `business_definition_override` only when explicit tenant/measure overrides exist.
   - Default remains null.

3. `MeasureIntegration`
   - Initialize defaults when fields are missing:
     - `requires_template_regeneration = false`
     - `sql_template_generation_status = Pending`
   - Keep lifecycle hashes/versions null until first template generation flow runs.

4. `ConnectionConfiguration`
   - Legacy records with encrypted credentials:
     - retain `encrypted_credentials` unchanged
     - set `external_provider` / `external_connection_id` only when mapping to known CData references is available
   - Non-mappable legacy records:
     - set `validation_status = Invalid`
     - populate `last_validation_error` with remediation hint

5. `SystemMeasureConfig`
   - Initialize `ai_topic` and `system_constraints_json` as null for existing records.
   - Populate incrementally during system-specific configuration updates.

### 3.3 Verification
- Build and domain tests must pass after migration tools/scripts are introduced.
- Spot-check by tenant:
  - query active connections and verify external-reference fields are either valid or explicitly flagged.
  - query measure integrations and verify lifecycle defaults are present.

## 4) Rollout Notes
- Deploy code first (backward compatible).
- Run backfill in dev stack.
- Validate read paths and integration execution behavior.
- Promote to higher environments after verification.
