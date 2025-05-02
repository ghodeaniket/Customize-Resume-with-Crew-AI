"""File system repository implementations for document and task access."""
import os
import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, BinaryIO

import aiofiles
from fastapi import UploadFile

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError
from app.repositories.document_repository import DocumentRepository
from app.repositories.task_repository import TaskRepository


class FileSystemDocumentRepository(DocumentRepository):
    """File system implementation of the document repository.
    
    This implementation stores documents, extracted text, metadata,
    and results as files in the file system.
    """
    
    def __init__(self, base_path: str = settings.UPLOADS_DIR):
        """Initialize file system document repository.
        
        Args:
            base_path: Base directory for storing documents
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized file system document repository at {self.base_path}")
    
    async def save(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Save a document entity.
        
        Args:
            entity: Document entity to save
            
        Returns:
            Dict[str, Any]: Saved document entity
        """
        task_id = entity.get("task_id")
        if not task_id:
            task_id = str(uuid.uuid4())
            entity["task_id"] = task_id
        
        # Save metadata
        await self.save_metadata(task_id, entity)
        
        return entity
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Find a document by ID.
        
        Args:
            id: Document ID
            
        Returns:
            Optional[Dict[str, Any]]: Document if found, None otherwise
        """
        metadata = await self.get_metadata(id)
        if not metadata:
            return None
        
        # Add extracted text if available
        extracted_text = await self.get_extracted_text(id)
        if extracted_text:
            metadata["text"] = extracted_text
        
        return metadata
    
    async def find_all(self) -> List[Dict[str, Any]]:
        """Find all documents.
        
        Returns:
            List[Dict[str, Any]]: List of all documents
        """
        return await self.list_documents()
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a document by ID.
        
        Args:
            id: Document ID
            data: Data to update
            
        Returns:
            Optional[Dict[str, Any]]: Updated document if found, None otherwise
        """
        metadata = await self.get_metadata(id)
        if not metadata:
            return None
        
        # Update metadata
        metadata.update(data)
        await self.save_metadata(id, metadata)
        
        return metadata
    
    async def delete(self, id: str) -> bool:
        """Delete a document by ID.
        
        Args:
            id: Document ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        task_dir = self.base_path / id
        if not task_dir.exists():
            return False
        
        # Delete all files in the directory
        for file in task_dir.iterdir():
            file.unlink()
        
        # Delete the directory
        task_dir.rmdir()
        
        return True
    
    async def exists(self, id: str) -> bool:
        """Check if a document exists by ID.
        
        Args:
            id: Document ID
            
        Returns:
            bool: True if exists, False otherwise
        """
        task_dir = self.base_path / id
        return task_dir.exists()
    
    async def save_document(
        self, content: bytes, task_id: str, original_filename: str
    ) -> Path:
        """Save document content to disk with a unique ID.
        
        Args:
            content: Document content bytes
            task_id: Unique task identifier
            original_filename: Original filename
            
        Returns:
            Path: Path to the saved document
            
        Raises:
            DocumentProcessingError: If saving fails
        """
        # Create directory for this task
        task_dir = self.base_path / task_id
        task_dir.mkdir(exist_ok=True)
        
        # Get file extension
        ext = Path(original_filename).suffix.lower() if original_filename else ""
        
        # Save original file
        file_path = task_dir / f"original{ext}"
        
        try:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
            
            # Save metadata
            await self.save_metadata(task_id, {
                "original_filename": original_filename,
                "file_size": len(content),
                "file_extension": ext
            })
            
            logger.info(f"Saved document to {file_path}, size: {len(content)} bytes")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Error saving document: {str(e)}")
    
    async def save_extracted_text(self, text: str, task_id: str) -> Path:
        """Save extracted text to disk.
        
        Args:
            text: Extracted text content
            task_id: Task identifier
            
        Returns:
            Path: Path to the saved text file
            
        Raises:
            DocumentProcessingError: If saving fails
        """
        task_dir = self.base_path / task_id
        task_dir.mkdir(exist_ok=True)
        
        text_path = task_dir / "extracted.txt"
        
        try:
            async with aiofiles.open(text_path, "w", encoding="utf-8") as f:
                await f.write(text)
            
            # Update metadata
            metadata = await self.get_metadata(task_id)
            metadata.update({
                "extracted_text_path": str(text_path),
                "extracted_text_size": len(text)
            })
            await self.save_metadata(task_id, metadata)
            
            logger.info(f"Saved extracted text to {text_path}, size: {len(text)} characters")
            return text_path
            
        except Exception as e:
            logger.error(f"Error saving extracted text: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Error saving extracted text: {str(e)}")
    
    async def save_metadata(self, task_id: str, metadata: Dict[str, Any]) -> Path:
        """Save metadata for a task.
        
        Args:
            task_id: Task identifier
            metadata: Metadata dictionary
            
        Returns:
            Path: Path to the metadata file
        """
        task_dir = self.base_path / task_id
        task_dir.mkdir(exist_ok=True)
        
        metadata_path = task_dir / "metadata.json"
        
        # Load existing metadata if it exists
        existing_metadata = {}
        if metadata_path.exists():
            try:
                async with aiofiles.open(metadata_path, "r", encoding="utf-8") as f:
                    content = await f.read()
                    existing_metadata = json.loads(content)
            except Exception as e:
                logger.warning(f"Error reading existing metadata: {str(e)}")
        
        # Update with new metadata
        existing_metadata.update(metadata)
        
        # Write updated metadata
        try:
            async with aiofiles.open(metadata_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(existing_metadata, indent=2))
            
            logger.debug(f"Saved metadata to {metadata_path}")
            return metadata_path
            
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Error saving metadata: {str(e)}")
    
    async def get_metadata(self, task_id: str) -> Dict[str, Any]:
        """Get metadata for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Dict: Metadata dictionary
            
        Raises:
            DocumentProcessingError: If metadata doesn't exist or can't be read
        """
        metadata_path = self.base_path / task_id / "metadata.json"
        
        if not metadata_path.exists():
            logger.warning(f"Metadata file does not exist: {metadata_path}")
            return {}
        
        try:
            async with aiofiles.open(metadata_path, "r", encoding="utf-8") as f:
                content = await f.read()
                return json.loads(content)
                
        except Exception as e:
            logger.error(f"Error reading metadata: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Error reading metadata: {str(e)}")
    
    async def get_extracted_text(self, task_id: str) -> Optional[str]:
        """Get extracted text for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[str]: Extracted text if available
        """
        text_path = self.base_path / task_id / "extracted.txt"
        
        if not text_path.exists():
            logger.warning(f"Extracted text file does not exist: {text_path}")
            return None
        
        try:
            async with aiofiles.open(text_path, "r", encoding="utf-8") as f:
                return await f.read()
                
        except Exception as e:
            logger.error(f"Error reading extracted text: {str(e)}", exc_info=True)
            return None
    
    async def get_original_document_path(self, task_id: str) -> Optional[Path]:
        """Get the path to the original document.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Path]: Path to the original document if available
        """
        task_dir = self.base_path / task_id
        
        if not task_dir.exists():
            logger.warning(f"Task directory does not exist: {task_dir}")
            return None
        
        # Try to find the original file
        for file in task_dir.iterdir():
            if file.name.startswith("original"):
                return file
        
        logger.warning(f"Original document not found in task directory: {task_dir}")
        return None
    
    async def save_result(self, task_id: str, result: str) -> Path:
        """Save task result to disk.
        
        Args:
            task_id: Task identifier
            result: Task result content
            
        Returns:
            Path: Path to the saved result file
            
        Raises:
            DocumentProcessingError: If saving fails
        """
        task_dir = self.base_path / task_id
        task_dir.mkdir(exist_ok=True)
        
        result_path = task_dir / "result.txt"
        
        try:
            async with aiofiles.open(result_path, "w", encoding="utf-8") as f:
                await f.write(result)
            
            # Update metadata
            metadata = await self.get_metadata(task_id)
            metadata.update({
                "result_path": str(result_path),
                "result_size": len(result),
                "result_created_at": time.time()
            })
            await self.save_metadata(task_id, metadata)
            
            logger.info(f"Saved task result to {result_path}, size: {len(result)} characters")
            return result_path
            
        except Exception as e:
            logger.error(f"Error saving task result: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Error saving task result: {str(e)}")
    
    async def get_result(self, task_id: str) -> Optional[str]:
        """Get task result for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[str]: Task result if available
        """
        result_path = self.base_path / task_id / "result.txt"
        
        if not result_path.exists():
            logger.warning(f"Result file does not exist: {result_path}")
            return None
        
        try:
            async with aiofiles.open(result_path, "r", encoding="utf-8") as f:
                return await f.read()
                
        except Exception as e:
            logger.error(f"Error reading task result: {str(e)}", exc_info=True)
            return None
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents with their metadata.
        
        Returns:
            List[Dict]: List of documents with metadata
        """
        documents = []
        
        for task_dir in self.base_path.iterdir():
            if not task_dir.is_dir():
                continue
            
            metadata_path = task_dir / "metadata.json"
            if metadata_path.exists():
                try:
                    async with aiofiles.open(metadata_path, "r", encoding="utf-8") as f:
                        content = await f.read()
                        metadata = json.loads(content)
                        documents.append({
                            "task_id": task_dir.name,
                            **metadata
                        })
                except Exception as e:
                    logger.warning(f"Error reading metadata for task {task_dir.name}: {str(e)}")
        
        return documents


