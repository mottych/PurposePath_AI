"""Base analysis service using Template Method pattern.

This module provides the abstract base for all analysis services,
implementing common workflow steps while allowing customization.
"""

from abc import ABC, abstractmethod
from typing import Any

import structlog

from src.application.llm.llm_service import LLMApplicationService
from src.core.constants import AnalysisType

logger = structlog.get_logger()


class BaseAnalysisService(ABC):
    """
    Abstract base class for analysis services.

    This class implements the Template Method pattern, defining the
    common workflow for all analysis types while allowing subclasses
    to customize specific steps.

    Design Pattern: Template Method
    - analyze() is the template method (final workflow)
    - build_prompt(), parse_response() are abstract (customized per type)
    - prepare_context() can be overridden if needed

    Design Principles:
        - DRY: Common workflow in one place
        - Open/Closed: Open for extension (new analysis types), closed for modification
        - Single Responsibility: Each analysis type handles its specific logic
        - Dependency Injection: Depends on LLMApplicationService
    """

    def __init__(self, llm_service: LLMApplicationService):
        """
        Initialize base analysis service.

        Args:
            llm_service: LLM application service for generation
        """
        self.llm_service = llm_service
        logger.info(
            f"{self.__class__.__name__} initialized",
            analysis_type=self.get_analysis_type().value,
        )

    @abstractmethod
    def get_analysis_type(self) -> AnalysisType:
        """
        Get the analysis type for this service.

        Returns:
            AnalysisType enum value

        Implemented by subclasses to identify analysis type.
        """
        pass

    @abstractmethod
    def build_prompt(self, context: dict[str, Any]) -> str:
        """
        Build analysis-specific prompt.

        Args:
            context: Analysis context with required data

        Returns:
            Formatted prompt string

        Implemented by subclasses to build type-specific prompts.
        Must include all necessary context and instructions.
        """
        pass

    @abstractmethod
    def parse_response(self, llm_response: str) -> dict[str, Any]:
        """
        Parse LLM response into structured result.

        Args:
            llm_response: Raw LLM response text

        Returns:
            Structured analysis result

        Implemented by subclasses to parse type-specific responses.
        Should handle parsing errors gracefully.
        """
        pass

    def prepare_context(self, raw_context: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare and validate analysis context.

        Args:
            raw_context: Raw context from caller

        Returns:
            Prepared context ready for prompt building

        Can be overridden by subclasses for custom preparation.
        Default implementation validates required fields.
        """
        # Default: pass through with basic validation
        if not raw_context:
            raise ValueError("Analysis context cannot be empty")

        return raw_context

    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute complete analysis workflow (Template Method).

        This is the main entry point for all analysis types.
        It orchestrates the workflow using abstract methods.

        Workflow:
        1. Prepare context (validate, enrich)
        2. Build prompt (type-specific)
        3. Generate LLM response
        4. Parse response (type-specific)
        5. Return structured result

        Args:
            context: Analysis context with required data

        Returns:
            Structured analysis result

        Raises:
            ValueError: If context is invalid
            Exception: If LLM generation or parsing fails
        """
        analysis_type = self.get_analysis_type()

        try:
            logger.info(
                "Analysis started",
                analysis_type=analysis_type.value,
            )

            # Step 1: Prepare context
            prepared_context = self.prepare_context(context)

            # Step 2: Build prompt
            prompt = self.build_prompt(prepared_context)

            logger.debug(
                "Prompt built",
                analysis_type=analysis_type.value,
                prompt_length=len(prompt),
            )

            # Step 3: Generate LLM response
            llm_response = await self.llm_service.generate_analysis(
                analysis_prompt=prompt,
                context=prepared_context,
                temperature=0.3,  # Lower temperature for deterministic analysis
            )

            logger.debug(
                "LLM response received",
                analysis_type=analysis_type.value,
                tokens=llm_response.usage.get("total_tokens", 0),
            )

            # Step 4: Parse response
            result = self.parse_response(llm_response.content)

            # Step 5: Add metadata
            result["_metadata"] = {
                "analysis_type": analysis_type.value,
                "model": llm_response.model,
                "tokens_used": llm_response.usage,
                "provider": llm_response.provider,
            }

            logger.info(
                "Analysis completed",
                analysis_type=analysis_type.value,
                tokens=llm_response.usage.get("total_tokens", 0),
            )

            return result

        except Exception as e:
            logger.error(
                "Analysis failed",
                analysis_type=analysis_type.value,
                error=str(e),
            )
            raise


__all__ = ["BaseAnalysisService"]
