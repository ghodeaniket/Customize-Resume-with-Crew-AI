"""Composed task repository implementation for file system storage."""
from typing import Dict, List, Optional, Any

from app.core.logging import logger
from app.repositories.task_repository import TaskRepository
from app.repositories.filesystem.task_crud_repository import TaskCrudRepository
from app.repositories.filesystem.task_management_repository import TaskManagementRepository


class FileSystemTaskRepository(TaskRepository):
    """File system implementation composed of specialized repositories."""
    
    def __init__(self, base_path: str):
        """Initialize composed task repository.
        
        Args:
            base_path: Base directory for storage
        """
        self.crud = TaskCrudRepository(base_path)
        self.management = TaskManagementRepository(base_path)
        logger.info("Initialized composed file system task repository")
    
    # CRUD operations delegate to TaskCrudRepository
    async def save(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Save a task entity."""
        return await self.crud.save(entity)
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Find a task by ID."""
        return await self.crud.find_by_id(id)
    
    async def find_all(self) -> List[Dict[str, Any]]:
        """Find all tasks."""
        return await self.crud.find_all()
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a task by ID."""
        return await self.crud.update(id, data)
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task data by ID."""
        return await self.crud.get_task(task_id)
    
    # Management operations delegate to TaskManagementRepository
    async def create_task(
        self, task_type: str, related_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new task with initial status."""
        return await self.management.create_task(task_type, related_id)
    
    async def update_task(
        self, task_id: str, status: str, progress: Optional[float] = None, **kwargs
    ) -> Dict[str, Any]:
        """Update task status and progress."""
        return await self.management.update_task(task_id, status, progress, **kwargs)
    
    async def list_tasks(
        self, task_type: Optional[str] = None, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filtering."""
        return await self.management.list_tasks(task_type, status)
    
    async def store_task_result(self, task_id: str, result: str) -> str:
        """Store the result of a completed task."""
        return await self.management.store_task_result(task_id, result)
