"""
End-to-end integration tests for the complete Resume Customizer workflow.

These tests verify the full workflow from resume upload through customization,
validating all steps and data transitions.
"""
import pytest
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.services.resume_service import ResumeService
from app.services.task_service import TaskService


@pytest.mark.asyncio
async def test_complete_workflow_pdf(
    client, 
    test_pdf_path, 
    test_job_description,
    wait_for_task_completion,
    verify_task_success,
    assert_valid_response,
    mock_resume_service,
    mock_task_service,
    mock_crewai_agents
):
    """Test the complete workflow from PDF upload to customization."""
    # 1. Upload Resume
    with open(test_pdf_path, "rb") as pdf_file:
        response = client.post(
            "/api/resumes/upload",
            files={"resume": ("test_resume.pdf", pdf_file, "application/pdf")}
        )
    
    upload_data = assert_valid_response(
        response, 
        expected_status=200, 
        expected_fields=["task_id", "filename", "status"]
    )
    
    resume_task_id = upload_data["task_id"]
    assert upload_data["status"] == "processing", "Expected upload status to be 'processing'"
    
    # 2. Wait for Resume Processing
    # Mock the resuming processing to be completed immediately
    mock_resume_service.get_resume_data.return_value = {
        "text": "Sample resume text for testing",
        "metadata": {
            "status": "completed",
            "filename": "test_resume.pdf",
            "created_at": "2025-04-30T12:00:00Z",
            "updated_at": "2025-04-30T12:01:00Z"
        }
    }
    
    resume_status = await wait_for_task_completion(
        client, 
        "/api/resumes", 
        resume_task_id
    )
    
    assert resume_status["status"] == "completed", f"Resume processing failed: {resume_status}"
    
    # 3. Request Resume Text
    response = client.get(f"/api/resumes/{resume_task_id}/text")
    
    text_data = assert_valid_response(
        response, 
        expected_status=200, 
        expected_fields=["task_id", "text", "metadata"]
    )
    
    assert text_data["task_id"] == resume_task_id, "Task ID mismatch in resume text response"
    assert len(text_data["text"]) > 0, "Resume text is empty"
    
    # 4. Request Customization
    customization_request = {
        "resume_id": resume_task_id,
        "job_description": test_job_description,
        "customize_level": "standard"
    }
    
    response = client.post(
        "/api/resumes/customize",
        json=customization_request
    )
    
    customization_data = assert_valid_response(
        response, 
        expected_status=200, 
        expected_fields=["task_id", "status"]
    )
    
    customization_task_id = customization_data["task_id"]
    assert customization_data["status"] == "processing", "Expected customization status to be 'processing'"
    
    # 5. Wait for Customization
    # Mock the customization task to be completed immediately
    mock_task_service.get_task.return_value = {
        "task_id": customization_task_id,
        "status": "completed",
        "progress": 100.0,
        "created_at": "2025-04-30T12:00:00Z",
        "updated_at": "2025-04-30T12:01:00Z"
    }
    
    customization_status = await wait_for_task_completion(
        client, 
        "/api/resumes/customization", 
        customization_task_id
    )
    
    verify_task_success(customization_status)
    
    # 6. Get Customization Result
    mock_resume_service.get_customization_result.return_value = {
        "task_id": customization_task_id,
        "status": "completed",
        "result": "Customized resume text for testing",
        "metadata": {
            "processing_time_ms": 2500,
            "customize_level": "standard",
            "completion_time": 1719759382.45
        }
    }
    
    response = client.get(f"/api/resumes/customization/{customization_task_id}/result")
    
    result_data = assert_valid_response(
        response, 
        expected_status=200, 
        expected_fields=["task_id", "status", "result"]
    )
    
    assert result_data["task_id"] == customization_task_id, "Task ID mismatch in result response"
    assert result_data["status"] == "completed", "Expected result status to be 'completed'"
    assert len(result_data["result"]) > 0, "Result text is empty"
    
    # Verify that all the appropriate service methods were called
    mock_resume_service.get_resume_data.assert_called()
    mock_resume_service.customize_resume.assert_called()
    mock_resume_service.get_customization_result.assert_called()


