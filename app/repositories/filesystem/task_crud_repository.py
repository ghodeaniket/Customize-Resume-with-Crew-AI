"""Task CRUD repository implementation for file system storage."""
import time
import uuid
from typing import Dict, List, Optional, Any

from app.core.logging import logger
from app.repositories.task_repository import TaskRepository
from app.repositories.filesystem.base_repository import FileSystemBaseRepository


class TaskCrudRepository(TaskRepository, FileSystemBaseRepository):
    """File system implementation for basic task CRUD operations."""
    
    def __init__(self, base_path: str):
        """Initialize task CRUD repository.
        
        Args:
            base_path: Base directory for storage
        """
        super().__init__(base_path)
        logger.info("Initialized task CRUD repository")
    
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
        all_tasks = []
        
        for task_dir in self.base_path.iterdir():
            if not task_dir.is_dir():
                continue
            
            metadata = await self.get_metadata(task_dir.name)
            if metadata:
                all_tasks.append(metadata)
        
        return all_tasks
    
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
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task data by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict]: Task data if found
        """
        return await self.get_metadata(task_id)
