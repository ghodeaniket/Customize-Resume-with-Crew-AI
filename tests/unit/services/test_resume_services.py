"""Tests for the refactored resume services."""
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from app.core.exceptions import DocumentProcessingError, ResumeNotFoundError, CustomizationError
from app.services.resume.storage_service import ResumeStorageService
from app.services.resume.extraction_service import ResumeExtractionService
from app.services.resume.customization_service import ResumeCustomizationService
from app.services.resume.service import ResumeService


@pytest.fixture
def mock_document_repository():
    """Create a mock document repository."""
    mock_repo = AsyncMock()
    mock_repo.exists.return_value = True
    mock_repo.get_metadata.return_value = {"status": "completed"}
    mock_repo.get_extracted_text.return_value = "Test resume content"
    mock_repo.save_document.return_value = Path("/test/path/document.pdf")
    mock_repo.save_extracted_text.return_value = Path("/test/path/extracted.txt")
    mock_repo.save_metadata.return_value = Path("/test/path/metadata.json")
    mock_repo.get_result.return_value = "Optimized resume content"
    return mock_repo


@pytest.fixture
def mock_task_repository():
    """Create a mock task repository."""
    mock_repo = AsyncMock()
    mock_repo.get_task.return_value = {
        "task_id": "test-task-id",
        "status": "completed",
        "progress": 100.0
    }
    mock_repo.update_task.return_value = {
        "task_id": "test-task-id",
        "status": "processing",
        "progress": 10.0
    }
    return mock_repo


@pytest.fixture
def mock_document_processor():
    """Create a mock document processor."""
    mock_processor = AsyncMock()
    mock_processor.extract_text_from_bytes.return_value = "Test resume content"
    return mock_processor


@pytest.fixture
def storage_service(mock_document_repository):
    """Create a storage service with mock repository."""
    return ResumeStorageService(document_repository=mock_document_repository)


@pytest.fixture
def extraction_service(mock_document_processor, storage_service):
    """Create an extraction service with mock dependencies."""
    return ResumeExtractionService(
        document_processor=mock_document_processor,
        storage_service=storage_service
    )


@pytest.fixture
def customization_service(extraction_service, storage_service, mock_task_repository):
    """Create a customization service with mock dependencies."""
    service = ResumeCustomizationService(
        extraction_service=extraction_service,
        storage_service=storage_service,
        task_repository=mock_task_repository
    )
    
    # Mock internal methods to avoid CrewAI dependencies
    service._setup_llm_environment = MagicMock()
    service._create_llm = MagicMock()
    service._create_tools = AsyncMock(return_value=[])
    service._create_agents = AsyncMock(return_value={"analyzer": MagicMock(), "optimizer": MagicMock()})
    service._run_job_analysis = AsyncMock(return_value="Job analysis result")
    service._run_resume_optimization = AsyncMock(return_value="Optimized resume content")
    
    return service


@pytest.fixture
def resume_service(storage_service, extraction_service, customization_service):
    """Create a resume service with mock dependencies."""
    return ResumeService(
        storage_service=storage_service,
        extraction_service=extraction_service,
        customization_service=customization_service
    )


@pytest.mark.asyncio
async def test_storage_service_exists(storage_service, mock_document_repository):
    """Test that storage service correctly checks if a resume exists."""
    # Given
    mock_document_repository.exists.return_value = True
    
    # When
    result = await storage_service.exists("test-id")
    
    # Then
    assert result is True
    mock_document_repository.exists.assert_called_once_with("test-id")


@pytest.mark.asyncio
async def test_storage_service_get_extracted_text(storage_service, mock_document_repository):
    """Test that storage service correctly gets extracted text."""
    # Given
    expected_text = "Test resume content"
    mock_document_repository.get_extracted_text.return_value = expected_text
    
    # When
    result = await storage_service.get_extracted_text("test-id")
    
    # Then
    assert result == expected_text
    mock_document_repository.get_extracted_text.assert_called_once_with("test-id")