@pytest.mark.asyncio
async def test_complete_workflow_docx(
    client, 
    test_docx_path, 
    test_job_description,
    wait_for_task_completion,
    verify_task_success,
    assert_valid_response,
    mock_resume_service,
    mock_task_service,
    mock_crewai_agents
):
    """Test the complete workflow from DOCX upload to customization."""
    # Similar to the PDF workflow test, but with DOCX file
    with open(test_docx_path, "rb") as docx_file:
        response = client.post(
            "/api/resumes/upload",
            files={"resume": ("test_resume.docx", docx_file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
    
    upload_data = assert_valid_response(
        response, 
        expected_status=200, 
        expected_fields=["task_id", "filename", "status"]
    )
    
    resume_task_id = upload_data["task_id"]
    assert upload_data["status"] == "processing", "Expected upload status to be 'processing'"
    
    # Mock the resuming processing to be completed immediately
    mock_resume_service.get_resume_data.return_value = {
        "text": "Sample resume text for testing from DOCX",
        "metadata": {
            "status": "completed",
            "filename": "test_resume.docx",
            "created_at": "2025-04-30T12:00:00Z",
            "updated_at": "2025-04-30T12:01:00Z"
        }
    }
    
    # Continue with the same flow as PDF test...
    resume_status = await wait_for_task_completion(
        client, 
        "/api/resumes", 
        resume_task_id
    )
    
    assert resume_status["status"] == "completed", f"Resume processing failed: {resume_status}"
    
    # Request customization with DOCX resume
    customization_request = {
        "resume_id": resume_task_id,
        "job_description": test_job_description,
        "customize_level": "standard"
    }
    
    response = client.post(
        "/api/resumes/customize",
        json=customization_request
    )
    
    customization_data = assert_valid_response(
        response, 
        expected_status=200, 
        expected_fields=["task_id", "status"]
    )
    
    customization_task_id = customization_data["task_id"]
    
    # Mock the customization task to be completed immediately
    mock_task_service.get_task.return_value = {
        "task_id": customization_task_id,
        "status": "completed",
        "progress": 100.0,
        "created_at": "2025-04-30T12:00:00Z",
        "updated_at": "2025-04-30T12:01:00Z"
    }
    
    mock_resume_service.get_customization_result.return_value = {
        "task_id": customization_task_id,
        "status": "completed",
        "result": "Customized resume text from DOCX for testing",
        "metadata": {
            "processing_time_ms": 2500,
            "customize_level": "standard",
            "completion_time": 1719759382.45
        }
    }
    
    # Complete the flow and verify results
    customization_status = await wait_for_task_completion(
        client, 
        "/api/resumes/customization", 
        customization_task_id
    )
    
    verify_task_success(customization_status)
    
    response = client.get(f"/api/resumes/customization/{customization_task_id}/result")
    
    result_data = assert_valid_response(
        response, 
        expected_status=200, 
        expected_fields=["task_id", "status", "result"]
    )
    
    assert result_data["task_id"] == customization_task_id
    assert result_data["status"] == "completed"
    assert "DOCX" in result_data["result"], "Result should contain 'DOCX' from the mocked response"


@pytest.mark.asyncio
async def test_error_handling_flow(
    client, 
    test_pdf_path,
    test_job_description,
    assert_valid_response,
    mock_resume_service,
    mock_task_service
):
    """Test error handling throughout the workflow."""
    # 1. Test invalid file type
    response = client.post(
        "/api/resumes/upload",
        files={"resume": ("invalid.xyz", b"invalid content", "application/octet-stream")}
    )
    
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
    
    # 2. Test empty resume file
    response = client.post(
        "/api/resumes/upload",
        files={"resume": ("empty.pdf", b"", "application/pdf")}
    )
    
    # Should fail with either 400 or 500 status
    assert response.status_code in (400, 500)
    
    # 3. Test resume not found error
    mock_resume_service.get_resume_data.return_value = None
    
    response = client.get("/api/resumes/nonexistent-task-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    
    # 4. Test empty job description error
    mock_resume_service.resume_exists.return_value = True
    
    response = client.post(
        "/api/resumes/customize",
        json={
            "resume_id": "valid-task-id",
            "job_description": "",
            "customize_level": "standard"
        }
    )
    
    assert response.status_code == 400
    assert "job description" in response.json()["detail"].lower()
    
    # 5. Test customization task not found
    mock_task_service.get_task.return_value = None
    
    response = client.get("/api/resumes/customization/nonexistent-task-id")
    assert response.status_code == 404
    
    # 6. Test customization result not ready
    mock_resume_service.get_customization_result.return_value = {
        "task_id": "incomplete-task-id",
        "status": "processing",
        "progress": 50.0
    }
    
    response = client.get("/api/resumes/customization/incomplete-task-id/result")
    assert response.status_code == 400
    assert "not complete" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_timeout_handling(
    client, 
    test_pdf_path, 
    test_job_description,
    wait_for_task_completion,
    mock_resume_service,
    mock_task_service
):
    """Test handling of timeout scenarios."""
    # Upload resume
    with open(test_pdf_path, "rb") as pdf_file:
        response = client.post(
            "/api/resumes/upload",
            files={"resume": ("test_resume.pdf", pdf_file, "application/pdf")}
        )
    
    resume_task_id = response.json()["task_id"]
    
    # Mock a task that never completes (status remains 'processing')
    mock_resume_service.get_resume_data.return_value = {
        "metadata": {
            "status": "processing",
            "progress": 50.0
        }
    }
    
    # Wait for task with a very short timeout
    with pytest.raises(TimeoutError):
        await wait_for_task_completion(
            client, 
            "/api/resumes", 
            resume_task_id,
            timeout=0.5,  # Very short timeout for testing
            interval=0.1
        )


@pytest.mark.asyncio
async def test_customization_with_different_levels(
    client, 
    test_pdf_path, 
    test_job_description,
    wait_for_task_completion,
    assert_valid_response,
    mock_resume_service,
    mock_task_service,
    mock_crewai_agents
):
    """Test customization with different levels (minimal, standard, comprehensive)."""
    # Upload resume first
    with open(test_pdf_path, "rb") as pdf_file:
        response = client.post(
            "/api/resumes/upload",
            files={"resume": ("test_resume.pdf", pdf_file, "application/pdf")}
        )
    
    resume_task_id = response.json()["task_id"]
    
    # Mock resume processing completed
    mock_resume_service.get_resume_data.return_value = {
        "text": "Sample resume text for testing",
        "metadata": {
            "status": "completed",
            "filename": "test_resume.pdf",
        }
    }
    
    # Mock customization task creation
    mock_task_service.create_task.return_value = {"task_id": "custom-task-id"}
    
    # Test minimal level
    response = client.post(
        "/api/resumes/customize",
        json={
            "resume_id": resume_task_id,
            "job_description": test_job_description,
            "customize_level": "minimal"
        }
    )
    
    assert response.status_code == 200
    minimal_task_id = response.json()["task_id"]
    
    # Test standard level (already tested in main flow)
    response = client.post(
        "/api/resumes/customize",
        json={
            "resume_id": resume_task_id,
            "job_description": test_job_description,
            "customize_level": "standard"
        }
    )
    
    assert response.status_code == 200
    standard_task_id = response.json()["task_id"]
    
    # Test comprehensive level
    response = client.post(
        "/api/resumes/customize",
        json={
            "resume_id": resume_task_id,
            "job_description": test_job_description,
            "customize_level": "comprehensive"
        }
    )
    
    assert response.status_code == 200
    comprehensive_task_id = response.json()["task_id"]
    
    # Verify that resume_service.customize_resume was called with different levels
    # Extract the customize_level from different calls
    customize_calls = [
        call[-1].get('customize_level') 
        for call in mock_resume_service.customize_resume.call_args_list
        if len(call) > 0 and isinstance(call[-1], dict) and 'customize_level' in call[-1]
    ]
    
    assert "minimal" in customize_calls, "No customization with 'minimal' level was called"
    assert "standard" in customize_calls, "No customization with 'standard' level was called"
    assert "comprehensive" in customize_calls, "No customization with 'comprehensive' level was called"
