"""Task query repository for file system storage."""
import json
import uuid
from typing import Dict, List, Optional, Any

import aiofiles

from app.core.logging import logger
from app.repositories.filesystem.base_repository import FileSystemBaseRepository


class TaskQueryRepository(FileSystemBaseRepository):
    """Repository for task query operations."""
    
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
