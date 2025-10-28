"""Prompt template models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class QuestionBank(BaseModel):
    """Bank of questions for a specific category."""

    category: str
    questions: list[str]
    follow_ups: list[str] | None = None


class EvaluationCriteria(BaseModel):
    """Criteria for evaluating conversation progress."""

    min_responses_per_category: int = 2
    value_identification_threshold: float = 0.7
    required_value_count_min: int = 5
    required_value_count_max: int = 7


class CompletionCriteria(BaseModel):
    """Criteria for completing a conversation."""

    user_confirmation: bool = True
    min_values_identified: int = 5
    max_values_identified: int = 7


class PromptTemplateYamlData(BaseModel):
    """YAML data structure for prompt template loading."""

    topic: str = Field(description="Template topic")
    version: str = Field(description="Template version")
    system_prompt: str = Field(description="System prompt")
    initial_message: str = Field(description="Initial message")
    question_bank: list[dict[str, Any]] | None = Field(
        default=None, description="Question bank data"
    )
    evaluation_criteria: dict[str, Any] | None = Field(
        default=None, description="Evaluation criteria"
    )
    completion_criteria: dict[str, Any] | None = Field(
        default=None, description="Completion criteria"
    )
    llm_config: dict[str, Any] | None = Field(default=None, description="LLM configuration")
    value_indicators: dict[str, Any] | None = Field(default=None, description="Value indicators")
    phase_prompts: dict[str, Any] | None = Field(default=None, description="Phase prompts")
    min_conversation_time_minutes: int = 15


class LLMConfig(BaseModel):
    """LLM configuration for a prompt template."""

    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.9


class PromptTemplate(BaseModel):
    """Complete prompt template for a coaching topic."""

    topic: str
    version: str
    system_prompt: str
    initial_message: str
    question_bank: list[QuestionBank]
    evaluation_criteria: EvaluationCriteria
    completion_criteria: CompletionCriteria
    llm_config: LLMConfig
    value_indicators: dict[str, list[str]] | None = None
    phase_prompts: dict[str, str] | None = None

    def to_yaml_dict(self) -> dict[str, Any]:
        """Convert PromptTemplate to YAML-serializable dict."""
        return {
            "topic": self.topic,
            "version": self.version,
            "system_prompt": self.system_prompt,
            "initial_message": self.initial_message,
            "question_bank": [
                {"category": q.category, "questions": q.questions, "follow_ups": q.follow_ups}
                for q in self.question_bank
            ],
            "evaluation_criteria": self.evaluation_criteria.model_dump(),
            "completion_criteria": self.completion_criteria.model_dump(),
            "llm_config": self.llm_config.model_dump(),
            "value_indicators": self.value_indicators,
            "phase_prompts": self.phase_prompts,
        }

    @classmethod
    def from_yaml(cls, yaml_data: PromptTemplateYamlData) -> "PromptTemplate":
        """Create PromptTemplate from YAML data."""
        return cls(
            topic=yaml_data.topic,
            version=yaml_data.version,
            system_prompt=yaml_data.system_prompt,
            initial_message=yaml_data.initial_message,
            question_bank=[QuestionBank(**q) for q in yaml_data.question_bank or []],
            evaluation_criteria=EvaluationCriteria(**yaml_data.evaluation_criteria or {}),
            completion_criteria=CompletionCriteria(**yaml_data.completion_criteria or {}),
            llm_config=LLMConfig(**yaml_data.llm_config or {}),
            value_indicators=yaml_data.value_indicators,
            phase_prompts=yaml_data.phase_prompts,
        )


class PromptTemplateMetadata(BaseModel):
    """Metadata for a prompt template file."""

    topic: str = Field(..., description="Template topic")
    version: str = Field(..., description="Template version")
    key: str = Field(..., description="S3 key")
    last_modified: datetime = Field(..., description="Last modification timestamp")
    size: int = Field(..., description="File size in bytes")
