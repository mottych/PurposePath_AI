"""Admin API routes for template and model management."""

from fastapi import APIRouter

from .analytics import router as analytics_router
from .conversations import router as conversations_router
from .models import router as models_router
from .templates import router as templates_router

# Create main admin router
router = APIRouter(prefix="/admin", tags=["Admin"])

# Include sub-routers
router.include_router(models_router)
router.include_router(templates_router)
router.include_router(conversations_router)
router.include_router(analytics_router)

__all__ = ["router"]
