# Issue 297 Validation - Claude Haiku 4.5 Migration

## Scope

Issue: `#297`  
Objective: add Claude Haiku 4.5 support, migrate extraction fallback to Haiku 4.5, and deactivate legacy Haiku 3/3.5 from active model selection.

## Authoritative References

- [Anthropic Models Overview](https://docs.anthropic.com/en/docs/about-claude/models/whats-new-claude-4-5)
- [AWS Bedrock Supported Model IDs](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html)

Confirmed model identifier used in code:

- `anthropic.claude-haiku-4-5-20251001-v1:0`

## Implementation Coverage

- Added `CLAUDE_HAIKU_4_5` to `MODEL_REGISTRY` as an active Bedrock model.
- Marked `CLAUDE_3_HAIKU` and `CLAUDE_3_5_HAIKU` as inactive to remove them from active model selection paths.
- Updated extraction default/fallback to `CLAUDE_HAIKU_4_5`.
- Updated Bedrock provider supported/inference-profile/cache model lists to include Haiku 4.5.
- Updated admin topic conversation config documentation and schema text for extraction default.

## Validation Commands

```powershell
python -m ruff check coaching/ shared/ --fix
python -m ruff format coaching/ shared/
python -m mypy coaching/src shared/ --explicit-package-bases
cd coaching && uv run pytest --cov=src
```

## Contract Impact

- `GET /api/v1/admin/models`: changed model catalog contents (legacy Haiku 3/3.5 no longer active; Haiku 4.5 active).
- Conversation extraction behavior: default/fallback extraction model is now Haiku 4.5.
- No endpoint path or payload shape changes were introduced by this migration.
