"""Unit tests for the resume service."""
import pytest
import uuid
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.resume_service import ResumeService
from app.core.exceptions import DocumentProcessingError, ResumeNotFoundError


@pytest.mark.asyncio
async def test_process_resume(document_processor, storage_service, mock_task_id, sample_pdf_content):
    """Test processing a resume."""
    # Setup
    resume_service = ResumeService(document_processor, storage_service)
    filename = "test_resume.pdf"
    
    # Mock document processor's extract_text_from_bytes method
    expected_text = "This is extracted test resume content"
    
    with patch.object(
        document_processor,
        'extract_text_from_bytes',
        return_value=expected_text
    ) as mock_extract:
        # Process resume
        result = await resume_service.process_resume(
            file_content=sample_pdf_content,
            filename=filename,
            task_id=mock_task_id
        )
        
        # Assertions
        assert result["task_id"] == mock_task_id
        assert result["filename"] == filename
        assert result["text"] == expected_text
        assert result["status"] == "completed"
        
        # Verify mocks were called
        mock_extract.assert_called_once_with(
            sample_pdf_content, filename=filename
        )


@pytest.mark.asyncio
async def test_process_resume_extraction_error(document_processor, storage_service, mock_task_id, sample_pdf_content):
    """Test error handling when processing a resume fails."""
    # Setup
    resume_service = ResumeService(document_processor, storage_service)
    filename = "test_resume.pdf"
    
    # Mock document processor to raise an error
    error_message = "Extraction failed"
    
    with patch.object(
        document_processor,
        'extract_text_from_bytes',
        side_effect=DocumentProcessingError(detail=error_message)
    ) as mock_extract:
        # Process resume should raise error
        with pytest.raises(DocumentProcessingError) as excinfo:
            await resume_service.process_resume(
                file_content=sample_pdf_content,
                filename=filename,
                task_id=mock_task_id
            )
        
        # Verify error message
        assert error_message in str(excinfo.value)
        
        # Verify mocks were called
        mock_extract.assert_called_once()
        
        # Verify metadata was updated with error
        metadata = await storage_service.get_metadata(mock_task_id)
        assert metadata["status"] == "failed"
        assert error_message in metadata.get("error", "")


@pytest.mark.asyncio
async def test_resume_exists(storage_service, temp_uploads_dir):
    """Test checking if a resume exists."""
    # Setup
    resume_service = ResumeService(None, storage_service)
    task_id = str(uuid.uuid4())
    
    # Create a test resume directory and files
    task_dir = temp_uploads_dir / task_id
    task_dir.mkdir(exist_ok=True)
    
    # Create metadata and original file
    with open(task_dir / "metadata.json", "w") as f:
        f.write('{"status": "completed"}')
    
    with open(task_dir / "original.pdf", "wb") as f:
        f.write(b"test content")
    
    # Check if resume exists
    exists = await resume_service.resume_exists(task_id)
    assert exists is True
    
    # Check for non-existent resume
    non_existent = await resume_service.resume_exists(str(uuid.uuid4()))
    assert non_existent is False


@pytest.mark.asyncio
async def test_get_resume_data(storage_service, temp_uploads_dir):
    """Test getting resume data."""
    # Setup
    resume_service = ResumeService(None, storage_service)
    task_id = str(uuid.uuid4())
    
    # Create a test resume directory and files
    task_dir = temp_uploads_dir / task_id
    task_dir.mkdir(exist_ok=True)
    
    # Create metadata file
    metadata = {
        "status": "completed",
        "file_size": 12345,
        "processing_time_ms": 500
    }
    
    with open(task_dir / "metadata.json", "w") as f:
        import json
        json.dump(metadata, f)
    
    # Create extracted text file
    extracted_text = "This is the extracted text from the resume"
    with open(task_dir / "extracted.txt", "w") as f:
        f.write(extracted_text)
    
    # Create original file
    with open(task_dir / "original.pdf", "wb") as f:
        f.write(b"test content")
    
    # Get resume data
    resume_data = await resume_service.get_resume_data(task_id)
    
    # Verify response
    assert resume_data["task_id"] == task_id
    assert resume_data["text"] == extracted_text
    assert resume_data["metadata"] == metadata
    assert resume_data["status"] == "completed"


@pytest.mark.asyncio
async def test_get_resume_data_not_found(storage_service):
    """Test getting resume data for a non-existent resume."""
    # Setup
    resume_service = ResumeService(None, storage_service)
    task_id = str(uuid.uuid4())
    
    # Get non-existent resume data
    resume_data = await resume_service.get_resume_data(task_id)
    
    # Verify response is None
    assert resume_data is None


@pytest.mark.asyncio
async def test_customize_resume(storage_service, temp_uploads_dir):
    """Test customizing a resume."""
    # Setup
    resume_service = ResumeService(None, storage_service)
    resume_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    job_description = "This is a test job description"
    
    # Create a test resume directory and files
    resume_dir = temp_uploads_dir / resume_id
    resume_dir.mkdir(exist_ok=True)
    
    # Create metadata and original file
    with open(resume_dir / "metadata.json", "w") as f:
        f.write('{"status": "completed"}')
    
    with open(resume_dir / "original.pdf", "wb") as f:
        f.write(b"test content")
    
    # Mock resume_exists to return True
    with patch.object(
        resume_service,
        'resume_exists',
        return_value=True
    ):
        # Call customize_resume
        result = await resume_service.customize_resume(
            resume_id=resume_id,
            job_description=job_description,
            task_id=task_id
        )
        
        # Verify response
        assert result == task_id
        
        # Verify metadata was created
        metadata = await storage_service.get_metadata(task_id)
        assert metadata["status"] == "processing"
        assert metadata["resume_id"] == resume_id
        assert metadata["customization_type"] == "job_description"


@pytest.mark.asyncio
async def test_customize_resume_not_found(storage_service):
    """Test error handling when customizing a non-existent resume."""
    # Setup
    resume_service = ResumeService(None, storage_service)
    resume_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    job_description = "This is a test job description"
    
    # Mock resume_exists to return False
    with patch.object(
        resume_service,
        'resume_exists',
        return_value=False
    ):
        # Call customize_resume should raise error
        with pytest.raises(ResumeNotFoundError) as excinfo:
            await resume_service.customize_resume(
                resume_id=resume_id,
                job_description=job_description,
                task_id=task_id
            )
        
        # Verify error message
        assert resume_id in str(excinfo.value)
