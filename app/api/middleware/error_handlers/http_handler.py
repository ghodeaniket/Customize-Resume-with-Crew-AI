"""HTTP error handler for FastAPI and Starlette exceptions."""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.middleware.error_handlers.base_handler import BaseErrorHandler


class HTTPErrorHandler(BaseErrorHandler):
    """Handler for HTTP-related exceptions."""
    
    async def handle_http_exception(
        self, 
        request: Request, 
        exc: HTTPException
    ) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        error_id = self._generate_error_id()
        
        self._log_error(
            message=f"HTTP Exception: {exc.detail}",
            error_id=error_id,
            path=request.url.path,
            method=request.method,
            status_code=exc.status_code
        )
        
        return self._create_error_response(
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            message=exc.detail,
            error_id=error_id,
            path=request.url.path
        )
    
    async def handle_starlette_http_exception(
        self, 
        request: Request, 
        exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle Starlette HTTP exceptions."""
        error_id = self._generate_error_id()
        
        self._log_error(
            message=f"Starlette HTTP Exception: {exc.detail}",
            error_id=error_id,
            path=request.url.path,
            method=request.method,
            status_code=exc.status_code
        )
        
        return self._create_error_response(
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            message=exc.detail,
            error_id=error_id,
            path=request.url.path
        )
