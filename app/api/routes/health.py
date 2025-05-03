"""Health check endpoints using controller pattern."""
from typing import Annotated, Dict, Any

from fastapi import APIRouter, Depends

from app.api.controllers.health_controller import HealthController
from app.models.schemas import responses

router = APIRouter(tags=["health"])


def get_health_controller() -> HealthController:
    """Get health controller instance."""
    return HealthController()


@router.get("/health", response_model=Dict[str, Any])
async def health_check(
    controller: Annotated[HealthController, Depends(get_health_controller)]
):
    """Health check endpoint to monitor API status.
    
    Returns comprehensive health information including:
    - Overall health status
    - Database connectivity
    - External dependencies status
    - API version and environment info
    
    Args:
        controller: Health controller dependency
        
    Returns:
        Dict containing health status information
    """
    return await controller.check_health()


@router.get("/health/ready", response_model=Dict[str, Any])
async def readiness_check(
    controller: Annotated[HealthController, Depends(get_health_controller)]
):
    """Readiness probe endpoint for Kubernetes/Docker deployments.
    
    Checks if the application is ready to serve traffic.
    Used by orchestration systems to determine service readiness.
    
    Args:
        controller: Health controller dependency
        
    Returns:
        Dict containing readiness status
    """
    return await controller.check_readiness()


@router.get("/health/live", response_model=Dict[str, Any])
async def liveness_check(
    controller: Annotated[HealthController, Depends(get_health_controller)]
):
    """Liveness probe endpoint for Kubernetes/Docker deployments.
    
    Simple check to verify the application is running.
    Used by orchestration systems to determine if the container should be restarted.
    
    Args:
        controller: Health controller dependency
        
    Returns:
        Dict containing liveness status
    """
    return await controller.check_liveness()
