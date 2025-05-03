"""Unexpected error handler for unhandled exceptions."""
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.api.middleware.error_handlers.base_handler import BaseErrorHandler


class UnexpectedErrorHandler(BaseErrorHandler):
    """Handler for unexpected server errors."""
    
    async def handle_unexpected_error(
        self, 
        request: Request, 
        exc: Exception
    ) -> JSONResponse:
        """Handle unexpected server errors."""
        error_id = self._generate_error_id()
        
        # Log the full traceback
        self._log_error(
            message=f"Unexpected Error: {str(exc).replace('{', '{{').replace('}', '}}')}",
            error_id=error_id,
            path=request.url.path,
            method=request.method,
            exception_type=type(exc).__name__,
            level="error"
        )
        
        # In production, don't expose internal error details
        message = "An unexpected error occurred"
        if self._is_development_environment():
            # Development environment - include more details
            message = f"{type(exc).__name__}: {str(exc)}"
        
        return self._create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            message=message,
            error_id=error_id,
            path=request.url.path
        )
