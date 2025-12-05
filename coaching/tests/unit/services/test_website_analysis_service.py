from unittest.mock import AsyncMock, Mock, patch

import pytest
from coaching.src.llm.providers.manager import ProviderManager
from coaching.src.services.website_analysis_service import WebsiteAnalysisService


class TestWebsiteAnalysisService:
    @pytest.fixture
    def mock_provider_manager(self):
        manager = Mock(spec=ProviderManager)
        manager._providers = {"bedrock": AsyncMock()}
        return manager

    @pytest.fixture
    def mock_llm_service(self):
        service = AsyncMock()
        return service

    @pytest.fixture
    def service(self, mock_provider_manager, mock_llm_service):
        return WebsiteAnalysisService(
            provider_manager=mock_provider_manager, llm_service=mock_llm_service
        )

    @pytest.mark.asyncio
    async def test_analyze_website_success_with_llm_service(self, service, mock_llm_service):
        # Arrange
        url = "https://example.com"
        # Make content longer than 100 chars
        long_content = "Test content about products. " * 10
        html_content = f"<html><head><title>Test Page</title><meta name='description' content='Test Description'></head><body><p>{long_content}</p></body></html>"

        mock_llm_response = {
            "response": """
            ```json
            {
                "products": [{"id": "p1", "name": "Product 1", "problem": "Problem 1"}],
                "niche": "Test Niche",
                "ica": "Test ICA",
                "value_proposition": "Test Value Prop"
            }
            ```
            """
        }
        mock_llm_service.generate_single_shot_analysis.return_value = mock_llm_response

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.text = html_content
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            # Act
            result = await service.analyze_website(url)

            # Assert
            assert result["niche"] == "Test Niche"
            assert len(result["products"]) == 1
            assert result["products"][0]["name"] == "Product 1"

            mock_llm_service.generate_single_shot_analysis.assert_called_once()
            call_args = mock_llm_service.generate_single_shot_analysis.call_args
            assert call_args.kwargs["topic"] == "website_analysis"
            assert "Test Page" in call_args.kwargs["user_input"]

    @pytest.mark.asyncio
    async def test_analyze_website_success_with_provider_manager(self, mock_provider_manager):
        # Arrange
        service = WebsiteAnalysisService(provider_manager=mock_provider_manager)
        url = "https://example.com"
        # Make content longer than 100 chars
        long_content = "Content " * 20
        html_content = f"<html><body><p>{long_content}</p></body></html>"

        mock_provider = mock_provider_manager._providers["bedrock"]
        mock_provider.invoke.return_value = (
            '{"products": [], "niche": "N", "ica": "I", "value_proposition": "V"}'
        )

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.text = html_content
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            # Act
            result = await service.analyze_website(url)

            # Assert
            assert result["niche"] == "N"
            mock_provider.invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_website_invalid_url(self, service):
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid URL"):
            await service.analyze_website("invalid-url")

    @pytest.mark.asyncio
    async def test_analyze_website_fetch_failure(self, service):
        # Arrange
        with (
            patch("requests.get", side_effect=Exception("Connection error")),
            pytest.raises(ValueError, match="Could not fetch website content"),
        ):
            # Act & Assert
            await service.analyze_website("https://example.com")

    @pytest.mark.asyncio
    async def test_analyze_website_empty_content(self, service):
        # Arrange
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.text = "<html><body></body></html>"  # Empty body
            mock_get.return_value = mock_response

            # Act & Assert
            with pytest.raises(ValueError, match="Could not extract meaningful content"):
                await service.analyze_website("https://example.com")

    @pytest.mark.asyncio
    async def test_analyze_website_llm_failure(self, service, mock_llm_service):
        # Arrange
        mock_llm_service.generate_single_shot_analysis.side_effect = Exception("LLM Error")

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.text = "<html><body><p>" + "content " * 20 + "</p></body></html>"
            mock_get.return_value = mock_response

            # Act & Assert
            with pytest.raises(RuntimeError, match="AI analysis failed"):
                await service.analyze_website("https://example.com")

    def test_validate_url_security(self, service):
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot analyze local or internal URLs"):
            service._validate_url("http://localhost:8000")

        with pytest.raises(ValueError, match="Cannot analyze local or internal URLs"):
            service._validate_url("http://127.0.0.1")

    def test_extract_text_content_cleaning(self, service):
        # Arrange
        html = """
        <html>
            <script>var x=1;</script>
            <style>.css {}</style>
            <body>
                <h1>Title</h1>
                <p>  Multiple    spaces   </p>
                <nav>Menu</nav>
            </body>
        </html>
        """

        # Act
        text = service._extract_text_content(html)

        # Assert
        assert "var x=1" not in text
        assert ".css" not in text
        assert "Menu" not in text
        assert "Title" in text
        assert "Multiple spaces" in text

    @pytest.mark.asyncio
    async def test_analyze_with_llm_json_fallback(self, service, mock_llm_service):
        # Arrange
        mock_llm_service.generate_single_shot_analysis.return_value = {
            "response": "Invalid JSON response"
        }

        # Act
        result = await service._analyze_with_llm("http://url", "Title", "Desc", "Content")

        # Assert
        assert result["products"][0]["id"] == "product-placeholder"  # Check for fallback value
        assert "Title" in result["niche"]

    @pytest.mark.asyncio
    async def test_analyze_with_llm_missing_fields(self, service, mock_llm_service):
        # Arrange
        mock_llm_service.generate_single_shot_analysis.return_value = {
            "response": '{"products": []}'  # Missing other fields
        }

        # Act
        result = await service._analyze_with_llm("http://url", "Title", "Desc", "Content")

        # Assert
        assert result["niche"] == "Not determined"
        assert result["products"] == []