class FileSystemTaskRepository(TaskRepository):
    """File system implementation of the task repository.
    
    This implementation uses the document repository for storage
    but provides task-specific operations and interfaces.
    """
    
    def __init__(self, document_repository: FileSystemDocumentRepository):
        """Initialize file system task repository.
        
        Args:
            document_repository: Document repository for storage
        """
        self.document_repository = document_repository
        logger.info("Initialized file system task repository")
    
    async def save(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Save a task entity.
        
        Args:
            entity: Task entity to save
            
        Returns:
            Dict[str, Any]: Saved task entity
        """
        task_id = entity.get("task_id")
        if not task_id:
            task_id = str(uuid.uuid4())
            entity["task_id"] = task_id
        
        # Save metadata
        await self.document_repository.save_metadata(task_id, entity)
        
        return entity
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Find a task by ID.
        
        Args:
            id: Task ID
            
        Returns:
            Optional[Dict[str, Any]]: Task if found, None otherwise
        """
        return await self.document_repository.get_metadata(id)
    
    async def find_all(self) -> List[Dict[str, Any]]:
        """Find all tasks.
        
        Returns:
            List[Dict[str, Any]]: List of all tasks
        """
        return await self.document_repository.list_documents()
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a task by ID.
        
        Args:
            id: Task ID
            data: Data to update
            
        Returns:
            Optional[Dict[str, Any]]: Updated task if found, None otherwise
        """
        metadata = await self.document_repository.get_metadata(id)
        if not metadata:
            return None
        
        # Update metadata
        metadata.update(data)
        await self.document_repository.save_metadata(id, metadata)
        
        return metadata
    
    async def delete(self, id: str) -> bool:
        """Delete a task by ID.
        
        Args:
            id: Task ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        return await self.document_repository.delete(id)
    
    async def exists(self, id: str) -> bool:
        """Check if a task exists by ID.
        
        Args:
            id: Task ID
            
        Returns:
            bool: True if exists, False otherwise
        """
        return await self.document_repository.exists(id)
    
    async def create_task(
        self, task_type: str, related_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new task with initial status.
        
        Args:
            task_type: Type of task (e.g., 'resume_processing', 'customization')
            related_id: Optional ID of related task (e.g., resume ID for customization)
            
        Returns:
            Dict: Task data with generated ID
        """
        task_id = str(uuid.uuid4())
        timestamp = time.time()
        
        task_data = {
            "task_id": task_id,
            "type": task_type,
            "status": "created",
            "progress": 0.0,
            "related_id": related_id,
            "created_at": timestamp,
            "updated_at": timestamp
        }
        
        await self.document_repository.save_metadata(task_id, task_data)
        logger.info(f"Created task {task_id} of type {task_type}")
        
        return task_data
    
    async def update_task(
        self, task_id: str, status: str, progress: Optional[float] = None, **kwargs
    ) -> Dict[str, Any]:
        """Update task status and progress.
        
        Args:
            task_id: Task identifier
            status: New status value
            progress: Optional progress percentage (0-100)
            **kwargs: Additional metadata to update
            
        Returns:
            Dict: Updated task data
        """
        # Get existing metadata
        metadata = await self.document_repository.get_metadata(task_id)
        
        if not metadata:
            logger.warning(f"Task {task_id} not found for update")
            return {}
        
        # Update fields
        metadata["status"] = status
        metadata["updated_at"] = time.time()
        
        if progress is not None:
            metadata["progress"] = progress
        
        # Update additional fields
        metadata.update(kwargs)
        
        # Save updated metadata
        await self.document_repository.save_metadata(task_id, metadata)
        
        logger.info(
            f"Updated task {task_id}: status={status}, "
            f"progress={progress if progress is not None else metadata.get('progress', 'N/A')}"
        )
        
        return metadata
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task data by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict]: Task data if found
        """
        return await self.document_repository.get_metadata(task_id)
    
    async def list_tasks(
        self, task_type: Optional[str] = None, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filtering.
        
        Args:
            task_type: Optional task type filter
            status: Optional status filter
            
        Returns:
            List[Dict]: List of matching tasks
        """
        all_tasks = await self.document_repository.list_documents()
        
        # Apply filters
        filtered_tasks = all_tasks
        
        if task_type:
            filtered_tasks = [t for t in filtered_tasks if t.get("type") == task_type]
        
        if status:
            filtered_tasks = [t for t in filtered_tasks if t.get("status") == status]
        
        return filtered_tasks
    
    async def store_task_result(self, task_id: str, result: str) -> str:
        """Store the result of a completed task.
        
        Args:
            task_id: Task identifier
            result: Task result content
            
        Returns:
            str: Path to the stored result
        """
        # Store the result
        result_path = await self.document_repository.save_result(task_id, result)
        
        # Update task metadata
        await self.update_task(
            task_id=task_id,
            status="completed",
            progress=100.0,
            result_path=str(result_path)
        )
        
        logger.info(f"Stored result for task {task_id}")
        return str(result_path)
