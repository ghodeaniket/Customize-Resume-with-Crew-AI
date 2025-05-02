"""Unit tests for file system repository implementations."""
import os
import json
import uuid
import shutil
import tempfile
from pathlib import Path

import pytest
from aiofiles.threadpool.text import AsyncTextIOWrapper

from app.repositories.file_system_repository import FileSystemDocumentRepository, FileSystemTaskRepository


@pytest.fixture
def temp_base_path():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def document_repository(temp_base_path):
    """Create a document repository instance for testing."""
    return FileSystemDocumentRepository(base_path=temp_base_path)


@pytest.fixture
def task_repository(document_repository):
    """Create a task repository instance for testing."""
    return FileSystemTaskRepository(document_repository=document_repository)


@pytest.fixture
def test_task_id():
    """Generate a random task ID for testing."""
    return str(uuid.uuid4())


@pytest.fixture
def test_task_data(test_task_id):
    """Create test task data."""
    return {
        "task_id": test_task_id,
        "type": "test",
        "status": "created",
        "progress": 0.0,
        "created_at": 1630000000.0,
        "updated_at": 1630000000.0
    }


@pytest.mark.asyncio
async def test_document_repository_save_and_find(document_repository, test_task_id):
    """Test saving and finding a document."""
    # Arrange
    document_data = {
        "task_id": test_task_id,
        "filename": "test.txt",
        "content": "Test content"
    }
    
    # Act
    saved = await document_repository.save(document_data)
    found = await document_repository.find_by_id(test_task_id)
    
    # Assert
    assert saved["task_id"] == test_task_id
    assert found["task_id"] == test_task_id
    assert found["filename"] == "test.txt"


@pytest.mark.asyncio
async def test_document_repository_save_document(document_repository, test_task_id):
    """Test saving document content."""
    # Arrange
    content = b"Test document content"
    filename = "test.txt"
    
    # Act
    path = await document_repository.save_document(content, test_task_id, filename)
    
    # Assert
    assert path.exists()
    assert path.name == "original.txt"
    
    # Verify content
    with open(path, "rb") as f:
        saved_content = f.read()
    
    assert saved_content == content
    
    # Verify metadata
    metadata = await document_repository.get_metadata(test_task_id)
    assert metadata["original_filename"] == filename
    assert metadata["file_size"] == len(content)


@pytest.mark.asyncio
async def test_document_repository_save_extracted_text(document_repository, test_task_id):
    """Test saving extracted text."""
    # Arrange
    text = "Test extracted text"
    
    # Act
    path = await document_repository.save_extracted_text(text, test_task_id)
    
    # Assert
    assert path.exists()
    assert path.name == "extracted.txt"
    
    # Verify content
    with open(path, "r", encoding="utf-8") as f:
        saved_text = f.read()
    
    assert saved_text == text
    
    # Verify metadata
    metadata = await document_repository.get_metadata(test_task_id)
    assert metadata["extracted_text_path"] == str(path)
    assert metadata["extracted_text_size"] == len(text)


@pytest.mark.asyncio
async def test_document_repository_get_metadata(document_repository, test_task_id):
    """Test getting metadata."""
    # Arrange
    metadata = {
        "test_key": "test_value",
        "task_id": test_task_id
    }
    
    # Save metadata
    await document_repository.save_metadata(test_task_id, metadata)
    
    # Act
    retrieved = await document_repository.get_metadata(test_task_id)
    
    # Assert
    assert retrieved["test_key"] == "test_value"
    assert retrieved["task_id"] == test_task_id


@pytest.mark.asyncio
async def test_document_repository_update(document_repository, test_task_id):
    """Test updating a document."""
    # Arrange
    document_data = {
        "task_id": test_task_id,
        "status": "created"
    }
    
    # Save initial data
    await document_repository.save(document_data)
    
    # Act
    update_data = {
        "status": "completed",
        "new_field": "new_value"
    }
    updated = await document_repository.update(test_task_id, update_data)
    
    # Assert
    assert updated["status"] == "completed"
    assert updated["new_field"] == "new_value"
    assert updated["task_id"] == test_task_id


