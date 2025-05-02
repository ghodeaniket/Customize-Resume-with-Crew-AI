"""
Comprehensive test fixtures for all test modules.

This file contains fixtures for unit, integration, and performance tests.
"""
import os
import sys
import uuid
import json
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.document_storage_service import DocumentStorageService
from app.services.resume_service import ResumeService
from app.services.task_service import TaskService
from app.infrastructure.document_processor import DocumentProcessor
from app.crews.agents.analyzer import create_resume_analyzer_agent
from app.crews.agents.optimizer import create_resume_optimizer_agent
from main import app as main_app


# ==================== Base Application Fixtures ====================

@pytest.fixture
def app():
    """Return the FastAPI app instance."""
    return main_app


@pytest.fixture
def client(app):
    """Return a TestClient for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client(app):
    """Return an AsyncClient for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ==================== Mock Service Fixtures ====================

@pytest.fixture
def mock_document_processor():
    """Return a mocked DocumentProcessor."""
    with patch("app.api.dependencies.get_document_processor") as mock:
        processor = MagicMock(spec=DocumentProcessor)
        processor.extract_text_from_bytes.return_value = "Sample resume text for testing"
        processor.is_supported_file_type.return_value = True
        mock.return_value = processor
        yield processor


@pytest.fixture
def mock_resume_service():
    """Return a mocked ResumeService."""
    with patch("app.api.dependencies.get_resume_service") as mock:
        service = MagicMock(spec=ResumeService)
        service.resume_exists.return_value = True
        service.get_resume_data.return_value = {
            "text": "Sample resume text for testing",
            "metadata": {
                "status": "completed",
                "filename": "test_resume.pdf",
                "created_at": "2025-04-30T12:00:00Z",
                "updated_at": "2025-04-30T12:01:00Z"
            }
        }
        service.get_customization_result.return_value = {
            "task_id": "test-task-id",
            "status": "completed",
            "result": "Customized resume text for testing",
            "metadata": {
                "processing_time_ms": 2500,
                "customize_level": "standard",
                "completion_time": 1719759382.45
            }
        }
        mock.return_value = service
        yield service


@pytest.fixture
def mock_task_service():
    """Return a mocked TaskService."""
    with patch("app.api.dependencies.get_task_service") as mock:
        service = MagicMock(spec=TaskService)
        service.create_task.return_value = {"task_id": "test-task-id"}
        service.get_task.return_value = {
            "task_id": "test-task-id",
            "status": "completed",
            "progress": 100.0,
            "created_at": "2025-04-30T12:00:00Z",
            "updated_at": "2025-04-30T12:01:00Z"
        }
        mock.return_value = service
        yield service


@pytest.fixture
def mock_storage_service():
    """Return a mocked DocumentStorageService."""
    with patch("app.api.dependencies.get_document_storage_service") as mock:
        service = MagicMock(spec=DocumentStorageService)
        service.save_document.return_value = Path("/tmp/test.pdf")
        service.save_extracted_text.return_value = Path("/tmp/extracted.txt")
        service.save_metadata.return_value = None
        mock.return_value = service
        yield service


@pytest.fixture
def mock_crewai_agents():
    """Mock CrewAI agents."""
    with patch("app.crews.agents.analyzer.create_resume_analyzer_agent") as mock_analyzer:
        with patch("app.crews.agents.optimizer.create_resume_optimizer_agent") as mock_optimizer:
            mock_analyzer_agent = MagicMock()
            mock_optimizer_agent = MagicMock()
            
            mock_analyzer.return_value = mock_analyzer_agent
            mock_optimizer.return_value = mock_optimizer_agent
            
            yield mock_analyzer_agent, mock_optimizer_agent


# ==================== Test Resources Fixtures ====================

