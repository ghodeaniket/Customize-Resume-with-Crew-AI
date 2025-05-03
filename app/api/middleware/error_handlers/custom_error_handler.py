"""Custom error handler for application-specific exceptions."""
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    DocumentProcessingError,
    UnsupportedFileTypeError,
    ResumeNotFoundError,
    TaskNotFoundError,
    CustomizationError
)
from app.api.middleware.error_handlers.base_handler import BaseErrorHandler


class CustomErrorHandler(BaseErrorHandler):
    """Handler for application-specific custom exceptions."""
    
    async def handle_document_error(
        self, 
        request: Request, 
        exc: DocumentProcessingError
    ) -> JSONResponse:
        """Handle document processing errors."""
        error_id = self._generate_error_id()
        
        self._log_error(
            message=f"Document Processing Error: {exc.detail}",
            error_id=error_id,
            path=request.url.path,
            method=request.method,
            level="error"
        )
        
        return self._create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="DOCUMENT_PROCESSING_ERROR",
            message=exc.detail,
            error_id=error_id,
            path=request.url.path
        )
    
    async def handle_file_type_error(
        self, 
        request: Request, 
        exc: UnsupportedFileTypeError
    ) -> JSONResponse:
        """Handle unsupported file type errors."""
        error_id = self._generate_error_id()
        
        self._log_error(
            message=f"Unsupported File Type: {exc.detail}",
            error_id=error_id,
            path=request.url.path,
            method=request.method
        )
        
        return self._create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="UNSUPPORTED_FILE_TYPE",
            message=exc.detail,
            error_id=error_id,
            path=request.url.path,
            suggestion="Please upload PDF, DOCX, or TXT files"
        )
    
    async def handle_not_found_error(
        self, 
        request: Request, 
        exc: Exception
    ) -> JSONResponse:
        """Handle resource not found errors."""
        error_id = self._generate_error_id()
        
        self._log_error(
            message=f"Resource Not Found: {exc.detail}",
            error_id=error_id,
            path=request.url.path,
            method=request.method
        )
        
        return self._create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            message=exc.detail,
            error_id=error_id,
            path=request.url.path
        )
    
    async def handle_customization_error(
        self, 
        request: Request, 
        exc: CustomizationError
    ) -> JSONResponse:
        """Handle customization errors."""
        error_id = self._generate_error_id()
        
        self._log_error(
            message=f"Customization Error: {exc.detail}",
            error_id=error_id,
            path=request.url.path,
            method=request.method,
            level="error"
        )
        
        return self._create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="CUSTOMIZATION_ERROR",
            message=exc.detail,
            error_id=error_id,
            path=request.url.path
        )
