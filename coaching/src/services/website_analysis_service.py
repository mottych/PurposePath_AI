"""Website analysis service for extracting business information from websites."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

import html2text
import requests
import structlog
from bs4 import BeautifulSoup
from coaching.src.services.llm_service import LLMService

logger = structlog.get_logger()

# Timeout for HTTP requests (seconds)
REQUEST_TIMEOUT = 15

# Maximum content length to analyze (characters)
MAX_CONTENT_LENGTH = 50000

# User agent to identify ourselves
USER_AGENT = "PurposePathBot/1.0 (Business Analysis; +https://purposepath.app)"


class WebsiteAnalysisService:
    """Service for analyzing websites and extracting business information using AI.

    This service:
    1. Fetches and parses website content
    2. Extracts relevant text from HTML
    3. Uses LLM to analyze and structure business information
    """

    def __init__(self, llm_service: LLMService):
        """Initialize website analysis service.

        Args:
            llm_service: LLM service for AI analysis
        """
        self.llm_service = llm_service
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.ignore_emphasis = False
        logger.info("Website analysis service initialized")

    async def analyze_website(self, url: str) -> dict[str, Any]:
        """Analyze website to extract business information.

        Args:
            url: Website URL to analyze

        Returns:
            Dictionary with extracted business information:
            - products: List of products/services
            - niche: Target market/niche description
            - ica: Ideal customer avatar description
            - value_proposition: Value proposition statement

        Raises:
            ValueError: If URL is invalid or unreachable
            RuntimeError: If analysis fails
        """
        logger.info("Starting website analysis", url=url)

        # Validate URL
        self._validate_url(url)

        # Fetch website content
        try:
            html_content, page_title, meta_description = await self._fetch_website_content(url)
        except Exception as e:
            logger.error("Failed to fetch website content", url=url, error=str(e))
            raise ValueError(f"Could not fetch website content: {e!s}") from e

        # Extract and clean text content
        text_content = self._extract_text_content(html_content)

        if not text_content or len(text_content.strip()) < 100:
            raise ValueError(
                "Could not extract meaningful content from website. "
                "The website might be blocking automated access or have minimal content."
            )

        logger.info(
            "Website content extracted",
            url=url,
            title=page_title,
            content_length=len(text_content),
        )

        # Analyze content with LLM
        try:
            analysis_result = await self._analyze_with_llm(
                url=url,
                title=page_title,
                description=meta_description,
                content=text_content,
            )
        except Exception as e:
            logger.error("LLM analysis failed", url=url, error=str(e))
            raise RuntimeError(f"AI analysis failed: {e!s}") from e

        logger.info("Website analysis completed", url=url)
        return analysis_result

    def _validate_url(self, url: str) -> None:
        """Validate URL format and scheme.

        Args:
            url: URL to validate

        Raises:
            ValueError: If URL is invalid
        """
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                raise ValueError("URL must use http or https scheme")
            if not parsed.netloc:
                raise ValueError("URL must include a domain name")

            # Security: Block localhost and internal IPs
            if any(
                host in parsed.netloc.lower()
                for host in ["localhost", "127.0.0.1", "0.0.0.0", "[::]", "169.254"]
            ):
                raise ValueError("Cannot analyze local or internal URLs")

        except Exception as e:
            raise ValueError(f"Invalid URL: {e!s}") from e

    async def _fetch_website_content(self, url: str) -> tuple[str, str, str]:
        """Fetch HTML content from URL.

        Args:
            url: Website URL

        Returns:
            Tuple of (html_content, page_title, meta_description)

        Raises:
            requests.RequestException: If request fails
        """
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "close",
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                verify=True,
            )
            response.raise_for_status()

            # Parse HTML to extract metadata
            soup = BeautifulSoup(response.text, "lxml")

            # Get page title
            title_tag = soup.find("title")
            page_title = title_tag.get_text().strip() if title_tag else ""

            # Get meta description
            meta_desc = soup.find("meta", {"name": "description"})
            if not meta_desc:
                meta_desc = soup.find("meta", {"property": "og:description"})
            meta_description = meta_desc.get("content", "").strip() if meta_desc else ""

            return response.text, page_title, meta_description

        except requests.Timeout as e:
            raise RuntimeError(f"Request timed out after {REQUEST_TIMEOUT}s") from e
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch website: {e!s}") from e

    def _extract_text_content(self, html: str) -> str:
        """Extract meaningful text content from HTML.

        Args:
            html: Raw HTML content

        Returns:
            Cleaned text content
        """
        soup = BeautifulSoup(html, "lxml")

        # Remove script, style, and other non-content elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        # Convert to markdown-like text
        text = self.html_converter.handle(str(soup))

        # Clean up whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)  # Max 2 consecutive newlines
        text = re.sub(r" +", " ", text)  # Collapse multiple spaces
        text = text.strip()

        # Truncate if too long
        if len(text) > MAX_CONTENT_LENGTH:
            text = text[:MAX_CONTENT_LENGTH] + "\n\n[Content truncated...]"

        return text

    async def _analyze_with_llm(
        self,
        url: str,
        title: str,
        description: str,
        content: str,
    ) -> dict[str, Any]:
        """Analyze website content using LLM.

        Args:
            url: Website URL
            title: Page title
            description: Meta description
            content: Extracted text content

        Returns:
            Structured analysis results
        """
        prompt = f"""Analyze this website and extract business information in JSON format.

Website URL: {url}
Page Title: {title}
Meta Description: {description}

Website Content:
{content}

Extract and structure the following information:

1. **products**: List of products/services offered. For each product, provide:
   - id: Generate a unique identifier (lowercase, hyphenated)
   - name: Product/service name
   - problem: What problem it solves

2. **niche**: Describe the target market and business niche (2-3 sentences)

3. **ica**: Describe the Ideal Customer Avatar - who is this business serving? Include:
   - Demographics (company size, industry, role)
   - Pain points and challenges
   - Goals and aspirations

4. **value_proposition**: The main value proposition - what makes this business unique? (1-2 sentences)

Return ONLY valid JSON with this exact structure:
{{
    "products": [
        {{"id": "product-1", "name": "Product Name", "problem": "Problem it solves"}}
    ],
    "niche": "Target market description",
    "ica": "Ideal customer avatar description",
    "value_proposition": "Unique value proposition"
}}

Important:
- Be specific and based only on content found on the website
- If information is unclear, make reasonable inferences
- Keep descriptions concise but informative
- Ensure valid JSON output"""

        # Generate analysis using LLM
        response_data = await self.llm_service.generate_single_shot_analysis(
            topic="website_analysis",
            user_input=prompt,
            analysis_type="business_extraction",
        )

        response_text = response_data.get("response", "")

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    raise ValueError("No JSON found in LLM response")

            analysis = json.loads(json_text)

            # Validate required fields
            required_fields = ["products", "niche", "ica", "value_proposition"]
            for field in required_fields:
                if field not in analysis:
                    logger.warning(f"Missing field in analysis: {field}")
                    analysis[field] = [] if field == "products" else "Not determined"

            return analysis

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(
                "Failed to parse LLM response as JSON", error=str(e), response=response_text[:500]
            )
            # Return fallback structure
            return {
                "products": [
                    {
                        "id": "product-placeholder",
                        "name": "Primary Service/Product",
                        "problem": "Business challenge (details in website content)",
                    }
                ],
                "niche": f"Business serving customers in the {title} space",
                "ica": "Professional organizations seeking business solutions",
                "value_proposition": description or "Unique business value proposition",
            }


__all__ = ["WebsiteAnalysisService"]