@pytest.fixture
def test_uploads_dir():
    """Create a temporary directory for uploads during tests."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after the test
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_task_id():
    """Generate a random task ID for testing."""
    return str(uuid.uuid4())


@pytest.fixture
def test_pdf_path():
    """Get path to test PDF file."""
    test_data_dir = Path(__file__).parent.parent / "test_data"
    pdf_path = test_data_dir / "test_resume.pdf"
    
    if not pdf_path.exists():
        pytest.fail(f"Test PDF file not found at {pdf_path}. Run create_test_pdf.py first.")
    
    return pdf_path


@pytest.fixture
def test_docx_path():
    """Get path to test DOCX file."""
    test_data_dir = Path(__file__).parent.parent / "test_data"
    docx_path = test_data_dir / "test_resume.docx"
    
    if not docx_path.exists():
        pytest.fail(f"Test DOCX file not found at {docx_path}. Run create_test_docx.py first.")
    
    return docx_path


@pytest.fixture
def test_pdf_content(test_pdf_path):
    """Get the binary content of the test PDF file."""
    with open(test_pdf_path, "rb") as f:
        return f.read()


@pytest.fixture
def test_docx_content(test_docx_path):
    """Get the binary content of the test DOCX file."""
    with open(test_docx_path, "rb") as f:
        return f.read()


@pytest.fixture
def test_job_description():
    """Get the test job description text."""
    test_data_dir = Path(__file__).parent.parent / "test_data"
    jd_path = test_data_dir / "test_job_description.txt"
    
    with open(jd_path, "r") as f:
        return f.read()


@pytest.fixture
def test_customization_request(test_task_id, test_job_description):
    """Get a test customization request."""
    return {
        "resume_id": test_task_id,
        "job_description": test_job_description,
        "customize_level": "standard"
    }


@pytest.fixture
def test_customization_request_json():
    """Get the test customization request JSON."""
    test_data_dir = Path(__file__).parent.parent / "test_data"
    json_path = test_data_dir / "customization_request.json"
    
    with open(json_path, "r") as f:
        return json.load(f)


# ==================== Test Helpers Fixtures ====================

@pytest.fixture
def wait_for_task_completion():
    """Helper fixture to wait for a task to complete with timeout."""
    async def _wait_for_completion(client, task_endpoint, task_id, timeout=10, interval=0.5):
        """
        Wait for a task to complete with timeout.
        
        Args:
            client: TestClient to make requests
            task_endpoint: API endpoint for checking task status
            task_id: ID of the task to check
            timeout: Maximum time to wait (seconds)
            interval: Time between checks (seconds)
            
        Returns:
            dict: The final task status response
            
        Raises:
            TimeoutError: If the task doesn't complete within the timeout
        """
        endpoint = f"{task_endpoint}/{task_id}"
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Failed to get task status: {response.text}"
            
            data = response.json()
            status = data.get("status")
            
            if status in ["completed", "failed"]:
                return data
                
            await asyncio.sleep(interval)
        
        raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")
    
    return _wait_for_completion
    

@pytest.fixture
def verify_task_success():
    """Helper fixture to verify a task completed successfully."""
    def _verify_success(task_data, expected_status="completed"):
        """
        Verify a task completed successfully.
        
        Args:
            task_data: Task status response data
            expected_status: Expected status string
            
        Returns:
            bool: True if verification passed
            
        Raises:
            AssertionError: If verification fails
        """
        assert task_data.get("status") == expected_status, f"Task status is {task_data.get('status')}, not {expected_status}"
        assert task_data.get("progress") == 100.0, f"Task progress is {task_data.get('progress')}%, not 100%"
        assert task_data.get("result_url") is not None, "Result URL is missing"
        
        return True
    
    return _verify_success


@pytest.fixture
def assert_valid_response():
    """Helper fixture for validating response schemas."""
    def _assert_valid(response, expected_status=200, expected_fields=None):
        """
        Assert that a response is valid.
        
        Args:
            response: HTTP response object
            expected_status: Expected HTTP status code
            expected_fields: List of field names that should be in the response
            
        Returns:
            dict: Response JSON if validation passed
            
        Raises:
            AssertionError: If validation fails
        """
        assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}: {response.text}"
        
        # For non-JSON responses or empty responses (e.g., 204 No Content)
        if expected_status in [204, 304] or not response.content:
            return None
            
        data = response.json()
        
        if expected_fields:
            for field in expected_fields:
                assert field in data, f"Expected field '{field}' missing from response: {data}"
        
        return data
    
    return _assert_valid
