"""API v1 router aggregator for clear version management."""
from fastapi import APIRouter

from app.api.routes import health, resumes, batch

api_router = APIRouter()

# Include all v1 route modules
api_router.include_router(health.router, tags=["health"])
api_router.include_router(resumes.router, tags=["resumes"]) 
api_router.include_router(batch.router, tags=["batch"])

# Future routes can be added here as they are developed
# api_router.include_router(users.router, tags=["users"])
# api_router.include_router(analysis.router, tags=["analysis"])
