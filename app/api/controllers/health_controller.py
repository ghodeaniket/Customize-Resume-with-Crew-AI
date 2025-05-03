"""Health check controller for API status monitoring."""
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Annotated

from fastapi import Depends

from app.core.config import settings
from app.core.logging import logger


class HealthController:
    """Controller for health check operations."""
    
    async def check_health(self) -> Dict[str, Any]:
        """Check the health status of the API.
        
        Returns:
            Dict containing health status information
        """
        try:
            # Check file system access (instead of database)
            storage_healthy = await self._check_storage()
            
            # Check external dependencies
            deps_healthy = await self._check_dependencies()
            
            # Overall health status
            is_healthy = storage_healthy and deps_healthy
            
            health_info = {
                "status": "healthy" if is_healthy else "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": settings.PROJECT_VERSION if hasattr(settings, 'PROJECT_VERSION') else "1.0.0",
                "environment": settings.ENVIRONMENT if hasattr(settings, 'ENVIRONMENT') else "development",
                "checks": {
                    "storage": {
                        "status": "up" if storage_healthy else "down",
                        "description": "File system access"
                    },
                    "dependencies": {
                        "status": "up" if deps_healthy else "down"
                    }
                }
            }
            
            logger.info(
                f"Health check completed - status: {health_info['status']}", 
                extra=health_info
            )
            
            return health_info
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def _check_storage(self) -> bool:
        """Check file system access and storage availability.
        
        Returns:
            bool: True if storage is accessible, False otherwise
        """
        try:
            import os
            from pathlib import Path
            
            # Check uploads directory exists and is writable
            uploads_dir = Path(settings.UPLOADS_DIR) if hasattr(settings, 'UPLOADS_DIR') else Path('uploads')
            
            if not uploads_dir.exists():
                uploads_dir.mkdir(parents=True, exist_ok=True)
            
            # Try to write a test file
            test_file = uploads_dir / ".health_check"
            test_file.write_text("health check")
            test_file.unlink()  # Delete the test file
            
            return True
            
        except Exception as e:
            logger.error(f"Storage health check failed: {str(e)}")
            return False
    
    async def _check_dependencies(self) -> bool:
        """Check external dependencies health.
        
        Returns:
            bool: True if all dependencies are healthy, False otherwise
        """
        # For now, we can check things like:
        # - Document processing service
        # - CrewAI service
        # - External APIs if any
        
        # Placeholder - check if critical modules can be imported
        try:
            import crewai
            import PyPDF2
            import docx
            return True
        except ImportError as e:
            logger.error(f"Dependency check failed: {str(e)}")
            return False
    
    async def check_readiness(self) -> Dict[str, Any]:
        """Check if the application is ready to accept requests.
        
        Returns:
            Dict containing readiness status
        """
        storage_ready = await self._check_storage()
        
        is_ready = storage_ready
        
        return {
            "ready": is_ready,
            "storage": "ready" if storage_ready else "not_ready",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def check_liveness(self) -> Dict[str, Any]:
        """Check if the application is running (alive).
        
        Returns:
            Dict containing liveness status
        """
        # Liveness check should be as simple as possible
        # It indicates if the app is running, not if it's functional
        return {
            "alive": True,
            "timestamp": datetime.utcnow().isoformat()
        }
