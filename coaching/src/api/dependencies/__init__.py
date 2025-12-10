"""Dependency injection for API layer.

This package aggregates dependencies from legacy and new modules.
"""

from coaching.src.api.auth import get_current_context
from coaching.src.api.legacy_dependencies import (
    get_alignment_service,
    get_analysis_service_by_type,
    get_cache_service,
    get_conversation_repository,
    get_conversation_service,
    get_insights_service,
    get_kpi_service,
    get_llm_configuration_repository,
    get_llm_configuration_service,
    get_llm_service,
    get_llm_template_service,
    get_model_config_service,
    get_prompt_service,
    get_strategy_service,
    get_template_metadata_repository,
)

from .ai_engine import (
    get_generic_handler,
    get_llm_provider,
    get_provider_factory,
    get_response_serializer,
    get_s3_prompt_storage,
    get_topic_repository,
    get_unified_ai_engine,
    reset_singletons,
)

__all__ = [
    # From legacy_dependencies
    "get_alignment_service",
    "get_analysis_service_by_type",
    "get_cache_service",
    "get_conversation_repository",
    "get_conversation_service",
    # Auth
    "get_current_context",
    # From ai_engine (overrides legacy if duplicates exist)
    "get_generic_handler",
    "get_insights_service",
    "get_kpi_service",
    "get_llm_configuration_repository",
    "get_llm_configuration_service",
    "get_llm_provider",
    "get_llm_service",
    "get_llm_template_service",
    "get_model_config_service",
    "get_prompt_service",
    "get_provider_factory",
    "get_response_serializer",
    "get_s3_prompt_storage",
    "get_strategy_service",
    "get_template_metadata_repository",
    "get_topic_repository",
    "get_unified_ai_engine",
    "reset_singletons",
]
