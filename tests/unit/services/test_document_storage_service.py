"""Unit tests for the document storage service."""
import pytest
import os
import uuid
import json
from pathlib import Path

from app.services.document_storage_service import DocumentStorageService
from app.core.exceptions import DocumentProcessingError


@pytest.mark.asyncio
async def test_save_document(temp_uploads_dir, storage_service):
    """Test saving a document."""
    # Test data
    task_id = str(uuid.uuid4())
    content = b"Test content"
    filename = "test.pdf"
    
    # Save document
    file_path = await storage_service.save_document(content, task_id, filename)
    
    # Check file exists
    assert file_path.exists()
    assert file_path.name == "original.pdf"
    
    # Check metadata was created
    metadata_path = temp_uploads_dir / task_id / "metadata.json"
    assert metadata_path.exists()
    
    # Check file content
    with open(file_path, "rb") as f:
        saved_content = f.read()
        assert saved_content == content


@pytest.mark.asyncio
async def test_save_extracted_text(temp_uploads_dir, storage_service):
    """Test saving extracted text."""
    # Test data
    task_id = str(uuid.uuid4())
    text = "Extracted text from document"
    
    # Create task directory
    task_dir = temp_uploads_dir / task_id
    task_dir.mkdir(exist_ok=True)
    
    # Save text
    text_path = await storage_service.save_extracted_text(text, task_id)
    
    # Check file exists
    assert text_path.exists()
    assert text_path.name == "extracted.txt"
    
    # Check metadata was updated
    metadata_path = task_dir / "metadata.json"
    assert metadata_path.exists()
    
    # Check file content
    with open(text_path, "r", encoding="utf-8") as f:
        saved_text = f.read()
        assert saved_text == text


@pytest.mark.asyncio
async def test_save_metadata(temp_uploads_dir, storage_service):
    """Test saving metadata."""
    # Test data
    task_id = str(uuid.uuid4())
    metadata = {
        "status": "completed",
        "file_size": 12345,
        "processing_time_ms": 500
    }
    
    # Save metadata
    metadata_path = await storage_service.save_metadata(task_id, metadata)
    
    # Check file exists
    assert metadata_path.exists()
    
    # Check file content
    with open(metadata_path, "r", encoding="utf-8") as f:
        saved_metadata = json.load(f)
        assert saved_metadata == metadata


@pytest.mark.asyncio
async def test_get_metadata(temp_uploads_dir, storage_service):
    """Test getting metadata."""
    # Test data
    task_id = str(uuid.uuid4())
    metadata = {
        "status": "completed",
        "file_size": 12345,
        "processing_time_ms": 500
    }
    
    # Create task directory
    task_dir = temp_uploads_dir / task_id
    task_dir.mkdir(exist_ok=True)
    
    # Create metadata file
    metadata_path = task_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f)
    
    # Get metadata
    retrieved_metadata = await storage_service.get_metadata(task_id)
    
    # Check metadata
    assert retrieved_metadata == metadata


@pytest.mark.asyncio
async def test_get_metadata_nonexistent(storage_service):
    """Test getting metadata for a nonexistent task."""
    # Test data
    task_id = str(uuid.uuid4())
    
    # Get metadata
    retrieved_metadata = await storage_service.get_metadata(task_id)
    
    # Check metadata is empty
    assert retrieved_metadata == {}


@pytest.mark.asyncio
async def test_get_extracted_text(temp_uploads_dir, storage_service):
    """Test getting extracted text."""
    # Test data
    task_id = str(uuid.uuid4())
    text = "Extracted text from document"
    
    # Create task directory
    task_dir = temp_uploads_dir / task_id
    task_dir.mkdir(exist_ok=True)
    
    # Create text file
    text_path = task_dir / "extracted.txt"
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text)
    
    # Get text
    retrieved_text = await storage_service.get_extracted_text(task_id)
    
    # Check text
    assert retrieved_text == text


@pytest.mark.asyncio
async def test_get_extracted_text_nonexistent(storage_service):
    """Test getting extracted text for a nonexistent task."""
    # Test data
    task_id = str(uuid.uuid4())
    
    # Get text
    retrieved_text = await storage_service.get_extracted_text(task_id)
    
    # Check text is None
    assert retrieved_text is None


@pytest.mark.asyncio
async def test_get_original_document_path(temp_uploads_dir, storage_service):
    """Test getting the original document path."""
    # Test data
    task_id = str(uuid.uuid4())
    content = b"Test content"
    
    # Create task directory
    task_dir = temp_uploads_dir / task_id
    task_dir.mkdir(exist_ok=True)
    
    # Create document file
    file_path = task_dir / "original.pdf"
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Get path
    retrieved_path = await storage_service.get_original_document_path(task_id)
    
    # Check path
    assert retrieved_path == file_path


@pytest.mark.asyncio
async def test_get_original_document_path_nonexistent(storage_service):
    """Test getting the original document path for a nonexistent task."""
    # Test data
    task_id = str(uuid.uuid4())
    
    # Get path
    retrieved_path = await storage_service.get_original_document_path(task_id)
    
    # Check path is None
    assert retrieved_path is None


@pytest.mark.asyncio
async def test_list_tasks(temp_uploads_dir, storage_service):
    """Test listing tasks."""
    # Test data
    task_id1 = str(uuid.uuid4())
    task_id2 = str(uuid.uuid4())
    
    # Create task directories and metadata
    task_dir1 = temp_uploads_dir / task_id1
    task_dir1.mkdir(exist_ok=True)
    with open(task_dir1 / "metadata.json", "w", encoding="utf-8") as f:
        json.dump({"status": "completed", "task_type": "pdf"}, f)
    
    task_dir2 = temp_uploads_dir / task_id2
    task_dir2.mkdir(exist_ok=True)
    with open(task_dir2 / "metadata.json", "w", encoding="utf-8") as f:
        json.dump({"status": "processing", "task_type": "docx"}, f)
    
    # List tasks
    tasks = await storage_service.list_tasks()
    
    # Check tasks
    assert len(tasks) == 2
    task_ids = [task["task_id"] for task in tasks]
    assert task_id1 in task_ids
    assert task_id2 in task_ids
