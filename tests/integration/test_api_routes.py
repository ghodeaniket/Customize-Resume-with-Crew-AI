"""Integration tests for API routes."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock

from main import app
from app.api.controllers.resume_controller import ResumeController
from app.api.controllers.health_controller import HealthController


class TestHealthRoutes:
    """Test cases for health check routes."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        with patch(
            'app.api.routes.health.get_health_controller',
            return_value=Mock(
                check_health=AsyncMock(return_value={
                    "status": "healthy",
                    "timestamp": "2025-05-03T00:00:00",
                    "version": "1.0.0",
                    "environment": "test",
                    "checks": {
                        "database": {"status": "up"},
                        "dependencies": {"status": "up"}
                    }
                })
            )
        ):
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "checks" in data
    
    def test_readiness_check(self, client):
        """Test readiness check endpoint."""
        with patch(
            'app.api.routes.health.get_health_controller',
            return_value=Mock(
                check_readiness=AsyncMock(return_value={
                    "ready": True,
                    "database": "ready",
                    "timestamp": "2025-05-03T00:00:00"
                })
            )
        ):
            response = client.get("/api/v1/health/ready")
            
            assert response.status_code == 200
            data = response.json()
            assert data["ready"] is True
    
    def test_liveness_check(self, client):
        """Test liveness check endpoint."""
        with patch(
            'app.api.routes.health.get_health_controller',
            return_value=Mock(
                check_liveness=AsyncMock(return_value={
                    "alive": True,
                    "timestamp": "2025-05-03T00:00:00"
                })
            )
        ):
            response = client.get("/api/v1/health/live")
            
            assert response.status_code == 200
            data = response.json()
            assert data["alive"] is True


class TestResumeRoutes:
    """Test cases for resume routes."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_controller(self):
        """Create mock resume controller."""
        controller = Mock(spec=ResumeController)
        controller.upload_resume = AsyncMock(return_value={
            "task_id": "test-task-id",
            "filename": "test_resume.pdf",
            "status": "processing"
        })
        controller.get_resume_status = AsyncMock(return_value={
            "task_id": "test-task-id",
            "status": "completed",
            "progress": 100.0,
            "created_at": "2025-05-03T00:00:00",
            "updated_at": "2025-05-03T00:00:00",
            "result_url": "/api/resumes/test-task-id/download"
        })
        controller.customize_resume = AsyncMock(return_value={
            "task_id": "custom-task-id",
            "status": "processing"
        })
        return controller
    
    def test_upload_resume(self, client, mock_controller):
        """Test resume upload endpoint."""
        with patch(
            'app.api.routes.resumes.get_resume_controller',
            return_value=mock_controller
        ):
            # Create test file
            files = {"resume": ("test_resume.pdf", b"test content", "application/pdf")}
            
            response = client.post("/api/v1/api/resumes/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-id"
            assert data["filename"] == "test_resume.pdf"
            assert data["status"] == "processing"
    
    def test_get_resume_status(self, client, mock_controller):
        """Test resume status endpoint."""
        with patch(
            'app.api.routes.resumes.get_resume_controller',
            return_value=mock_controller
        ):
            response = client.get("/api/v1/api/resumes/test-task-id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-id"
            assert data["status"] == "completed"
            assert data["progress"] == 100.0
    
    def test_customize_resume(self, client, mock_controller):
        """Test resume customization endpoint."""
        with patch(
            'app.api.routes.resumes.get_resume_controller',
            return_value=mock_controller
        ):
            request_data = {
                "resume_id": "test-resume-id",
                "job_description": "Senior Python Developer with FastAPI experience",
                "customize_level": "standard"
            }
            
            response = client.post("/api/v1/api/resumes/customize", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "custom-task-id"
            assert data["status"] == "processing"


class TestBatchRoutes:
    """Test cases for batch operation routes."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_task_service(self):
        """Create mock task service."""
        service = Mock()
        service.get_task = AsyncMock(return_value={
            "task_id": "test-task-id",
            "status": "completed",
            "progress": 100.0,
            "task_type": "resume_processing",
            "created_at": "2025-05-03T00:00:00",
            "updated_at": "2025-05-03T00:00:00"
        })
        return service
    
    def test_batch_task_status(self, client, mock_task_service):
        """Test batch task status endpoint."""
        with patch(
            'app.api.routes.batch.get_task_service',
            return_value=mock_task_service
        ):
            request_data = {
                "task_ids": ["task-1", "task-2"],
                "include_metadata": True
            }
            
            response = client.post("/api/v1/api/batch/tasks/status", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert "summary" in data
            assert data["summary"]["total_requested"] == 2
    
    def test_list_tasks(self, client, mock_task_service):
        """Test task list endpoint."""
        with patch(
            'app.api.routes.batch.get_task_service',
            return_value=mock_task_service
        ):
            response = client.get(
                "/api/v1/api/batch/tasks",
                params={
                    "page": 1,
                    "page_size": 10,
                    "task_type": "resume_processing"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert "pagination" in data
            assert data["pagination"]["current_page"] == 1
