"""Factory functions for repository creation and dependency injection."""
from typing import Annotated
from functools import lru_cache

from fastapi import Depends

from app.core.config import settings
from app.repositories.document_repository import DocumentRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.file_system_repository import (
    FileSystemDocumentRepository,
    FileSystemTaskRepository
)


@lru_cache
def get_document_repository() -> DocumentRepository:
    """Get document repository instance.
    
    Returns:
        DocumentRepository: Document repository implementation
        
    Note:
        This uses lru_cache to ensure a single instance is created
        and reused for the lifetime of the application.
    """
    return FileSystemDocumentRepository(base_path=settings.UPLOADS_DIR)


@lru_cache
def get_task_repository(
    document_repository: Annotated[DocumentRepository, Depends(get_document_repository)]
) -> TaskRepository:
    """Get task repository instance.
    
    Args:
        document_repository: Document repository dependency
        
    Returns:
        TaskRepository: Task repository implementation
        
    Note:
        This uses lru_cache to ensure a single instance is created
        and reused for the lifetime of the application.
    """
    if isinstance(document_repository, FileSystemDocumentRepository):
        return FileSystemTaskRepository(document_repository=document_repository)
    else:
        # For other repository types, we would implement corresponding task repositories
        raise NotImplementedError(
            f"Task repository not implemented for {document_repository.__class__.__name__}"
        )
