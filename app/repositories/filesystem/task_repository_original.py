"""Task repository implementation for file system storage."""
import time
import uuid
from typing import Dict, List, Optional, Any

from app.core.logging import logger
from app.repositories.task_repository import TaskRepository
from app.repositories.filesystem.base_repository import FileSystemBaseRepository
from app.repositories.filesystem.document_storage_repository import DocumentStorageRepository


class FileSystemTaskRepository(TaskRepository, FileSystemBaseRepository):
    """File system implementation of the task repository.
    
    This implementation provides task-specific operations using file storage.
    """
    
    def __init__(self, base_path: str):
        """Initialize file system task repository.
        
        Args:
            base_path: Base directory for storage
        """
        super().__init__(base_path)
        self.storage_repository = DocumentStorageRepository(base_path)
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
        await self.save_metadata(task_id, entity)
        
        return entity
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Find a task by ID.
        
        Args:
            id: Task ID
            
        Returns:
            Optional[Dict[str, Any]]: Task if found, None otherwise
        """
        return await self.get_metadata(id)
    
    async def find_all(self) -> List[Dict[str, Any]]:
        """Find all tasks.
        
        Returns:
            List[Dict[str, Any]]: List of all tasks
        """
        return await self.list_tasks()
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a task by ID.
        
        Args:
            id: Task ID
            data: Data to update
            
        Returns:
            Optional[Dict[str, Any]]: Updated task if found, None otherwise
        """
        metadata = await self.get_metadata(id)
        if not metadata:
            return None
        
        # Update metadata
        metadata.update(data)
        await self.save_metadata(id, metadata)
        
        return metadata
    
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
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task data by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict]: Task data if found
        """
        return await self.get_metadata(task_id)
    
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
        all_tasks = []
        
        for task_dir in self.base_path.iterdir():
            if not task_dir.is_dir():
                continue
            
            metadata = await self.get_metadata(task_dir.name)
            if metadata:
                all_tasks.append(metadata)
        
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