@pytest.mark.asyncio
async def test_document_repository_delete(document_repository, test_task_id):
    """Test deleting a document."""
    # Arrange
    document_data = {
        "task_id": test_task_id,
        "status": "created"
    }
    
    # Save initial data
    await document_repository.save(document_data)
    
    # Act
    deleted = await document_repository.delete(test_task_id)
    exists = await document_repository.exists(test_task_id)
    
    # Assert
    assert deleted is True
    assert exists is False


@pytest.mark.asyncio
async def test_task_repository_create_task(task_repository):
    """Test creating a task."""
    # Act
    task = await task_repository.create_task("test_type", "related_id_123")
    
    # Assert
    assert task["type"] == "test_type"
    assert task["related_id"] == "related_id_123"
    assert task["status"] == "created"
    assert task["progress"] == 0.0
    assert "task_id" in task
    assert "created_at" in task
    assert "updated_at" in task


@pytest.mark.asyncio
async def test_task_repository_update_task(task_repository, test_task_id, test_task_data):
    """Test updating a task."""
    # Arrange
    await task_repository.save(test_task_data)
    
    # Act
    updated = await task_repository.update_task(
        test_task_id, 
        status="processing", 
        progress=50.0,
        new_field="new_value"
    )
    
    # Assert
    assert updated["status"] == "processing"
    assert updated["progress"] == 50.0
    assert updated["new_field"] == "new_value"
    assert updated["task_id"] == test_task_id


@pytest.mark.asyncio
async def test_task_repository_get_task(task_repository, test_task_id, test_task_data):
    """Test getting a task."""
    # Arrange
    await task_repository.save(test_task_data)
    
    # Act
    task = await task_repository.get_task(test_task_id)
    
    # Assert
    assert task["task_id"] == test_task_id
    assert task["type"] == "test"
    assert task["status"] == "created"


@pytest.mark.asyncio
async def test_task_repository_list_tasks(task_repository):
    """Test listing tasks with filtering."""
    # Arrange
    tasks = [
        {
            "task_id": str(uuid.uuid4()),
            "type": "type_a",
            "status": "created"
        },
        {
            "task_id": str(uuid.uuid4()),
            "type": "type_a",
            "status": "processing"
        },
        {
            "task_id": str(uuid.uuid4()),
            "type": "type_b",
            "status": "created"
        }
    ]
    
    # Save tasks
    for task in tasks:
        await task_repository.save(task)
    
    # Act - Get all tasks
    all_tasks = await task_repository.list_tasks()
    
    # Act - Filter by type
    type_a_tasks = await task_repository.list_tasks(task_type="type_a")
    
    # Act - Filter by status
    created_tasks = await task_repository.list_tasks(status="created")
    
    # Act - Filter by type and status
    type_a_created_tasks = await task_repository.list_tasks(task_type="type_a", status="created")
    
    # Assert
    assert len(all_tasks) >= 3  # At least our 3 tasks
    assert len(type_a_tasks) == 2
    assert len(created_tasks) >= 2  # At least 2 tasks with status "created"
    assert len(type_a_created_tasks) == 1


@pytest.mark.asyncio
async def test_task_repository_store_task_result(task_repository, test_task_id, test_task_data, document_repository):
    """Test storing a task result."""
    # Arrange
    await task_repository.save(test_task_data)
    result = "Test result content"
    
    # Act
    result_path = await task_repository.store_task_result(test_task_id, result)
    
    # Assert
    # Check file exists
    assert Path(result_path).exists()
    
    # Check file content
    with open(result_path, "r", encoding="utf-8") as f:
        saved_result = f.read()
    
    assert saved_result == result
    
    # Check task status was updated
    task = await task_repository.get_task(test_task_id)
    assert task["status"] == "completed"
    assert task["progress"] == 100.0
    assert task["result_path"] == result_path