@pytest.mark.asyncio
async def test_extraction_service_process_resume(extraction_service, mock_document_processor, storage_service):
    """Test that extraction service correctly processes a resume."""
    # Given
    file_content = b"Test PDF content"
    filename = "test.pdf"
    task_id = "test-task-id"
    
    # When
    result = await extraction_service.process_resume(file_content, filename, task_id)
    
    # Then
    assert result["task_id"] == task_id
    assert result["filename"] == filename
    assert result["text"] == "Test resume content"
    assert result["status"] == "completed"
    
    # Verify interactions
    mock_document_processor.extract_text_from_bytes.assert_called_once()
    assert await storage_service.storage_service.save_document.call_count >= 1
    assert await storage_service.storage_service.save_extracted_text.call_count >= 1
    assert await storage_service.storage_service.save_metadata.call_count >= 1


@pytest.mark.asyncio
async def test_customization_service_customize_resume(
    customization_service, extraction_service, storage_service, mock_task_repository
):
    """Test that customization service correctly customizes a resume."""
    # Given
    resume_id = "test-resume-id"
    job_description = "Test job description"
    task_id = "test-task-id"
    customize_level = "standard"
    
    # Mock extraction service to return resume data
    extraction_service.get_by_id = AsyncMock(return_value={
        "task_id": resume_id,
        "text": "Test resume content",
        "status": "completed"
    })
    
    # When
    result = await customization_service.customize_resume(
        resume_id=resume_id,
        job_description=job_description,
        task_id=task_id,
        customize_level=customize_level
    )
    
    # Then
    assert result == task_id
    
    # Verify interactions
    extraction_service.get_by_id.assert_called_once_with(resume_id)
    assert mock_task_repository.update_task.call_count >= 2
    assert storage_service.save_result.call_count >= 1


@pytest.mark.asyncio
async def test_resume_service_process_resume(resume_service, extraction_service):
    """Test that main resume service correctly delegates to extraction service."""
    # Given
    file_content = b"Test PDF content"
    filename = "test.pdf"
    task_id = "test-task-id"
    
    # Mock extraction service
    extraction_service.process_resume = AsyncMock(return_value={
        "task_id": task_id,
        "filename": filename,
        "text": "Test resume content",
        "status": "completed"
    })
    
    # When
    result = await resume_service.process_resume(file_content, filename, task_id)
    
    # Then
    assert result["task_id"] == task_id
    assert result["filename"] == filename
    assert result["text"] == "Test resume content"
    assert result["status"] == "completed"
    
    # Verify delegation
    extraction_service.process_resume.assert_called_once_with(
        file_content=file_content,
        filename=filename,
        task_id=task_id
    )


@pytest.mark.asyncio
async def test_resume_service_customize_resume(resume_service, customization_service):
    """Test that main resume service correctly delegates to customization service."""
    # Given
    resume_id = "test-resume-id"
    job_description = "Test job description"
    task_id = "test-task-id"
    customize_level = "standard"
    
    # Mock customization service
    customization_service.customize_resume = AsyncMock(return_value=task_id)
    
    # When
    result = await resume_service.customize_resume(
        resume_id=resume_id,
        job_description=job_description,
        task_id=task_id,
        customize_level=customize_level
    )
    
    # Then
    assert result == task_id
    
    # Verify delegation
    customization_service.customize_resume.assert_called_once_with(
        resume_id=resume_id,
        job_description=job_description,
        task_id=task_id,
        customize_level=customize_level
    )


@pytest.mark.asyncio
async def test_error_handling_extraction(extraction_service, mock_document_processor, storage_service):
    """Test error handling in extraction service."""
    # Given
    file_content = b"Test PDF content"
    filename = "test.pdf"
    task_id = "test-task-id"
    
    # Mock error in document processor
    mock_document_processor.extract_text_from_bytes.side_effect = Exception("Test error")
    
    # When/Then
    with pytest.raises(DocumentProcessingError):
        await extraction_service.process_resume(file_content, filename, task_id)
    
    # Verify error metadata was saved
    assert storage_service.save_metadata.call_count >= 1
    last_call = storage_service.save_metadata.call_args
    assert "failed" in last_call[1]["metadata"]["status"]


@pytest.mark.asyncio
async def test_error_handling_customization(customization_service, extraction_service):
    """Test error handling in customization service."""
    # Given
    resume_id = "test-resume-id"
    job_description = "Test job description"
    task_id = "test-task-id"
    
    # Mock extraction service to return no resume
    extraction_service.exists = AsyncMock(return_value=False)
    
    # When/Then
    with pytest.raises(ResumeNotFoundError):
        await customization_service.customize_resume(
            resume_id=resume_id,
            job_description=job_description,
            task_id=task_id
        )
