"""Unit tests for Google Vertex AI LLM provider.

Tests the GoogleVertexLLMProvider using the new google-genai SDK.
"""

import contextlib
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from coaching.src.domain.ports.llm_provider_port import LLMMessage
from coaching.src.infrastructure.llm.google_vertex_provider import GoogleVertexLLMProvider


class TestGoogleVertexProviderInitialization:
    """Tests for provider initialization."""

    def test_provider_name_is_google_vertex(self) -> None:
        """Test that provider_name property returns correct value."""
        provider = GoogleVertexLLMProvider(project_id="test-project")
        assert provider.provider_name == "google_vertex"

    def test_supported_models_returns_list(self) -> None:
        """Test that supported_models property returns expected models."""
        provider = GoogleVertexLLMProvider(project_id="test-project")
        models = provider.supported_models

        assert isinstance(models, list)
        assert "gemini-2.5-pro" in models
        assert "gemini-2.5-flash" in models
        assert "gemini-2.0-flash" in models

    def test_supported_models_is_copy(self) -> None:
        """Test that supported_models returns a copy, not the original list."""
        provider = GoogleVertexLLMProvider(project_id="test-project")
        models1 = provider.supported_models
        models2 = provider.supported_models

        assert models1 is not models2
        assert models1 == models2

    def test_initialization_with_all_params(self) -> None:
        """Test initialization with all parameters."""
        mock_creds = MagicMock()
        provider = GoogleVertexLLMProvider(
            project_id="test-project",
            location="europe-west1",
            credentials=mock_creds,
        )

        assert provider.project_id == "test-project"
        assert provider.location == "europe-west1"
        assert provider.credentials == mock_creds
        assert provider._client is None
        assert provider._initialized is False

    def test_default_location_is_global(self) -> None:
        """Test that default location is global (required for Gemini 3 models)."""
        provider = GoogleVertexLLMProvider(project_id="test-project")
        assert provider.location == "global"


class TestGoogleVertexProviderValidation:
    """Tests for input validation."""

    @pytest.fixture
    def provider(self) -> GoogleVertexLLMProvider:
        """Create a provider instance for testing."""
        return GoogleVertexLLMProvider(project_id="test-project")

    @pytest.mark.asyncio
    async def test_generate_rejects_temperature_below_zero(
        self, provider: GoogleVertexLLMProvider
    ) -> None:
        """Test that generate raises error for temperature < 0."""
        messages = [LLMMessage(role="user", content="Hello")]

        with pytest.raises(ValueError, match="Temperature must be between 0.0 and 2.0"):
            await provider.generate(
                messages=messages,
                model="gemini-2.5-flash",
                temperature=-0.1,
            )

    @pytest.mark.asyncio
    async def test_generate_rejects_temperature_above_two(
        self, provider: GoogleVertexLLMProvider
    ) -> None:
        """Test that generate raises error for temperature > 2.0."""
        messages = [LLMMessage(role="user", content="Hello")]

        with pytest.raises(ValueError, match="Temperature must be between 0.0 and 2.0"):
            await provider.generate(
                messages=messages,
                model="gemini-2.5-flash",
                temperature=2.1,
            )

    @pytest.mark.asyncio
    async def test_generate_accepts_valid_temperature_range(
        self, provider: GoogleVertexLLMProvider
    ) -> None:
        """Test temperature boundary values are accepted (0.0, 1.0, 2.0)."""
        messages = [LLMMessage(role="user", content="Hello")]

        # 0.0 should be valid
        with patch.object(provider, "_get_client") as mock_client:
            mock_response = MagicMock()
            mock_response.text = "Test response"
            mock_response.candidates = []
            mock_response.usage_metadata = None
            mock_client.return_value.aio.models.generate_content = AsyncMock(
                return_value=mock_response
            )

            # These should not raise temperature validation errors
            with contextlib.suppress(RuntimeError):
                await provider.generate(
                    messages=messages, model="gemini-2.5-flash", temperature=0.0
                )

            with contextlib.suppress(RuntimeError):
                await provider.generate(
                    messages=messages, model="gemini-2.5-flash", temperature=2.0
                )

    @pytest.mark.asyncio
    async def test_generate_rejects_unsupported_model(
        self, provider: GoogleVertexLLMProvider
    ) -> None:
        """Test that generate raises error for unsupported model."""
        messages = [LLMMessage(role="user", content="Hello")]

        with pytest.raises(ValueError, match="not supported"):
            await provider.generate(
                messages=messages,
                model="unsupported-model-xyz",
                temperature=0.7,
            )

    @pytest.mark.asyncio
    async def test_stream_rejects_temperature_out_of_range(
        self, provider: GoogleVertexLLMProvider
    ) -> None:
        """Test that generate_stream validates temperature range."""
        messages = [LLMMessage(role="user", content="Hello")]

        with pytest.raises(ValueError, match="Temperature must be between 0.0 and 2.0"):
            async for _ in provider.generate_stream(
                messages=messages,
                model="gemini-2.5-flash",
                temperature=3.0,
            ):
                pass

    @pytest.mark.asyncio
    async def test_stream_rejects_unsupported_model(
        self, provider: GoogleVertexLLMProvider
    ) -> None:
        """Test that generate_stream raises error for unsupported model."""
        messages = [LLMMessage(role="user", content="Hello")]

        with pytest.raises(ValueError, match="not supported"):
            async for _ in provider.generate_stream(
                messages=messages,
                model="invalid-model",
                temperature=0.7,
            ):
                pass


