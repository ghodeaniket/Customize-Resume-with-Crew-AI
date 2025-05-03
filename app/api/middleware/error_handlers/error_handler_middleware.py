"""Unified error handler middleware that delegates to specific handlers."""
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    DocumentProcessingError,
    UnsupportedFileTypeError,
    ResumeNotFoundError,
    TaskNotFoundError,
    CustomizationError
)
from app.api.middleware.error_handlers.http_handler import HTTPErrorHandler
from app.api.middleware.error_handlers.validation_handler import ValidationErrorHandler
from app.api.middleware.error_handlers.custom_error_handler import CustomErrorHandler
from app.api.middleware.error_handlers.unexpected_error_handler import UnexpectedErrorHandler


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling and standardizing error responses."""
    
    def __init__(self, app):
        """Initialize with error handler instances."""
        super().__init__(app)
        self.http_handler = HTTPErrorHandler()
        self.validation_handler = ValidationErrorHandler()
        self.custom_handler = CustomErrorHandler()
        self.unexpected_handler = UnexpectedErrorHandler()
    
    async def dispatch(self, request: Request, call_next):
        """Process requests and handle any exceptions."""
        try:
            return await call_next(request)
        
        except HTTPException as http_exc:
            # FastAPI HTTP exceptions
            return await self.http_handler.handle_http_exception(request, http_exc)
        
        except StarletteHTTPException as starlette_exc:
            # Starlette HTTP exceptions
            return await self.http_handler.handle_starlette_http_exception(request, starlette_exc)
        
        except RequestValidationError as validation_exc:
            # Request validation errors
            return await self.validation_handler.handle_validation_error(request, validation_exc)
        
        except DocumentProcessingError as doc_exc:
            # Custom document processing errors
            return await self.custom_handler.handle_document_error(request, doc_exc)
        
        except UnsupportedFileTypeError as file_exc:
            # Unsupported file type errors
            return await self.custom_handler.handle_file_type_error(request, file_exc)
        
        except (ResumeNotFoundError, TaskNotFoundError) as not_found_exc:
            # Resource not found errors
            return await self.custom_handler.handle_not_found_error(request, not_found_exc)
        
        except CustomizationError as custom_exc:
            # Customization errors
            return await self.custom_handler.handle_customization_error(request, custom_exc)
        
        except Exception as exc:
            # All other unhandled exceptions
            return await self.unexpected_handler.handle_unexpected_error(request, exc)
