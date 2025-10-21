"""AWS Bedrock LLM provider implementation with LangChain integration."""

import json
from typing import Any, Dict, List

import boto3
import structlog
from langchain_aws import ChatBedrock
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage

try:
    import tiktoken
except ImportError:  # pragma: no cover - fallback for local testing

    class _FallbackEncoding:
        def encode(self, text: str) -> list[int]:
            return list(text.encode("utf-8"))

    class _TiktokenFallback:
        @staticmethod
        def get_encoding(_: str) -> _FallbackEncoding:
            return _FallbackEncoding()

    tiktoken = _TiktokenFallback()  # type: ignore[assignment]

from botocore.exceptions import ClientError

from .base import BaseProvider, LLMProvider, ProviderType

logger = structlog.get_logger()


# Simple exception class for compatibility
class LLMProviderCompatError(Exception):
    """Exception for LLM provider compatibility issues."""

    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"Provider {provider}: {message}")


class BedrockProvider(BaseProvider):
    """AWS Bedrock provider using LangChain integration."""

    # Supported Bedrock models
    SUPPORTED_MODELS = [
        "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "anthropic.claude-3-5-haiku-20241022-v1:0",
        "anthropic.claude-3-opus-20240229-v1:0",
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-haiku-20240307-v1:0",
        "amazon.titan-text-premier-v1:0",
        "amazon.titan-text-express-v1",
        "cohere.command-r-plus-v1:0",
        "cohere.command-r-v1:0",
        "meta.llama3-1-405b-instruct-v1:0",
        "meta.llama3-1-70b-instruct-v1:0",
        "meta.llama3-1-8b-instruct-v1:0",
    ]

    def __init__(self, config: Any) -> None:
        """Initialize Bedrock provider."""
        super().__init__(config)

        # Legacy direct client support
        self._legacy_client = None

        # Initialize tokenizer for token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            logger.debug("Falling back to gpt2 tokenizer for Bedrock provider")
            self.tokenizer = tiktoken.get_encoding("gpt2")

    @property
    def provider_type(self) -> ProviderType:
        """Get the provider type."""
        return ProviderType.BEDROCK

    @property
    def supported_models(self) -> List[str]:
        """Get list of supported model names."""
        return self.SUPPORTED_MODELS.copy()

    async def initialize(self) -> None:
        """Initialize the Bedrock client."""
        try:
            logger.info("Initializing Bedrock provider", model=self.config.model_name)

            # Create LangChain Bedrock client
            # Note: LangChain's ChatBedrock signature may vary by version
            self._client = ChatBedrock(  # type: ignore[call-arg]
                model_id=self.config.model_name,
                region_name=self.config.region_name or "us-east-1",
                model_kwargs={
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens or 4096,
                    "top_p": self.config.top_p or 0.9,
                },
                streaming=self.config.streaming,
            )

            logger.info("Bedrock provider initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize Bedrock provider", error=str(e))
            raise

    async def get_client(self) -> BaseChatModel:
        """Get the LangChain chat model client."""
        if self._client is None:
            await self.initialize()
        if self._client is None:
            raise RuntimeError("Failed to initialize Bedrock client")
        return self._client

    async def invoke(self, messages: List[BaseMessage]) -> str:
        """Invoke the model with messages and return response."""
        try:
            client = await self.get_client()
            response = await client.ainvoke(messages)
            # Handle different response content types
            if isinstance(response.content, str):
                return response.content
            elif isinstance(response.content, list):
                # If content is a list, join string elements
                content_parts = []
                for part in response.content:
                    if isinstance(part, str):
                        content_parts.append(part)
                    elif isinstance(part, dict) and "text" in part:
                        content_parts.append(str(part["text"]))
                return "".join(content_parts)
            else:
                return str(response.content)

        except Exception as e:
            logger.error("Error invoking Bedrock model", error=str(e), model=self.config.model_name)
            raise

    async def stream(self, messages: List[BaseMessage]) -> Any:
        """Stream model responses."""
        try:
            client = await self.get_client()
            async for chunk in client.astream(messages):
                yield chunk.content

        except Exception as e:
            logger.error(
                "Error streaming from Bedrock model", error=str(e), model=self.config.model_name
            )
            raise

    async def validate_model(self, model_name: str) -> bool:
        """Validate if model is supported and accessible."""
        if model_name not in self.SUPPORTED_MODELS:
            return False

        try:
            # Try to list available models via Bedrock
            session = boto3.Session(region_name=self.config.region_name or "us-east-1")
            bedrock = session.client("bedrock")

            # List foundation models to verify access
            response = bedrock.list_foundation_models()
            available_models = [model["modelId"] for model in response.get("modelSummaries", [])]

            return model_name in available_models

        except Exception as e:
            logger.warning("Unable to validate Bedrock model", model=model_name, error=str(e))
            return False

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        try:
            session = boto3.Session(region_name=self.config.region_name or "us-east-1")
            bedrock = session.client("bedrock")

            # Get model details
            response = bedrock.get_foundation_model(modelIdentifier=self.config.model_name)
            model_details = response.get("modelDetails", {})

            return {
                "model_id": self.config.model_name,
                "provider": "bedrock",
                "region": self.config.region_name or "us-east-1",
                "model_name": model_details.get("modelName", "Unknown"),
                "provider_name": model_details.get("providerName", "Unknown"),
                "input_modalities": model_details.get("inputModalities", []),
                "output_modalities": model_details.get("outputModalities", []),
                "supported_customizations": model_details.get("customizationsSupported", []),
                "inference_types": model_details.get("inferenceTypesSupported", []),
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "streaming": self.config.streaming,
            }

        except Exception as e:
            logger.warning("Unable to get Bedrock model info", error=str(e))
            return {
                "model_id": self.config.model_name,
                "provider": "bedrock",
                "region": self.config.region_name or "us-east-1",
                "error": str(e),
            }

    async def cleanup(self) -> None:
        """Clean up Bedrock resources."""
        logger.info("Cleaning up Bedrock provider")
        self._client = None
        self._legacy_client = None

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))

    # Legacy compatibility methods
    def _get_provider_from_model_id(self, model_id: str) -> str:
        """Extract provider from model ID."""
        if "anthropic" in model_id:
            return "anthropic"
        if "meta" in model_id:
            return "meta"
        if "amazon" in model_id:
            return "amazon"
        if "cohere" in model_id:
            return "cohere"
        return "unknown"


