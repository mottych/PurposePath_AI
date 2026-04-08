"""Map legacy multitenant coaching LLM responses into usage recording types."""

from coaching.src.application.llm_usage.token_usage import normalize_token_counts
from coaching.src.core.constants import TopicType
from coaching.src.core.topic_registry import get_topic_by_topic_id
from coaching.src.domain.entities.llm_topic import LLMTopic
from coaching.src.domain.ports.llm_provider_port import LLMResponse as DomainLLMResponse
from coaching.src.models.llm_models import LLMResponse as CoachingLLMResponse


def build_llm_topic_for_usage(*, topic_id: str, max_tokens_topic_config: int) -> LLMTopic:
    """Minimal LLMTopic for usage rows (registry + max_tokens from conversation template)."""
    td = get_topic_by_topic_id(topic_id)
    category = td.category.value if td else "conversation"
    topic_type = td.topic_type.value if td else TopicType.CONVERSATION_COACHING.value
    topic_name = (td.description[:200] if td and td.description else None) or topic_id
    return LLMTopic(
        topic_id=topic_id,
        topic_name=topic_name,
        topic_type=topic_type,
        category=category,
        is_active=True,
        max_tokens=max_tokens_topic_config,
    )


def coaching_llm_response_to_domain(resp: CoachingLLMResponse) -> DomainLLMResponse:
    """Convert multitenant `LLMResponse` to provider-shaped response for cost/token extraction."""
    tu = resp.token_usage
    if isinstance(tu, dict):
        inp, out, tot = normalize_token_counts(tu)
    else:
        tot = int(tu) if tu else 0
        inp = int(tot * 0.6)
        out = max(tot - inp, 0)
    meta = resp.metadata or {}
    finish = str(meta.get("finish_reason", "") or "")
    provider = str(meta.get("provider", "bedrock") or "bedrock")
    total = tot if tot else inp + out
    return DomainLLMResponse(
        content=resp.response or "",
        model=resp.model_id,
        usage={
            "prompt_tokens": inp,
            "completion_tokens": out,
            "total_tokens": total,
        },
        finish_reason=finish,
        provider=provider,
    )
