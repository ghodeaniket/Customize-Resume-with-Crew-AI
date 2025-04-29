"""FastAPI dependency injection functions."""
from typing import Annotated

from fastapi import Depends

from app.infrastructure.document_processor import DocumentProcessor
from app.services.document_storage_service import DocumentStorageService, get_document_storage_service
from app.services.task_service import TaskService, get_task_service
from app.services.resume_service import ResumeService


def get_document_processor() -> DocumentProcessor:
    """Dependency for document processor.
    
    Returns:
        DocumentProcessor: Instance of document processor
    """
    return DocumentProcessor()


def get_task_service(
    storage_service: DocumentStorageService = Depends(get_document_storage_service)
) -> TaskService:
    """Dependency for task service.
    
    Args:
        storage_service: Document storage service instance
        
    Returns:
        TaskService: Instance of task service
    """
    return TaskService(storage_service)


def get_resume_service(
    document_processor: DocumentProcessor = Depends(get_document_processor),
    storage_service: DocumentStorageService = Depends(get_document_storage_service),
    task_service: TaskService = Depends(get_task_service)
) -> ResumeService:
    """Dependency for resume service.
    
    Args:
        document_processor: Document processor instance
        storage_service: Document storage service instance
        task_service: Task service instance
        
    Returns:
        ResumeService: Instance of resume service
    """
    return ResumeService(document_processor, storage_service, task_service)
