"""AWS Systems Manager Parameter Store service for runtime configuration.

This service provides access to SSM Parameter Store for retrieving and updating
runtime configuration values like default model codes.
"""

from datetime import datetime, timedelta

import boto3
import structlog
from botocore.exceptions import ClientError

logger = structlog.get_logger(__name__)


class ParameterStoreService:
    """Service for interacting with AWS Systems Manager Parameter Store.

    Provides cached access to runtime configuration parameters with automatic
    fallback to hardcoded defaults if parameters are not found.
    """

    def __init__(self, region: str = "us-east-1", stage: str = "dev"):
        """Initialize Parameter Store service.

        Args:
            region: AWS region for SSM client
            stage: Environment stage (dev, staging, prod)
        """
        self.ssm_client = boto3.client("ssm", region_name=region)
        self.region = region
        self.stage = stage
        self.parameter_prefix = f"/purposepath/{stage}"
        self._cache: tuple[str, str] | None = None
        self._cache_time: datetime | None = None
        self._cache_ttl_seconds = 300  # 5 minute TTL
        logger.info("Parameter Store service initialized", stage=stage, region=region)

    def get_default_models(self) -> tuple[str, str]:
        """Get default model codes from Parameter Store.

        Returns cached values with 5-minute TTL. Falls back to hardcoded
        defaults if parameters don't exist or SSM is unavailable.

        Returns:
            Tuple of (basic_model_code, premium_model_code)
        """
        # Check cache
        if (
            self._cache is not None
            and self._cache_time is not None
            and datetime.utcnow() - self._cache_time < timedelta(seconds=self._cache_ttl_seconds)
        ):
            return self._cache

        # Cache miss or expired - fetch from Parameter Store
        result = self._fetch_default_models()
        self._cache = result
        self._cache_time = datetime.utcnow()
        return result

    def _fetch_default_models(self) -> tuple[str, str]:
        """Fetch default model codes from Parameter Store.

        Returns:
            Tuple of (basic_model_code, premium_model_code)
        """
        try:
            response = self.ssm_client.get_parameters(
                Names=[
                    f"{self.parameter_prefix}/models/default_basic",
                    f"{self.parameter_prefix}/models/default_premium",
                ],
                WithDecryption=False,  # Not using SecureString for model codes
            )

            if not response["Parameters"]:
                logger.warning(
                    "No default model parameters found, using hardcoded fallback",
                    prefix=self.parameter_prefix,
                )
                return self._get_fallback_models()

            # Build parameter map
            params: dict[str, str] = {}
            for param in response["Parameters"]:
                key = param["Name"].split("/")[
                    -1
                ]  # Extract last part (default_basic/default_premium)
                params[key] = param["Value"]

            basic = params.get("default_basic")
            premium = params.get("default_premium")

            if not basic or not premium:
                logger.warning(
                    "Incomplete default model parameters, using fallback",
                    found_basic=bool(basic),
                    found_premium=bool(premium),
                )
                return self._get_fallback_models()

            logger.debug(
                "Loaded default models from Parameter Store",
                basic_model=basic,
                premium_model=premium,
            )
            return (basic, premium)

        except ClientError as e:
            logger.error(
                "Failed to load default models from Parameter Store",
                error=str(e),
                error_code=e.response.get("Error", {}).get("Code"),
            )
            return self._get_fallback_models()
        except Exception as e:
            logger.error(
                "Unexpected error loading default models",
                error=str(e),
                exc_info=True,
            )
            return self._get_fallback_models()

    def update_default_models(
        self,
        basic_model_code: str,
        premium_model_code: str,
        updated_by: str = "admin",
    ) -> bool:
        """Update default model codes in Parameter Store.

        Args:
            basic_model_code: Model code for Free/Basic tier (e.g., "CLAUDE_3_5_SONNET_V2")
            premium_model_code: Model code for Premium/Ultimate tier (e.g., "CLAUDE_OPUS_4_5")
            updated_by: User or system updating the values

        Returns:
            True if update successful, False otherwise
        """
        try:
            # Update basic model parameter
            self.ssm_client.put_parameter(
                Name=f"{self.parameter_prefix}/models/default_basic",
                Value=basic_model_code,
                Type="String",
                Overwrite=True,
                Description=f"Default model code for Free/Basic tier topics (updated by {updated_by})",
            )

            # Update premium model parameter
            self.ssm_client.put_parameter(
                Name=f"{self.parameter_prefix}/models/default_premium",
                Value=premium_model_code,
                Type="String",
                Overwrite=True,
                Description=f"Default model code for Premium/Ultimate tier topics (updated by {updated_by})",
            )

            # Clear cache to pick up new values
            self.clear_cache()

            logger.info(
                "Default models updated in Parameter Store",
                basic_model=basic_model_code,
                premium_model=premium_model_code,
                updated_by=updated_by,
            )
            return True

        except ClientError as e:
            logger.error(
                "Failed to update default models in Parameter Store",
                error=str(e),
                error_code=e.response.get("Error", {}).get("Code"),
            )
            return False
        except Exception as e:
            logger.error(
                "Unexpected error updating default models",
                error=str(e),
                exc_info=True,
            )
            return False

    def _get_fallback_models(self) -> tuple[str, str]:
        """Get hardcoded fallback model codes.

        Used when Parameter Store is unavailable or parameters don't exist.

        Returns:
            Tuple of (basic_model_code, premium_model_code)
        """
        logger.info("Using hardcoded fallback default models")
        return ("CLAUDE_3_5_SONNET_V2", "CLAUDE_OPUS_4_5")

    def clear_cache(self) -> None:
        """Clear the parameter cache.

        Useful for testing or forcing a fresh read from Parameter Store.
        """
        self._cache = None
        self._cache_time = None
        logger.debug("Parameter Store cache cleared")


# Module-level singleton (lazy initialization)
_parameter_store_instance: ParameterStoreService | None = None


def get_parameter_store_service(
    region: str | None = None,
    stage: str | None = None,
) -> ParameterStoreService:
    """Get or create the global ParameterStoreService singleton.

    Args:
        region: AWS region (uses default if not provided)
        stage: Environment stage (uses default if not provided)

    Returns:
        Global ParameterStoreService instance
    """
    global _parameter_store_instance
    if _parameter_store_instance is None:
        from coaching.src.core.config_multitenant import get_settings

        settings = get_settings()
        _parameter_store_instance = ParameterStoreService(
            region=region or settings.aws_region,
            stage=stage or settings.stage,
        )
    return _parameter_store_instance


__all__ = [
    "ParameterStoreService",
    "get_parameter_store_service",
]
