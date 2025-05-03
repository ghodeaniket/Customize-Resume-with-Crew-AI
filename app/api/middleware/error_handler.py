"""Centralized error handling middleware for standardized error responses."""
import traceback
import sys
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import logger
from app.core.exceptions import (
    DocumentProcessingError,
    UnsupportedFileTypeError,
    ResumeNotFoundError,
    TaskNotFoundError,
    CustomizationError
)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling and standardizing error responses."""
    
    async def dispatch(self, request: Request, call_next):
        """Process requests and handle any exceptions."""
        try:
            return await call_next(request)
        
        except HTTPException as http_exc:
            # FastAPI HTTP exceptions
            return await self._handle_http_exception(request, http_exc)
        
        except StarletteHTTPException as starlette_exc:
            # Starlette HTTP exceptions
            return await self._handle_starlette_http_exception(request, starlette_exc)
        
        except RequestValidationError as validation_exc:
            # Request validation errors
            return await self._handle_validation_error(request, validation_exc)
        
        except DocumentProcessingError as doc_exc:
            # Custom document processing errors
            return await self._handle_document_error(request, doc_exc)
        
        except UnsupportedFileTypeError as file_exc:
            # Unsupported file type errors
            return await self._handle_file_type_error(request, file_exc)
        
        except (ResumeNotFoundError, TaskNotFoundError) as not_found_exc:
            # Resource not found errors
            return await self._handle_not_found_error(request, not_found_exc)
        
        except CustomizationError as custom_exc:
            # Customization errors
            return await self._handle_customization_error(request, custom_exc)
        
        except Exception as exc:
            # All other unhandled exceptions
            return await self._handle_unexpected_error(request, exc)
    
    async def _handle_http_exception(
        self, 
        request: Request, 
        exc: HTTPException
    ) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        error_id = self._generate_error_id()
        
        logger.warning(
            f"HTTP Exception: {exc.detail}", 
            extra={
                "error_id": error_id,
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        return self._create_error_response(
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            message=exc.detail,
            error_id=error_id,
            path=request.url.path
        )
    
    async def _handle_starlette_http_exception(
        self, 
        request: Request, 
        exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle Starlette HTTP exceptions."""
        error_id = self._generate_error_id()
        
        logger.warning(
            f"Starlette HTTP Exception: {exc.detail}", 
            extra={
                "error_id": error_id,
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        return self._create_error_response(
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            message=exc.detail,
            error_id=error_id,
            path=request.url.path
        )
    
    async def _handle_validation_error(
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
        
        logger.warning(
            f"Validation Error: {errors}", 
            extra={
                "error_id": error_id,
                "path": request.url.path,
                "method": request.method,
                "validation_errors": errors
            }
        )
        
        return self._create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            error_id=error_id,
            path=request.url.path,
            details={"validation_errors": errors}
        )
    
    async def _handle_document_error(
        self, 
        request: Request, 
        exc: DocumentProcessingError
    ) -> JSONResponse:
        """Handle document processing errors."""
        error_id = self._generate_error_id()
        
        logger.error(
            f"Document Processing Error: {exc.detail}", 
            extra={
                "error_id": error_id,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        return self._create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="DOCUMENT_PROCESSING_ERROR",
            message=exc.detail,
            error_id=error_id,
            path=request.url.path
        )
    
    async def _handle_file_type_error(
        self, 
        request: Request, 
        exc: UnsupportedFileTypeError
    ) -> JSONResponse:
        """Handle unsupported file type errors."""
        error_id = self._generate_error_id()
        
        logger.warning(
            f"Unsupported File Type: {exc.detail}", 
            extra={
                "error_id": error_id,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        return self._create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="UNSUPPORTED_FILE_TYPE",
            message=exc.detail,
            error_id=error_id,
            path=request.url.path,
            suggestion="Please upload PDF, DOCX, or TXT files"
        )
    
    async def _handle_not_found_error(
        self, 
        request: Request, 
        exc: Exception
    ) -> JSONResponse:
        """Handle resource not found errors."""
        error_id = self._generate_error_id()
        
        logger.warning(
            f"Resource Not Found: {exc.detail}", 
            extra={
                "error_id": error_id,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        return self._create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            message=exc.detail,
            error_id=error_id,
            path=request.url.path
        )
    
    async def _handle_customization_error(
        self, 
        request: Request, 
        exc: CustomizationError
    ) -> JSONResponse:
        """Handle customization errors."""
        error_id = self._generate_error_id()
        
        logger.error(
            f"Customization Error: {exc.detail}", 
            extra={
                "error_id": error_id,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        return self._create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="CUSTOMIZATION_ERROR",
            message=exc.detail,
            error_id=error_id,
            path=request.url.path
        )
    
    async def _handle_unexpected_error(
        self, 
        request: Request, 
        exc: Exception
    ) -> JSONResponse:
        """Handle unexpected server errors."""
        error_id = self._generate_error_id()
        
        # Log the full traceback
        logger.error(
            f"Unexpected Error: {str(exc)}", 
            exc_info=True,
            extra={
                "error_id": error_id,
                "path": request.url.path,
                "method": request.method,
                "exception_type": type(exc).__name__
            }
        )
        
        # In production, don't expose internal error details
        message = "An unexpected error occurred"
        if hasattr(sys, '_getframe') and sys._getframe().f_code.co_name != 'dispatch':
            # Development environment - include more details
            message = f"{type(exc).__name__}: {str(exc)}"
        
        return self._create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            message=message,
            error_id=error_id,
            path=request.url.path
        )
    
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
    
    def _generate_error_id(self) -> str:
        """Generate a unique error ID for tracking."""
        import uuid
        return f"err_{uuid.uuid4().hex[:8]}"
