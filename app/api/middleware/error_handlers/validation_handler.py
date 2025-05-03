"""Validation error handler for request validation errors."""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.api.middleware.error_handlers.base_handler import BaseErrorHandler


class ValidationErrorHandler(BaseErrorHandler):
    """Handler for request validation errors."""
    
    async def handle_validation_error(
        self, 
        request: Request, 
        exc: RequestValidationError
    ) -> JSONResponse:
        """Handle request validation errors."""
        error_id = self._generate_error_id()
        
        # Format validation errors
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            errors.append({"field": field, "message": message})
        
        self._log_error(
            message="Validation Error",
            error_id=error_id,
            path=request.url.path,
            method=request.method,
            validation_errors=errors
        )
        
        return self._create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            error_id=error_id,
            path=request.url.path,
            details={"validation_errors": errors}
        )
