from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient

from fastapi import APIRouter, Header
from jose import JWTError, jwt

from shared.models.schemas import ApiResponse
from shared.services.aws_helpers import get_secretsmanager_client
from src.core.config_multitenant import settings
from src.models.requests import OnboardingSuggestionRequest
from src.models.responses import OnboardingSuggestionResponse

router = APIRouter()


def _get_jwt_secret() -> str:
    try:
        if settings.jwt_secret_arn:
            client: SecretsManagerClient = get_secretsmanager_client(settings.aws_region)
            resp = client.get_secret_value(SecretId=settings.jwt_secret_arn)
            s = resp.get("SecretString") or ""
            try:
                obj = json.loads(s)
                return str(obj.get("secret", s))
            except Exception:
                return s
        return "change-me-in-prod"
    except Exception:
        return "change-me-in-prod"


def _authorized(auth_header: str | None) -> bool:
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return False
    token = auth_header.split(" ", 1)[1]
    secret = _get_jwt_secret()
    try:
        jwt.decode(token, secret, algorithms=[settings.jwt_algorithm], issuer=settings.jwt_issuer)
        return True
    except JWTError:
        return False


@router.post("/onboarding", response_model=ApiResponse[OnboardingSuggestionResponse])
async def suggest_onboarding(
    payload: OnboardingSuggestionRequest, authorization: str | None = Header(default=None)
) -> ApiResponse[OnboardingSuggestionResponse]:
    if not _authorized(authorization):
        return ApiResponse(success=False, error="Unauthorized")

    # Simple deterministic stub; can be replaced with Bedrock/LLM call
    base = {
        "niche": "Consider specializing in a focused segment to increase resonance.",
        "ica": "Define your ideal customer by role, pains, and goals.",
        "valueProposition": "We reduce time-to-insight by unifying siloed data and automating analysis.",
    }[payload.kind]

    suggestion = (
        base
        if not payload.current
        else f"{base} Based on your input, strengthen it around: '{payload.current}'."
    )

    response = OnboardingSuggestionResponse(suggestion=suggestion)
    return ApiResponse(success=True, data=response)
