"""Service for task management and status tracking."""
import time
from typing import Dict, List, Optional, Any
from uuid import uuid4

from app.core.logging import logger
from app.services.document_storage_service import DocumentStorageService


class TaskService:
    """Service for managing and tracking task status."""
    
    def __init__(self, storage_service: DocumentStorageService):
        """Initialize the task service.
        
        Args:
            storage_service: Storage service for task data persistence
        """
        self.storage_service = storage_service
        logger.info("Initialized TaskService")
    
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
        task_id = str(uuid4())
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
        
        await self.storage_service.save_metadata(task_id, task_data)
        logger.info(f"Created task {task_id} of type {task_type}")
        
        return task_data
    
    async def update_task(
        self, task_id: str, status: str, progress: float = None, **kwargs
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
        metadata = await self.storage_service.get_metadata(task_id)
        
        if not metadata:
            logger.warning(f"Task {task_id} not found for update")
            return None
        
        # Update fields
        metadata["status"] = status
        metadata["updated_at"] = time.time()
        
        if progress is not None:
            metadata["progress"] = progress
        
        # Update additional fields
        metadata.update(kwargs)
        
        # Save updated metadata
        await self.storage_service.save_metadata(task_id, metadata)
        
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
        metadata = await self.storage_service.get_metadata(task_id)
        
        if not metadata:
            logger.warning(f"Task {task_id} not found")
            return None
        
        return metadata
    
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
        all_tasks = await self.storage_service.list_tasks()
        
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
        result_path = await self.storage_service.save_result(task_id, result)
        
        # Update task metadata
        await self.update_task(
            task_id=task_id,
            status="completed",
            progress=100.0,
            result_path=str(result_path)
        )
        
        logger.info(f"Stored result for task {task_id}")
        return str(result_path)


# Factory function for dependency injection
def get_task_service(storage_service: DocumentStorageService) -> TaskService:
    """Get task service instance.
    
    Args:
        storage_service: Document storage service
        
    Returns:
        TaskService: Task service instance
    """
    return TaskService(storage_service)
