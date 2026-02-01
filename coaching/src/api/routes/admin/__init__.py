"""Admin API routes for template and model management."""

from fastapi import APIRouter

from .analytics import router as analytics_router
from .interactions import router as interactions_router
from .models import router as models_router
from .topics import router as topics_router

# Create main admin router
router = APIRouter(prefix="/admin", tags=["Admin"])

# Include sub-routers
router.include_router(interactions_router)
router.include_router(models_router)
router.include_router(analytics_router)
router.include_router(topics_router)

__all__ = ["router"]
