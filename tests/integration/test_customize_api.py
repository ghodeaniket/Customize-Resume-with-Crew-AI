"""Integration tests for resume customization API endpoints."""
import os
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.resume_service import ResumeService


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_resume_service():
    """Mock the resume service."""
    with patch("app.api.routes.resumes.get_resume_service") as mock_get_service:
        mock_service = AsyncMock(spec=ResumeService)
        mock_get_service.return_value = mock_service
        yield mock_service


def test_customize_resume_endpoint(test_client, mock_resume_service):
    """Test the customize resume endpoint."""
    # Configure mock resume service
    mock_resume_service.resume_exists.return_value = True
    mock_resume_service.customize_resume.return_value = "test-task-id"
    
    # Test request data
    request_data = {
        "resume_id": "test-resume-id",
        "job_description": "We are looking for a Python developer with FastAPI experience",
        "customize_level": "standard"
    }
    
    # Make request to the API
    response = test_client.post("/api/resumes/customize", json=request_data)
    
    # Check response
    assert response.status_code == 200
    assert response.json()["status"] == "processing"
    assert "task_id" in response.json()
    
    # Verify service method calls
    mock_resume_service.resume_exists.assert_called_once_with("test-resume-id")


def test_customize_resume_endpoint_resume_not_found(test_client, mock_resume_service):
    """Test the customize resume endpoint with a non-existent resume."""
    # Configure mock resume service
    mock_resume_service.resume_exists.return_value = False
    
    # Test request data
    request_data = {
        "resume_id": "non-existent-resume-id",
        "job_description": "We are looking for a Python developer with FastAPI experience",
        "customize_level": "standard"
    }
    
    # Make request to the API
    response = test_client.post("/api/resumes/customize", json=request_data)
    
    # Check response
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
    
    # Verify service method calls
    mock_resume_service.resume_exists.assert_called_once_with("non-existent-resume-id")
    mock_resume_service.customize_resume.assert_not_called()


def test_customize_resume_endpoint_invalid_job_description(test_client, mock_resume_service):
    """Test the customize resume endpoint with an invalid job description."""
    # Configure mock resume service
    mock_resume_service.resume_exists.return_value = True
    
    # Test request data with empty job description
    request_data = {
        "resume_id": "test-resume-id",
        "job_description": "",
        "customize_level": "standard"
    }
    
    # Make request to the API
    response = test_client.post("/api/resumes/customize", json=request_data)
    
    # Check response
    assert response.status_code == 400
    assert "job description" in response.json()["detail"].lower()
    
    # Verify service method calls
    mock_resume_service.customize_resume.assert_not_called()


def test_get_customization_status_endpoint(test_client, mock_resume_service):
    """Test the get customization status endpoint."""
    # Configure mock task service (through patch)
    with patch("app.api.routes.resumes.get_task_service") as mock_get_task_service:
        mock_task_service = AsyncMock()
        mock_get_task_service.return_value = mock_task_service
        
        # Mock task data
        mock_task_data = {
            "task_id": "test-task-id",
            "status": "processing",
            "progress": 50.0,
            "created_at": 1619712000.0,
            "updated_at": 1619712060.0
        }
        mock_task_service.get_task.return_value = mock_task_data
        
        # Make request to the API
        response = test_client.get("/api/resumes/customization/test-task-id")
        
        # Check response
        assert response.status_code == 200
        assert response.json()["task_id"] == "test-task-id"
        assert response.json()["status"] == "processing"
        assert response.json()["progress"] == 50.0
        
        # Verify service method calls
        mock_task_service.get_task.assert_called_once_with("test-task-id")


def test_get_customization_result_endpoint(test_client, mock_resume_service):
    """Test the get customization result endpoint."""
    # Configure mock resume service
    mock_result = {
        "task_id": "test-task-id",
        "status": "completed",
        "result": "Customized resume content",
        "metadata": {"processing_time_ms": 1500}
    }
    mock_resume_service.get_customization_result.return_value = mock_result
    
    # Make request to the API
    response = test_client.get("/api/resumes/customization/test-task-id/result")
    
    # Check response
    assert response.status_code == 200
    assert response.json()["task_id"] == "test-task-id"
    assert response.json()["status"] == "completed"
    assert response.json()["result"] == "Customized resume content"
    
    # Verify service method calls
    mock_resume_service.get_customization_result.assert_called_once_with("test-task-id")


def test_get_customization_result_not_complete(test_client, mock_resume_service):
    """Test the get customization result endpoint for incomplete task."""
    # Configure mock resume service
    mock_result = {
        "task_id": "test-task-id",
        "status": "processing",
        "progress": 75.0,
        "message": "Task not completed"
    }
    mock_resume_service.get_customization_result.return_value = mock_result
    
    # Make request to the API
    response = test_client.get("/api/resumes/customization/test-task-id/result")
    
    # Check response
    assert response.status_code == 400
    assert "not complete" in response.json()["detail"].lower()
    
    # Verify service method calls
    mock_resume_service.get_customization_result.assert_called_once_with("test-task-id")
