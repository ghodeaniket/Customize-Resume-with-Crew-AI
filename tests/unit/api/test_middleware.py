"""Unit tests for API middleware."""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.middleware.error_handler import ErrorHandlerMiddleware
from app.core.exceptions import (
    DocumentProcessingError,
    UnsupportedFileTypeError,
    ResumeNotFoundError,
    CustomizationError
)


class TestErrorHandlerMiddleware:
    """Test cases for ErrorHandlerMiddleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance for testing."""
        return ErrorHandlerMiddleware(app=Mock())
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request object."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/test"
        request.method = "GET"
        return request
    
    @pytest.mark.asyncio
    async def test_handle_http_exception(self, middleware, mock_request):
        """Test handling FastAPI HTTPException."""
        # Create a FastAPI HTTPException
        http_exc = HTTPException(status_code=404, detail="Resource not found")
        
        # Mock call_next to raise the exception
        async def mock_call_next(request):
            raise http_exc
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 404
        assert b"Resource not found" in response.body
    
    @pytest.mark.asyncio
    async def test_handle_starlette_http_exception(self, middleware, mock_request):
        """Test handling Starlette HTTPException."""
        # Create a Starlette HTTPException
        starlette_exc = StarletteHTTPException(status_code=400, detail="Bad request")
        
        async def mock_call_next(request):
            raise starlette_exc
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 400
        assert b"Bad request" in response.body
    
    @pytest.mark.asyncio
    async def test_handle_validation_error(self, middleware, mock_request):
        """Test handling request validation errors."""
        # Create a mock validation error
        validation_exc = RequestValidationError(
            errors=[{
                "loc": ("body", "field_name"),
                "msg": "Field is required",
                "type": "value_error.missing"
            }]
        )
        
        async def mock_call_next(request):
            raise validation_exc
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 422
        assert b"VALIDATION_ERROR" in response.body
        assert b"Field is required" in response.body
    
    @pytest.mark.asyncio
    async def test_handle_document_processing_error(self, middleware, mock_request):
        """Test handling custom document processing error."""
        doc_exc = DocumentProcessingError("Failed to process document")
        
        async def mock_call_next(request):
            raise doc_exc
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 422
        assert b"DOCUMENT_PROCESSING_ERROR" in response.body
        assert b"Failed to process document" in response.body
    
    @pytest.mark.asyncio
    async def test_handle_unsupported_file_type_error(self, middleware, mock_request):
        """Test handling unsupported file type error."""
        file_exc = UnsupportedFileTypeError("File type .exe not supported")
        
        async def mock_call_next(request):
            raise file_exc
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 400
        assert b"UNSUPPORTED_FILE_TYPE" in response.body
        assert b"Please upload PDF, DOCX, or TXT files" in response.body
    
    @pytest.mark.asyncio
    async def test_handle_resume_not_found_error(self, middleware, mock_request):
        """Test handling resume not found error."""
        not_found_exc = ResumeNotFoundError("test-resume-id")
        
        async def mock_call_next(request):
            raise not_found_exc
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 404
        assert b"RESOURCE_NOT_FOUND" in response.body
        assert b"test-resume-id" in response.body
    
    @pytest.mark.asyncio
    async def test_handle_customization_error(self, middleware, mock_request):
        """Test handling customization error."""
        custom_exc = CustomizationError("Failed to customize resume")
        
        async def mock_call_next(request):
            raise custom_exc
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 422
        assert b"CUSTOMIZATION_ERROR" in response.body
        assert b"Failed to customize resume" in response.body
    
    @pytest.mark.asyncio
    async def test_handle_unexpected_error(self, middleware, mock_request):
        """Test handling unexpected server error."""
        unexpected_exc = ValueError("Unexpected error occurred")
        
        async def mock_call_next(request):
            raise unexpected_exc
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 500
        assert b"INTERNAL_SERVER_ERROR" in response.body
    
    @pytest.mark.asyncio
    async def test_successful_request(self, middleware, mock_request):
        """Test successful request without errors."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.body = b'{"success": true}'
        
        async def mock_call_next(request):
            return mock_response
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 200
        assert response.body == b'{"success": true}'
