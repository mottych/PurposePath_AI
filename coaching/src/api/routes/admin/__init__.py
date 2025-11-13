"""Admin API routes for template and model management."""

from fastapi import APIRouter

from .analytics import router as analytics_router
from .configurations import router as configurations_router
from .conversations import router as conversations_router
from .interactions import router as interactions_router
from .models import router as models_router
from .prompts import router as prompts_router

# Create main admin router
router = APIRouter(prefix="/admin", tags=["Admin"])

# Include sub-routers
router.include_router(interactions_router)
router.include_router(models_router)
router.include_router(prompts_router)
router.include_router(configurations_router)
router.include_router(conversations_router)
router.include_router(analytics_router)

__all__ = ["router"]
