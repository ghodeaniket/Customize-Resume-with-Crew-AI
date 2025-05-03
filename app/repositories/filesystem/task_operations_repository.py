"""Task operations repository for file system storage."""
import time
import uuid
from typing import Dict, Optional, Any

from app.core.logging import logger
from app.repositories.filesystem.base_repository import FileSystemBaseRepository
from app.repositories.filesystem.document_storage_repository import DocumentStorageRepository


class TaskOperationsRepository(FileSystemBaseRepository):
    """Repository for core task operations."""
    
    def __init__(self, base_path: str):
        """Initialize task operations repository.
        
        Args:
            base_path: Base directory for storage
        """
        super().__init__(base_path)
        self.storage_repository = DocumentStorageRepository(base_path)
        logger.info("Initialized task operations repository")
    
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
        
        await self.save_metadata(task_id, task_data)
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
        metadata = await self.get_metadata(task_id)
        
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
        await self.save_metadata(task_id, metadata)
        
        logger.info(
            f"Updated task {task_id}: status={status}, "
            f"progress={progress if progress is not None else metadata.get('progress', 'N/A')}"
        )
        
        return metadata
    
    async def store_task_result(self, task_id: str, result: str) -> str:
        """Store the result of a completed task.
        
        Args:
            task_id: Task identifier
            result: Task result content
            
        Returns:
            str: Path to the stored result
        """
        # Store the result
        result_path = await self.storage_repository.save_result(task_id, result)
        
        # Update task metadata
        await self.update_task(
            task_id=task_id,
            status="completed",
            progress=100.0,
            result_path=str(result_path)
        )
        
        logger.info(f"Stored result for task {task_id}")
        return str(result_path)
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task data by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict]: Task data if found
        """
        return await self.get_metadata(task_id)
