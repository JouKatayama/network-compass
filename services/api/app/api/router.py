from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.interactions import router as interactions_router
from app.api.routes.network import router as network_router
from app.api.routes.people import router as people_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(interactions_router, prefix="/api/v1")
api_router.include_router(network_router, prefix="/api/v1")
api_router.include_router(people_router, prefix="/api/v1")
