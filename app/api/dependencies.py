"""Dependencies for the FastAPI application."""
from typing import Annotated

from fastapi import Depends

from app.infrastructure.document_processor import DocumentProcessor
from app.services.document_storage_service import DocumentStorageService
from app.services.task_service import TaskService
from app.services.resume_service import ResumeService
from app.services.resume_service_repository import ResumeServiceRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.factory import get_document_repository, get_task_repository


def get_document_processor() -> DocumentProcessor:
    """Get document processor instance."""
    return DocumentProcessor()


def get_document_storage_service() -> DocumentStorageService:
    """Get document storage service instance."""
    return DocumentStorageService()


def get_task_service(
    storage_service: DocumentStorageService = Depends(get_document_storage_service)
) -> TaskService:
    """Get task service instance.
    
    Args:
        storage_service: Document storage service
        
    Returns:
        TaskService: Task service instance
    """
    return TaskService(storage_service)


def get_resume_service(
    document_processor: DocumentProcessor = Depends(get_document_processor),
    storage_service: DocumentStorageService = Depends(get_document_storage_service),
    task_service: TaskService = Depends(get_task_service)
) -> ResumeService:
    """Get resume service instance.
    
    Args:
        document_processor: Document processor
        storage_service: Document storage service
        task_service: Task service
        
    Returns:
        ResumeService: Resume service instance
    """
    return ResumeService(
        document_processor=document_processor,
        storage_service=storage_service,
        task_service=task_service
    )


# New repository-based dependencies

def get_resume_service_repository(
    document_processor: Annotated[DocumentProcessor, Depends(get_document_processor)],
    document_repository: Annotated[DocumentRepository, Depends(get_document_repository)],
    task_repository: Annotated[TaskRepository, Depends(get_task_repository)]
) -> ResumeServiceRepository:
    """Get repository-based resume service instance.
    
    Args:
        document_processor: Document processor
        document_repository: Document repository
        task_repository: Task repository
        
    Returns:
        ResumeServiceRepository: Repository-based resume service instance
    """
    return ResumeServiceRepository(
        document_processor=document_processor,
        document_repository=document_repository,
        task_repository=task_repository
    )
