"""Onboarding service for AI-powered onboarding assistance."""

import structlog
from coaching.src.services.llm_service import LLMService
from coaching.src.services.website_analysis_service import WebsiteAnalysisService

logger = structlog.get_logger()


class OnboardingService:
    """Service for AI-powered onboarding assistance.

    Provides intelligent suggestions and coaching during the onboarding process.
    """

    def __init__(
        self,
        llm_service: LLMService,
        website_analysis_service: WebsiteAnalysisService | None = None,
    ):
        """Initialize onboarding service.

        Args:
            llm_service: LLM service for AI generation
            website_analysis_service: Optional service for website analysis
        """
        self.llm_service = llm_service
        self.website_analysis_service = website_analysis_service or WebsiteAnalysisService(
            llm_service=llm_service
        )
        logger.info("Onboarding service initialized")

    async def get_suggestions(
        self,
        kind: str,
        current: str | None = None,
        context: dict[str, str | list[str]] | None = None,
    ) -> dict[str, list[str] | str]:
        """Get AI suggestions for onboarding fields.

        Args:
            kind: Type of suggestion (niche, ica, valueProposition)
            current: Current draft text (optional)
            context: Business context

        Returns:
            Dictionary with suggestions and reasoning
        """
        logger.info("Generating onboarding suggestions", kind=kind)

        context = context or {}
        business_name = context.get("businessName", "")
        industry = context.get("industry", "")
        products = context.get("products", [])

        # Build prompt based on kind
        prompts = {
            "niche": f"""Generate 3-5 professional niche descriptions for a business.

Business Name: {business_name or "Not provided"}
Industry: {industry or "Not provided"}
Products/Services: {", ".join(products) if products else "Not provided"}
Current Draft: {current or "None"}

Provide clear, specific niche descriptions that define the target market and unique positioning.
Each should be 1-2 sentences.""",
            "ica": f"""Generate 3-5 Ideal Customer Avatar (ICA) descriptions for a business.

Business Name: {business_name or "Not provided"}
Industry: {industry or "Not provided"}
Products/Services: {", ".join(products) if products else "Not provided"}
Current Draft: {current or "None"}

Describe the perfect customer in detail: demographics, psychographics, pain points, goals.
Each should be specific and actionable.""",
            "valueProposition": f"""Generate 3-5 value proposition statements for a business.

Business Name: {business_name or "Not provided"}
Industry: {industry or "Not provided"}
Products/Services: {", ".join(products) if products else "Not provided"}
Current Draft: {current or "None"}

Create compelling value propositions that clearly state what makes this business unique.
Each should be concise and customer-focused.""",
        }

        prompt = prompts.get(kind, prompts["niche"])

        # Generate suggestions using LLM
        response_data = await self.llm_service.generate_single_shot_analysis(
            topic="onboarding",
            user_input=prompt,
            analysis_type="suggestion",
        )
        response = response_data.get("response", "")

        # Parse response into list of suggestions
        suggestions = self._parse_suggestions(response)

        reasoning = (
            f"Based on your {industry or 'business'} "
            + f"{'and products (' + ', '.join(products[:2]) + ')' if products else 'information'}, "
            + "these suggestions align with market positioning best practices."
        )

        return {
            "suggestions": suggestions,
            "reasoning": reasoning,
        }

    async def scan_website(self, url: str) -> dict[str, str | list[str]]:
        """Scan website to extract business information using AI analysis.

        Args:
            url: Website URL to scan

        Returns:
            Dictionary with extracted business information:
            - businessName: Extracted business name
            - industry: Identified industry
            - description: Business description
            - products: List of product/service names
            - targetMarket: Target market description
            - suggestedNiche: Suggested niche positioning

        Raises:
            ValueError: If URL is invalid or website cannot be accessed
            RuntimeError: If analysis fails
        """
        logger.info("Scanning website", url=url)

        try:
            # Use website analysis service to extract information
            analysis = await self.website_analysis_service.analyze_website(url)

            # Map analysis results to onboarding format
            products_list = [
                product.get("name", "Product/Service") for product in analysis.get("products", [])
            ]

            # Extract business name from URL or products
            from urllib.parse import urlparse

            parsed_url = urlparse(url)
            business_name = parsed_url.netloc.replace("www.", "").split(".")[0].title()

            result = {
                "businessName": business_name,
                "industry": "Professional Services",  # Could be enhanced with industry detection
                "description": analysis.get("value_proposition", ""),
                "products": products_list,
                "targetMarket": analysis.get("ica", ""),
                "suggestedNiche": analysis.get("niche", ""),
            }

            logger.info("Website scanned successfully", url=url, products_count=len(products_list))
            return result

        except (ValueError, RuntimeError) as e:
            logger.error("Website scan failed", url=url, error=str(e))
            raise

    async def get_coaching(
        self,
        topic: str,
        message: str,
        context: dict[str, str] | None = None,
    ) -> dict[str, str | list[str]]:
        """Get coaching assistance for onboarding topic.

        Args:
            topic: Onboarding topic (coreValues, purpose, vision)
            message: User's question
            context: Business context

        Returns:
            Dictionary with coach response and suggestions
        """
        logger.info("Providing onboarding coaching", topic=topic)

        context = context or {}
        business_name = context.get("businessName", "your business")
        industry = context.get("industry", "your industry")
        current_draft = context.get("currentDraft", "")

        # Topic-specific prompts
        topic_prompts = {
            "coreValues": f"""You are a business coach helping define core values.

Business: {business_name}
Industry: {industry}
Current Draft: {current_draft or "None yet"}

User Question: {message}

Provide helpful, actionable guidance. Explain what core values are, give examples relevant to their industry,
and help them think through what principles should guide their business decisions.

Also suggest 4-6 potential core values they might consider.""",
            "purpose": f"""You are a business coach helping define company purpose.

Business: {business_name}
Industry: {industry}
Current Draft: {current_draft or "None yet"}

User Question: {message}

Provide helpful guidance on crafting a purpose statement. Explain the difference between purpose and goals,
give examples of strong purpose statements, and help them articulate why their business exists beyond profit.

Suggest 2-3 purpose statement examples they could refine.""",
            "vision": f"""You are a business coach helping create a vision statement.

Business: {business_name}
Industry: {industry}
Current Draft: {current_draft or "None yet"}

User Question: {message}

Provide guidance on creating an inspiring vision statement. Explain what makes a good vision,
give examples, and help them envision their ideal future state.

Suggest 2-3 vision statement examples they could adapt.""",
        }

        prompt = topic_prompts.get(topic, topic_prompts["coreValues"])

        # Generate coaching response
        response_data = await self.llm_service.generate_single_shot_analysis(
            topic=topic,
            user_input=prompt,
            analysis_type="coaching",
        )
        response_text = response_data.get("response", "")

        # Extract suggestions from response
        suggestions = self._extract_suggestions_from_coaching(response_text, topic)

        return {
            "response": response_text,
            "suggestions": suggestions,
        }

    def _parse_suggestions(self, response: str) -> list[str]:
        """Parse AI response into list of suggestions.

        Args:
            response: Raw AI response

        Returns:
            List of suggestions
        """
        # Split by newlines and filter out empty/short lines
        lines = [
            line.strip().lstrip("0123456789.-•* ")
            for line in response.split("\n")
            if line.strip() and len(line.strip()) > 20
        ]

        # Return up to 5 suggestions
        return (
            lines[:5]
            if lines
            else ["Unable to generate suggestions. Please try with more context."]
        )

    def _extract_suggestions_from_coaching(
        self,
        response: str,
        topic: str,
    ) -> list[str]:
        """Extract specific suggestions from coaching response.

        Args:
            response: Coaching response text
            topic: Topic being coached

        Returns:
            List of suggestions
        """
        # Simple extraction: look for quoted phrases or bullet points
        suggestions = []

        # Look for quoted text
        import re

        quoted = re.findall(r'"([^"]+)"', response)
        suggestions.extend(quoted[:6])

        # If we have suggestions, return them
        if suggestions:
            return suggestions[:6]

        # Default suggestions by topic
        defaults = {
            "coreValues": [
                "Integrity",
                "Innovation",
                "Customer Success",
                "Excellence",
            ],
            "purpose": [
                f"To help our customers achieve their goals through {topic}",
                "To make a positive impact in our industry",
            ],
            "vision": [
                "To be the leading provider in our market",
                "To transform how our industry approaches challenges",
            ],
        }

        return defaults.get(topic, [])


__all__ = ["OnboardingService"]
