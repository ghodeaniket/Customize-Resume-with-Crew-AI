"""Consolidated file system task repository."""
from typing import Dict, List, Optional, Any

from app.repositories.task_repository import TaskRepository
from app.repositories.filesystem.task_operations_repository import TaskOperationsRepository
from app.repositories.filesystem.task_query_repository import TaskQueryRepository


class FileSystemTaskRepository(TaskRepository):
    """File system implementation of the task repository.
    
    This implementation provides task-specific operations using file storage,
    combining operations and query functionality.
    """
    
    def __init__(self, document_repository: Any = None, base_path: str = None):
        """Initialize file system task repository.
        
        Args:
            document_repository: Document repository (optional for compatibility)
            base_path: Base directory for storage (used if document_repository not provided)
        """
        # If document_repository is provided, use its base_path
        if document_repository and hasattr(document_repository, 'base_path'):
            base_path = str(document_repository.base_path)
        elif document_repository and hasattr(document_repository, 'metadata_repo') and hasattr(document_repository.metadata_repo, 'base_path'):
            base_path = str(document_repository.metadata_repo.base_path)
        elif not base_path:
            # Fallback to default configuration
            from app.core.config import settings
            base_path = settings.UPLOADS_DIR
            
        self.operations = TaskOperationsRepository(base_path)
        self.queries = TaskQueryRepository(base_path)
    
    async def save(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Save a task entity."""
        return await self.queries.save(entity)
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Find a task by ID."""
        return await self.queries.find_by_id(id)
    
    async def find_all(self) -> List[Dict[str, Any]]:
        """Find all tasks."""
        return await self.queries.find_all()
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a task by ID."""
        return await self.queries.update(id, data)
    
    async def delete(self, id: str) -> bool:
        """Delete a task by ID."""
        return await self.operations.delete(id)
    
    async def exists(self, id: str) -> bool:
        """Check if a task exists by ID."""
        return await self.operations.exists(id)
    
    async def create_task(
        self, task_type: str, related_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new task with initial status."""
        return await self.operations.create_task(task_type, related_id)
    
    async def update_task(
        self, task_id: str, status: str, progress: Optional[float] = None, **kwargs
    ) -> Dict[str, Any]:
        """Update task status and progress."""
        return await self.operations.update_task(task_id, status, progress, **kwargs)
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task data by ID."""
        return await self.operations.get_task(task_id)
    
    async def list_tasks(
        self, task_type: Optional[str] = None, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filtering."""
        return await self.queries.list_tasks(task_type, status)
    
    async def store_task_result(self, task_id: str, result: str) -> str:
        """Store the result of a completed task."""
        return await self.operations.store_task_result(task_id, result)