# Legacy compatibility class
class BedrockProviderLegacy(LLMProvider):
    """Legacy AWS Bedrock LLM provider for backward compatibility."""

    def __init__(
        self,
        client: Any,  # boto3.client('bedrock-runtime')  # type: ignore[misc]
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
    ) -> None:
        """Initialize Bedrock provider.

        Args:
            client: Boto3 Bedrock Runtime client
            model_id: Model identifier
        """
        # Create modern config from legacy parameters
        from .base import ProviderConfig, ProviderType

        config = ProviderConfig(
            provider_type=ProviderType.BEDROCK,
            model_name=model_id,
            temperature=0.7,
            max_tokens=2000,
        )

        super().__init__(config)

        self.client = client
        self.model_id = model_id
        self.provider = self._get_provider_from_model_id(model_id)

        # Initialize tokenizer (using tiktoken as approximation)
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:  # Fall back when the preferred encoding is unavailable
            logger.debug("Falling back to gpt2 tokenizer for Bedrock provider")
            self.tokenizer = tiktoken.get_encoding("gpt2")

    def _get_provider_from_model_id(self, model_id: str) -> str:
        """Extract provider from model ID."""
        if "anthropic" in model_id:
            return "anthropic"
        if "meta" in model_id:
            return "meta"
        if "amazon" in model_id:
            return "amazon"
        if "cohere" in model_id:
            return "cohere"
        return "unknown"

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs: Any,
    ) -> str:
        """Generate response using Bedrock."""
        try:
            # Format messages for the provider
            formatted_messages = self.format_messages(messages, system_prompt)
            top_p = float(kwargs.get("top_p", 0.9))

            # Prepare request based on provider
            if self.provider == "anthropic":
                request_body = self._prepare_anthropic_request(
                    formatted_messages,
                    temperature,
                    max_tokens,
                    top_p,
                )
            elif self.provider == "meta":
                request_body = self._prepare_meta_request(
                    formatted_messages,
                    temperature,
                    max_tokens,
                    top_p,
                )
            else:
                raise LLMProviderCompatError(
                    self.provider,
                    f"Unsupported provider: {self.provider}",
                )

            # Make request to Bedrock
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body),
            )

            # Parse response
            response_body = json.loads(response["body"].read())

            # Extract text based on provider
            if self.provider == "anthropic":
                return str(response_body["content"][0]["text"])
            if self.provider == "meta":
                return str(response_body["generation"])
            return str(response_body)

        except ClientError as error:
            logger.error(
                "Bedrock API error",
                error=str(error),
                model_id=self.model_id,
            )
            raise LLMProviderCompatError(
                self.provider,
                f"Bedrock API error: {error}",
            ) from error
        except Exception as error:  # pragma: no cover - defensive logging
            logger.error(
                "Unexpected error in Bedrock provider",
                error=str(error),
                model_id=self.model_id,
            )
            raise LLMProviderCompatError(
                self.provider,
                f"Unexpected error: {error}",
            ) from error

    async def analyze_text(
        self,
        text: str,
        analysis_prompt: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Analyze text using Bedrock."""
        # Construct analysis message
        messages = [{"role": "user", "content": f"{analysis_prompt}\n\nText to analyze:\n{text}"}]

        # Get response
        response = await self.generate_response(
            messages=messages,
            system_prompt="You are an expert analyst. Provide structured analysis in JSON format.",
            temperature=0.3,  # Lower temperature for analysis
            max_tokens=1500,
        )

        # Try to parse as JSON
        try:
            # Extract JSON from response if wrapped in markdown
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()

            result: Any = json.loads(response)
            return result if isinstance(result, dict) else {"analysis": str(result)}
        except json.JSONDecodeError:
            # If not valid JSON, return as text analysis
            return {"analysis": response}

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))

    def _prepare_anthropic_request(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float,
    ) -> Dict[str, Any]:
        """Prepare request body for Anthropic models."""
        # Extract system message if present
        system_message = ""
        conversation_messages: List[Dict[str, str]] = []

        for message in messages:
            if message["role"] == "system":
                system_message = message["content"]
            else:
                # Convert role names for Anthropic
                role = "user" if message["role"] == "user" else "assistant"
                conversation_messages.append(
                    {
                        "role": role,
                        "content": message["content"],
                    }
                )

        return {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": conversation_messages,
            "system": system_message,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }

    def _prepare_meta_request(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float,
    ) -> Dict[str, Any]:
        """Prepare request body for Meta Llama models."""
        # Combine messages into a single prompt
        prompt = ""
        for message in messages:
            if message["role"] == "system":
                prompt += f"System: {message['content']}\n\n"
            elif message["role"] == "user":
                prompt += f"User: {message['content']}\n\n"
            else:
                prompt += f"Assistant: {message['content']}\n\n"

        prompt += "Assistant: "

        return {
            "prompt": prompt,
            "max_gen_len": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }
