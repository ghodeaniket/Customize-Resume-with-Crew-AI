"""Integration tests for the Resume API endpoints."""
import pytest
import os
import uuid
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.services.resume_service import ResumeService


def test_health_check(test_client):
    """Test the health check endpoint."""
    response = test_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_resume_endpoint_pdf(test_client, sample_pdf_content, mock_process_resume):
    """Test the resume upload endpoint with PDF."""
    # Create test data
    test_pdf_path = Path(__file__).parent.parent / "data" / "test_resume.pdf"
    
    # Ensure test PDF exists
    if not test_pdf_path.exists():
        with open(test_pdf_path, "wb") as f:
            f.write(sample_pdf_content)
    
    # Upload file
    with open(test_pdf_path, "rb") as f:
        response = test_client.post(
            "/api/resumes/upload",
            files={"resume": ("test_resume.pdf", f, "application/pdf")}
        )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["filename"] == "test_resume.pdf"
    assert data["status"] == "processing"
    
    # Verify mock was called
    mock_process_resume.assert_called_once()


def test_upload_resume_endpoint_docx(test_client, sample_docx_content, mock_process_resume):
    """Test the resume upload endpoint with DOCX."""
    # Create test data
    test_docx_path = Path(__file__).parent.parent / "data" / "test_resume.docx"
    
    # Ensure test DOCX exists
    if not test_docx_path.exists():
        with open(test_docx_path, "wb") as f:
            f.write(sample_docx_content)
    
    # Upload file
    with open(test_docx_path, "rb") as f:
        response = test_client.post(
            "/api/resumes/upload",
            files={"resume": ("test_resume.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["filename"] == "test_resume.docx"
    assert data["status"] == "processing"


def test_upload_resume_endpoint_invalid_file(test_client):
    """Test the resume upload endpoint with invalid file type."""
    # Upload invalid file
    response = test_client.post(
        "/api/resumes/upload",
        files={"resume": ("invalid.xyz", b"invalid content", "application/octet-stream")}
    )
    
    # Check response
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_resume_endpoint_empty_file(test_client):
    """Test the resume upload endpoint with empty file."""
    # Upload empty file
    response = test_client.post(
        "/api/resumes/upload",
        files={"resume": ("empty.pdf", b"", "application/pdf")}
    )
    
    # Check response - should fail with either 400 or 500 status
    assert response.status_code in (400, 500)


def test_get_resume_status_endpoint(test_client):
    """Test the get resume status endpoint with mocked data."""
    # Mock task ID
    task_id = str(uuid.uuid4())
    
    # Create a mock implementation of get_resume_data
    async def mock_get_resume_data(task_id):
        return {
            "task_id": task_id,
            "metadata": {
                "status": "completed",
                "created_at": time.time() - 3600,
                "updated_at": time.time(),
                "file_size": 12345
            },
            "text": "Sample extracted text",
            "status": "completed"
        }
    
    # Patch the get_resume_data method
    with patch.object(
        ResumeService, 'get_resume_data', side_effect=mock_get_resume_data
    ):
        # Call the endpoint
        response = test_client.get(f"/api/resumes/{task_id}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] == "completed"
    assert data["progress"] == 100.0
    assert "result_url" in data


def test_get_resume_status_not_found(test_client):
    """Test the get resume status endpoint with non-existent task."""
    # Mock task ID that doesn't exist
    task_id = str(uuid.uuid4())
    
    # Create a mock implementation of get_resume_data that returns None
    async def mock_get_resume_data_none(task_id):
        return None
    
    # Patch the get_resume_data method
    with patch.object(
        ResumeService, 'get_resume_data', side_effect=mock_get_resume_data_none
    ):
        # Call the endpoint
        response = test_client.get(f"/api/resumes/{task_id}")
    
    # Check response
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_resume_text_endpoint(test_client):
    """Test the get resume text endpoint with mocked data."""
    # Mock task ID
    task_id = str(uuid.uuid4())
    
    # Sample text content
    sample_text = "This is a sample resume text for testing."
    
    # Create a mock implementation of get_resume_data
    async def mock_get_resume_data(task_id):
        return {
            "task_id": task_id,
            "metadata": {
                "status": "completed",
                "created_at": time.time() - 3600,
                "updated_at": time.time(),
                "file_size": 12345
            },
            "text": sample_text,
            "status": "completed"
        }
    
    # Patch the get_resume_data method
    with patch.object(
        ResumeService, 'get_resume_data', side_effect=mock_get_resume_data
    ):
        # Call the endpoint
        response = test_client.get(f"/api/resumes/{task_id}/text")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["text"] == sample_text
    assert "metadata" in data
