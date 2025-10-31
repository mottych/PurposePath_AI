I """LLM Configuration seeding and management scripts.

This package contains scripts for managing LLM configurations, templates,
and migrations for the PurposePath AI Coaching Service.

Scripts:
    - seed_templates.py: Upload templates to S3 and create metadata
    - seed_configurations.py: Create configuration records (upcoming)
    - migrate_existing_configs.py: Migrate hardcoded configs (upcoming)
    - validate_configuration.py: Validate system integrity (upcoming)
    - rollback_configuration.py: Configuration rollback (upcoming)
"""

__all__ = [
    "seed_templates",
]
