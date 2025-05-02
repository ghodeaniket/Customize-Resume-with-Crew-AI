"""
Contract tests for the Resume Customizer API.

These tests verify that the API adheres to the defined contracts.
They ensure that the API responses match the expected schemas and
that backward compatibility is maintained.
"""
import pytest
import json
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from tests.contract.api_contracts import (
    HealthResponse,
    ResumeUploadResponse,
    TaskStatusResponse,
    ResumeTextResponse,
    CustomizationResponse,
    CustomizationResultResponse,
    ErrorResponse
)


@pytest.fixture
def client():
    """Return a TestClient for the FastAPI app."""
    return TestClient(app)


class TestHealthContract:
    """Test the health endpoint contract."""
    
    def test_health_endpoint_contract(self, client):
        """Test that the health endpoint response matches the contract."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        
        # Validate response against contract
        try:
            HealthResponse(**response.json())
        except ValidationError as e:
            pytest.fail(f"Health response does not match contract: {e}")
    
    def test_health_response_structure(self, client):
        """Test that the health response has all required fields."""
        response = client.get("/api/health")
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert data["status"] == "ok"
        
        # Ensure no extra fields
        with pytest.raises(ValidationError):
            HealthResponse(**{**data, "extra_field": "should not be allowed"})


class TestResumeUploadContract:
    """Test the resume upload endpoint contract."""
    
    def test_resume_upload_response_contract(self, client, test_pdf_path, mock_resume_service):
        """Test that the resume upload response matches the contract."""
        with open(test_pdf_path, "rb") as pdf_file:
            response = client.post(
                "/api/resumes/upload",
                files={"resume": ("test_resume.pdf", pdf_file, "application/pdf")}
            )
        
        assert response.status_code == 200
        
        # Validate response against contract
        try:
            ResumeUploadResponse(**response.json())
        except ValidationError as e:
            pytest.fail(f"Resume upload response does not match contract: {e}")
    
    def test_resume_upload_response_structure(self, client, test_pdf_path, mock_resume_service):
        """Test that the resume upload response has all required fields."""
        with open(test_pdf_path, "rb") as pdf_file:
            response = client.post(
                "/api/resumes/upload",
                files={"resume": ("test_resume.pdf", pdf_file, "application/pdf")}
            )
        
        data = response.json()
        
        # Check required fields
        assert "task_id" in data
        assert "filename" in data
        assert "status" in data
        assert data["filename"] == "test_resume.pdf"
        assert data["status"] == "processing"
        
        # Ensure no extra fields
        with pytest.raises(ValidationError):
            ResumeUploadResponse(**{**data, "extra_field": "should not be allowed"})
    
    def test_resume_upload_error_contract(self, client):
        """Test that the resume upload error response matches the contract."""
        # Invalid file type
        response = client.post(
            "/api/resumes/upload",
            files={"resume": ("invalid.xyz", b"invalid content", "application/octet-stream")}
        )
        
        assert response.status_code == 400
        
        # Validate error response against contract
        try:
            ErrorResponse(**response.json())
        except ValidationError as e:
            pytest.fail(f"Resume upload error response does not match contract: {e}")


class TestTaskStatusContract:
    """Test the task status endpoint contract."""
    
    def test_task_status_response_contract(self, client, test_task_id, mock_resume_service):
        """Test that the task status response matches the contract."""
        response = client.get(f"/api/resumes/{test_task_id}")
        
        assert response.status_code == 200
        
        # Validate response against contract
        try:
            TaskStatusResponse(**response.json())
        except ValidationError as e:
            pytest.fail(f"Task status response does not match contract: {e}")
    
    def test_task_status_response_structure(self, client, test_task_id, mock_resume_service):
        """Test that the task status response has all required fields."""
        response = client.get(f"/api/resumes/{test_task_id}")
        data = response.json()
        
        # Check required fields
        assert "task_id" in data
        assert "status" in data
        assert "progress" in data
        
        # Optional fields may be present
        if data["status"] == "completed":
            assert "result_url" in data
        
        # Ensure no extra fields
        with pytest.raises(ValidationError):
            TaskStatusResponse(**{**data, "extra_field": "should not be allowed"})


class TestResumeTextContract:
    """Test the resume text endpoint contract."""
    
    def test_resume_text_response_contract(self, client, test_task_id, mock_resume_service):
        """Test that the resume text response matches the contract."""
        response = client.get(f"/api/resumes/{test_task_id}/text")
        
        assert response.status_code == 200
        
        # Validate response against contract
        try:
            # The actual response is a dictionary with the required fields plus possibly other metadata
            ResumeTextResponse(**response.json())
        except ValidationError as e:
            pytest.fail(f"Resume text response does not match contract: {e}")
    
    def test_resume_text_response_structure(self, client, test_task_id, mock_resume_service):
        """Test that the resume text response has all required fields."""
        response = client.get(f"/api/resumes/{test_task_id}/text")
        data = response.json()
        
        # Check required fields
        assert "task_id" in data
        assert "text" in data
        assert "metadata" in data


class TestCustomizationContract:
    """Test the customization endpoints contract."""
    
    def test_customization_request_validation(self, test_task_id, test_job_description):
        """Test that the customization request model validates correctly."""
        from tests.contract.api_contracts import CustomizationRequest
        
        # Valid request
        valid_request = {
            "resume_id": test_task_id,
            "job_description": test_job_description,
            "customize_level": "standard"
        }
        
        try:
            CustomizationRequest(**valid_request)
        except ValidationError as e:
            pytest.fail(f"Valid customization request failed validation: {e}")
        
        # Invalid request (empty job description)
        invalid_request = {
            "resume_id": test_task_id,
            "job_description": "",
            "customize_level": "standard"
        }
        
        with pytest.raises(ValidationError):
            CustomizationRequest(**invalid_request)
        
        # Invalid request (unknown customize level should still be accepted)
        unusual_level_request = {
            "resume_id": test_task_id,
            "job_description": test_job_description,
            "customize_level": "ultra"  # Non-standard level
        }
        
        try:
            CustomizationRequest(**unusual_level_request)
        except ValidationError as e:
            pytest.fail(f"Customization request with unusual level failed validation: {e}")
    
    def test_customization_response_contract(self, client, test_customization_request, mock_resume_service):
        """Test that the customization response matches the contract."""
        response = client.post(
            "/api/resumes/customize",
            json=test_customization_request
        )
        
        assert response.status_code == 200
        
        # Validate response against contract
        try:
            CustomizationResponse(**response.json())
        except ValidationError as e:
            pytest.fail(f"Customization response does not match contract: {e}")
    
    def test_customization_status_contract(self, client, test_task_id, mock_task_service):
        """Test that the customization status response matches the contract."""
        response = client.get(f"/api/resumes/customization/{test_task_id}")
        
        assert response.status_code == 200
        
        # Validate response against contract
        try:
            TaskStatusResponse(**response.json())
        except ValidationError as e:
            pytest.fail(f"Customization status response does not match contract: {e}")
    
    def test_customization_result_contract(self, client, test_task_id, mock_resume_service):
        """Test that the customization result response matches the contract."""
        response = client.get(f"/api/resumes/customization/{test_task_id}/result")
        
        assert response.status_code == 200
        
        # Validate response against contract
        try:
            CustomizationResultResponse(**response.json())
        except ValidationError as e:
            pytest.fail(f"Customization result response does not match contract: {e}")


class TestErrorResponseContract:
    """Test error response contracts."""
    
    def test_not_found_error_contract(self, client):
        """Test that a 404 response matches the error contract."""
        response = client.get("/api/resumes/nonexistent-task-id")
        
        assert response.status_code == 404
        
        # Validate error response against contract
        try:
            ErrorResponse(**response.json())
        except ValidationError as e:
            pytest.fail(f"Not found error response does not match contract: {e}")
    
    def test_bad_request_error_contract(self, client, mock_resume_service):
        """Test that a 400 response matches the error contract."""
        # Configure mock
        mock_resume_service.resume_exists.return_value = True
        
        response = client.post(
            "/api/resumes/customize",
            json={
                "resume_id": "valid-task-id",
                "job_description": "",  # Empty job description should trigger 400
                "customize_level": "standard"
            }
        )
        
        assert response.status_code == 400
        
        # Validate error response against contract
        try:
            ErrorResponse(**response.json())
        except ValidationError as e:
            pytest.fail(f"Bad request error response does not match contract: {e}")


class TestBackwardCompatibility:
    """Test backward compatibility of the API responses."""
    
    def test_resume_upload_backward_compatibility(self, client, test_pdf_path, mock_resume_service):
        """Test that the resume upload response is backward compatible with older clients."""
        # Old client expected format
        old_client_format = {
            "task_id": "any-task-id",
            "filename": "resume.pdf",
            "status": "processing"
        }
        
        # Current response
        with open(test_pdf_path, "rb") as pdf_file:
            response = client.post(
                "/api/resumes/upload",
                files={"resume": ("test_resume.pdf", pdf_file, "application/pdf")}
            )
        
        current_format = response.json()
        
        # Check that all fields from old format exist in current response
        for key in old_client_format:
            assert key in current_format
    
    def test_task_status_backward_compatibility(self, client, test_task_id, mock_resume_service):
        """Test that the task status response is backward compatible with older clients."""
        # Old client expected format
        old_client_format = {
            "task_id": "any-task-id",
            "status": "processing",
            "progress": 50.0
        }
        
        # Current response
        response = client.get(f"/api/resumes/{test_task_id}")
        current_format = response.json()
        
        # Check that all fields from old format exist in current response
        for key in old_client_format:
            assert key in current_format
    
    def test_customization_backward_compatibility(self, client, test_customization_request, mock_resume_service):
        """Test that the customization response is backward compatible with older clients."""
        # Old client expected format
        old_client_format = {
            "task_id": "any-task-id",
            "status": "processing"
        }
        
        # Current response
        response = client.post(
            "/api/resumes/customize",
            json=test_customization_request
        )
        current_format = response.json()
        
        # Check that all fields from old format exist in current response
        for key in old_client_format:
            assert key in current_format
