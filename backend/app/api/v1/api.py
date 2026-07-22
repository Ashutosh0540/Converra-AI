from fastapi import APIRouter

from app.api.v1.endpoints.ai import router as ai_router
from app.api.v1.endpoints.knowledge import router as knowledge_router
from app.api.v1.endpoints.organization import router as organization_router
from app.api.v1.endpoints.user import router as user_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(ai_router)
api_router.include_router(knowledge_router)
api_router.include_router(organization_router)
api_router.include_router(user_router)