class TestGoogleVertexProviderGenerate:
    """Tests for generate method."""

    @pytest.fixture
    def provider(self) -> GoogleVertexLLMProvider:
        """Create a provider instance for testing."""
        return GoogleVertexLLMProvider(project_id="test-project")

    @pytest.fixture
    def mock_response(self) -> MagicMock:
        """Create a mock Vertex AI response."""
        response = MagicMock()
        response.text = "This is a test response from Gemini."
        response.candidates = [MagicMock(finish_reason="STOP")]
        response.usage_metadata = MagicMock(
            prompt_token_count=10,
            candidates_token_count=15,
            total_token_count=25,
        )
        return response

    @pytest.mark.asyncio
    async def test_generate_returns_llm_response(
        self,
        provider: GoogleVertexLLMProvider,
        mock_response: MagicMock,
    ) -> None:
        """Test that generate returns properly formatted LLMResponse."""
        with patch.object(provider, "_get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_client

            messages = [LLMMessage(role="user", content="Hello, how are you?")]

            response = await provider.generate(
                messages=messages,
                model="gemini-2.5-flash",
                temperature=0.7,
            )

            assert response.content == "This is a test response from Gemini."
            assert response.model == "gemini-2.5-flash"
            assert response.provider == "google_vertex"
            assert response.finish_reason == "stop"
            assert response.usage["prompt_tokens"] == 10
            assert response.usage["completion_tokens"] == 15
            assert response.usage["total_tokens"] == 25

    @pytest.mark.asyncio
    async def test_generate_maps_user_role_correctly(
        self,
        provider: GoogleVertexLLMProvider,
    ) -> None:
        """Test that user role is mapped to 'user' in Vertex AI format."""
        mock_response = MagicMock()
        mock_response.text = "Response"
        mock_response.candidates = []
        mock_response.usage_metadata = None

        with patch.object(provider, "_get_client") as mock_get:
            mock_client = MagicMock()
            mock_generate = AsyncMock(return_value=mock_response)
            mock_client.aio.models.generate_content = mock_generate
            mock_get.return_value = mock_client

            messages = [LLMMessage(role="user", content="Hello")]

            await provider.generate(messages=messages, model="gemini-2.5-flash")

            # Verify the call was made with correct content structure
            call_kwargs = mock_generate.call_args.kwargs
            contents = call_kwargs["contents"]
            assert contents[0].role == "user"

    @pytest.mark.asyncio
    async def test_generate_maps_assistant_role_to_model(
        self,
        provider: GoogleVertexLLMProvider,
    ) -> None:
        """Test that assistant role is mapped to 'model' in Vertex AI format."""
        mock_response = MagicMock()
        mock_response.text = "Response"
        mock_response.candidates = []
        mock_response.usage_metadata = None

        with patch.object(provider, "_get_client") as mock_get:
            mock_client = MagicMock()
            mock_generate = AsyncMock(return_value=mock_response)
            mock_client.aio.models.generate_content = mock_generate
            mock_get.return_value = mock_client

            messages = [
                LLMMessage(role="user", content="Hello"),
                LLMMessage(role="assistant", content="Hi there!"),
                LLMMessage(role="user", content="How are you?"),
            ]

            await provider.generate(messages=messages, model="gemini-2.5-flash")

            call_kwargs = mock_generate.call_args.kwargs
            contents = call_kwargs["contents"]
            assert contents[0].role == "user"
            assert contents[1].role == "model"
            assert contents[2].role == "user"


class TestGoogleVertexProviderStreaming:
    """Tests for streaming generation."""

    @pytest.fixture
    def provider(self) -> GoogleVertexLLMProvider:
        """Create a provider instance for testing."""
        return GoogleVertexLLMProvider(project_id="test-project")

    @pytest.mark.asyncio
    async def test_generate_stream_yields_tokens(
        self,
        provider: GoogleVertexLLMProvider,
    ) -> None:
        """Test that generate_stream yields token chunks."""
        # Create mock chunks
        mock_chunks = [
            MagicMock(text="Hello"),
            MagicMock(text=" "),
            MagicMock(text="world"),
            MagicMock(text="!"),
        ]

        # Create an async generator from chunks
        async def mock_stream() -> Any:
            for chunk in mock_chunks:
                yield chunk

        with patch.object(provider, "_get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content_stream = AsyncMock(return_value=mock_stream())
            mock_get.return_value = mock_client

            messages = [LLMMessage(role="user", content="Say hello")]

            collected_tokens: list[str] = []
            async for token in provider.generate_stream(
                messages=messages,
                model="gemini-2.5-flash",
            ):
                collected_tokens.append(token)

            assert collected_tokens == ["Hello", " ", "world", "!"]


class TestGoogleVertexProviderTokenCounting:
    """Tests for token counting."""

    @pytest.fixture
    def provider(self) -> GoogleVertexLLMProvider:
        """Create a provider instance for testing."""
        return GoogleVertexLLMProvider(project_id="test-project")

    @pytest.mark.asyncio
    async def test_count_tokens_returns_count(
        self,
        provider: GoogleVertexLLMProvider,
    ) -> None:
        """Test that count_tokens returns token count from API."""
        mock_response = MagicMock(total_tokens=42)

        with patch.object(provider, "_get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.aio.models.count_tokens = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_client

            count = await provider.count_tokens("Hello, world!", model="gemini-2.5-flash")

            assert count == 42

    @pytest.mark.asyncio
    async def test_count_tokens_fallback_on_error(
        self,
        provider: GoogleVertexLLMProvider,
    ) -> None:
        """Test that count_tokens falls back to approximation on error."""
        with patch.object(provider, "_get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.aio.models.count_tokens = AsyncMock(side_effect=Exception("API Error"))
            mock_get.return_value = mock_client

            text = "Hello, world!"
            count = await provider.count_tokens(text, model="gemini-2.5-flash")

            # Fallback approximation: ~4 chars per token
            expected_approx = len(text) // 4
            assert count == expected_approx


class TestGoogleVertexProviderModelValidation:
    """Tests for model validation."""

    @pytest.fixture
    def provider(self) -> GoogleVertexLLMProvider:
        """Create a provider instance for testing."""
        return GoogleVertexLLMProvider(project_id="test-project")

    @pytest.mark.asyncio
    async def test_validate_model_returns_true_for_supported(
        self,
        provider: GoogleVertexLLMProvider,
    ) -> None:
        """Test validate_model returns True for supported models."""
        assert await provider.validate_model("gemini-2.5-pro") is True
        assert await provider.validate_model("gemini-2.5-flash") is True
        assert await provider.validate_model("gemini-2.0-flash") is True

    @pytest.mark.asyncio
    async def test_validate_model_returns_false_for_unsupported(
        self,
        provider: GoogleVertexLLMProvider,
    ) -> None:
        """Test validate_model returns False for unsupported models."""
        assert await provider.validate_model("gpt-4") is False
        assert await provider.validate_model("claude-3") is False
        assert await provider.validate_model("invalid-model") is False


class TestGoogleVertexProviderClose:
    """Tests for provider cleanup."""

    @pytest.fixture
    def provider(self) -> GoogleVertexLLMProvider:
        """Create a provider instance for testing."""
        return GoogleVertexLLMProvider(project_id="test-project")

    @pytest.mark.asyncio
    async def test_close_clears_client(
        self,
        provider: GoogleVertexLLMProvider,
    ) -> None:
        """Test that close clears the client and resets state."""
        # Simulate an initialized client
        mock_client = MagicMock()
        mock_client.aio.close = AsyncMock()
        provider._client = mock_client
        provider._initialized = True

        await provider.close()

        assert provider._client is None
        assert provider._initialized is False
        mock_client.aio.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_handles_no_client(
        self,
        provider: GoogleVertexLLMProvider,
    ) -> None:
        """Test that close handles case when no client exists."""
        # Should not raise error
        await provider.close()

        assert provider._client is None
        assert provider._initialized is False
