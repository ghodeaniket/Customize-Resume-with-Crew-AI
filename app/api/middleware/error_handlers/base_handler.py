"""Base error handler with common functionality."""
import sys
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi.responses import JSONResponse

from app.core.logging import logger


class BaseErrorHandler:
    """Base error handler with common error handling functionality."""
    
    def _generate_error_id(self) -> str:
        """Generate a unique error ID for tracking."""
        return f"err_{uuid.uuid4().hex[:8]}"
    
    def _create_error_response(
        self,
        status_code: int,
        error_code: str,
        message: str,
        error_id: str,
        path: str,
        suggestion: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Create standardized error response."""
        content = {
            "error": {
                "code": error_code,
                "message": message,
                "error_id": error_id,
                "path": path,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        if suggestion:
            content["error"]["suggestion"] = suggestion
        
        if details:
            content["error"]["details"] = details
        
        return JSONResponse(
            status_code=status_code,
            content=content,
            headers={
                "X-Error-ID": error_id,
                "X-Content-Type-Options": "nosniff"
            }
        )
    
    def _is_development_environment(self) -> bool:
        """Check if we're in a development environment."""
        return hasattr(sys, '_getframe') and sys._getframe().f_code.co_name != 'dispatch'
    
    def _log_error(
        self, 
        message: str, 
        error_id: str, 
        path: str, 
        method: str, 
        level: str = "warning",
        **kwargs
    ) -> None:
        """Log error with consistent format."""
        extra = {
            "error_id": error_id,
            "path": path,
            "method": method,
            **kwargs
        }
        
        if level == "error":
            logger.error(message, extra=extra, exc_info=True)
        elif level == "warning":
            logger.warning(message, extra=extra)
        else:
            logger.info(message, extra=extra)
