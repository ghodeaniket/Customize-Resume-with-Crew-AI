"""Unit tests for API controllers."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException, UploadFile
from datetime import datetime

from app.api.controllers.health_controller import HealthController
from app.api.controllers.resume_controller import ResumeController
from app.models.schemas.requests import CustomizationRequest
from app.models.schemas.responses import (
    ResumeUploadResponse,
    CustomizationResponse,
    TaskStatusResponse
)


class TestHealthController:
    """Test cases for HealthController."""
    
    @pytest.mark.asyncio
    async def test_check_health_success(self):
        """Test successful health check."""
        controller = HealthController()
        
        # Mock dependencies
        with patch.object(controller, '_check_database', return_value=True), \
             patch.object(controller, '_check_dependencies', return_value=True):
            
            result = await controller.check_health()
            
            assert result["status"] == "healthy"
            assert "timestamp" in result
            assert "checks" in result
    
    @pytest.mark.asyncio
    async def test_check_health_database_failure(self):
        """Test health check with database failure."""
        controller = HealthController()
        
        # Mock database check to fail
        with patch.object(controller, '_check_database', return_value=False), \
             patch.object(controller, '_check_dependencies', return_value=True):
            
            result = await controller.check_health()
            
            assert result["status"] == "unhealthy"
            assert result["checks"]["database"]["status"] == "down"
    
    @pytest.mark.asyncio
    async def test_check_readiness(self):
        """Test readiness check."""
        controller = HealthController()
        
        with patch.object(controller, '_check_database', return_value=True):
            result = await controller.check_readiness()
            
            assert result["ready"] is True
            assert result["database"] == "ready"
    
    @pytest.mark.asyncio
    async def test_check_liveness(self):
        """Test liveness check."""
        controller = HealthController()
        result = await controller.check_liveness()
        
        assert result["alive"] is True
        assert "timestamp" in result


class TestResumeController:
    """Test cases for ResumeController."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        return {
            "resume_service": Mock(),
            "task_service": Mock(),
            "storage_service": Mock(),
            "document_processor": Mock()
        }
    
    @pytest.fixture
    def controller(self, mock_services):
        """Create controller with mock services."""
        return ResumeController(
            resume_service=mock_services["resume_service"],
            task_service=mock_services["task_service"],
            storage_service=mock_services["storage_service"],
            document_processor=mock_services["document_processor"]
        )
    
    @pytest.mark.asyncio
    async def test_upload_resume_success(self, controller, mock_services):
        """Test successful resume upload."""
        # Create mock upload file
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test_resume.pdf"
        mock_file.read = AsyncMock(return_value=b"test content")
        
        # Mock is_supported_file_type
        with patch('app.api.controllers.resume_controller.is_supported_file_type', return_value=True):
            background_tasks = Mock()
            
            response = await controller.upload_resume(mock_file, background_tasks)
            
            assert isinstance(response, ResumeUploadResponse)
            assert response.filename == "test_resume.pdf"
            assert response.status == "processing"
            assert response.task_id is not None
            
            # Verify background task was added
            background_tasks.add_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_resume_unsupported_file_type(self, controller):
        """Test upload with unsupported file type."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test_resume.exe"
        
        with patch('app.api.controllers.resume_controller.is_supported_file_type', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await controller.upload_resume(mock_file, Mock())
            
            assert exc_info.value.status_code == 400
            assert "Unsupported file type" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_upload_resume_file_too_large(self, controller):
        """Test upload with file exceeding size limit."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test_resume.pdf"
        # Create content larger than 10MB
        mock_file.read = AsyncMock(return_value=b"x" * (10 * 1024 * 1024 + 1))
        
        with patch('app.api.controllers.resume_controller.is_supported_file_type', return_value=True):
            with pytest.raises(HTTPException) as exc_info:
                await controller.upload_resume(mock_file, Mock())
            
            assert exc_info.value.status_code == 413
            assert "File too large" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_resume_status_success(self, controller, mock_services):
        """Test successful resume status retrieval."""
        task_id = "test-task-id"
        mock_resume_data = {
            "metadata": {
                "status": "completed",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        }
        
        mock_services["resume_service"].get_resume_data = AsyncMock(
            return_value=mock_resume_data
        )
        
        response = await controller.get_resume_status(task_id)
        
        assert isinstance(response, TaskStatusResponse)
        assert response.task_id == task_id
        assert response.status == "completed"
        assert response.progress == 100.0
    
    @pytest.mark.asyncio
    async def test_get_resume_status_not_found(self, controller, mock_services):
        """Test resume status for non-existent task."""
        task_id = "non-existent-task"
        
        mock_services["resume_service"].get_resume_data = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await controller.get_resume_status(task_id)
        
        assert exc_info.value.status_code == 404
        assert f"Resume task with ID {task_id} not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_customize_resume_success(self, controller, mock_services):
        """Test successful resume customization."""
        request = CustomizationRequest(
            resume_id="test-resume-id",
            job_description="Senior Python Developer with FastAPI experience",
            customize_level="standard"
        )
        
        mock_services["resume_service"].resume_exists = AsyncMock(return_value=True)
        mock_services["task_service"].create_task = AsyncMock(
            return_value={"task_id": "test-task-id"}
        )
        
        background_tasks = Mock()
        
        response = await controller.customize_resume(request, background_tasks)
        
        assert isinstance(response, CustomizationResponse)
        assert response.task_id == "test-task-id"
        assert response.status == "processing"
        
        # Verify background task was added
        background_tasks.add_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_customize_resume_not_found(self, controller, mock_services):
        """Test customization with non-existent resume."""
        request = CustomizationRequest(
            resume_id="non-existent",
            job_description="Job description",
            customize_level="standard"
        )
        
        mock_services["resume_service"].resume_exists = AsyncMock(return_value=False)
        
        with pytest.raises(HTTPException) as exc_info:
            await controller.customize_resume(request, Mock())
        
        assert exc_info.value.status_code == 404
        assert "Resume with ID non-existent not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_customize_resume_short_description(self, controller, mock_services):
        """Test customization with too short job description."""
        request = CustomizationRequest(
            resume_id="test-resume-id",
            job_description="Too short",
            customize_level="standard"
        )
        
        mock_services["resume_service"].resume_exists = AsyncMock(return_value=True)
        
        with pytest.raises(HTTPException) as exc_info:
            await controller.customize_resume(request, Mock())
        
        assert exc_info.value.status_code == 400
        assert "Job description is too short" in str(exc_info.value.detail)
