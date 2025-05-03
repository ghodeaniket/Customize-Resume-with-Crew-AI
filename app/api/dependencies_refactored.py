"""Dependencies for the FastAPI application using refactored services."""
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.infrastructure.document_processor import DocumentProcessor
from app.repositories.document_repository import DocumentRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.factory import get_document_repository, get_task_repository
from app.services.resume.storage_service import ResumeStorageService, get_resume_storage_service
from app.services.resume.extraction_service import ResumeExtractionService, get_resume_extraction_service
from app.services.resume.customization_service import ResumeCustomizationService, get_resume_customization_service
from app.services.resume.service import ResumeService, get_resume_service


# Infrastructure dependencies

@lru_cache
def get_document_processor() -> DocumentProcessor:
    """Get document processor instance.
    
    Returns:
        DocumentProcessor: Document processor instance
    """
    return DocumentProcessor()


# Repository dependencies

@lru_cache
def get_repositories():
    """Get repository instances.
    
    Returns:
        tuple: Document repository and task repository instances
    """
    document_repo = get_document_repository()
    task_repo = get_task_repository()
    return document_repo, task_repo


def get_document_repository_dependency() -> DocumentRepository:
    """Get document repository instance for dependency injection.
    
    Returns:
        DocumentRepository: Document repository instance
    """
    document_repo, _ = get_repositories()
    return document_repo


def get_task_repository_dependency() -> TaskRepository:
    """Get task repository instance for dependency injection.
    
    Returns:
        TaskRepository: Task repository instance
    """
    _, task_repo = get_repositories()
    return task_repo


# Service dependencies

def get_resume_storage_service_dependency(
    document_repository: Annotated[DocumentRepository, Depends(get_document_repository_dependency)]
) -> ResumeStorageService:
    """Get resume storage service instance.
    
    Args:
        document_repository: Document repository dependency
        
    Returns:
        ResumeStorageService: Resume storage service instance
    """
    return get_resume_storage_service(document_repository=document_repository)


def get_resume_extraction_service_dependency(
    document_processor: Annotated[DocumentProcessor, Depends(get_document_processor)],
    storage_service: Annotated[ResumeStorageService, Depends(get_resume_storage_service_dependency)]
) -> ResumeExtractionService:
    """Get resume extraction service instance.
    
    Args:
        document_processor: Document processor dependency
        storage_service: Resume storage service dependency
        
    Returns:
        ResumeExtractionService: Resume extraction service instance
    """
    return get_resume_extraction_service(
        document_processor=document_processor,
        storage_service=storage_service
    )


def get_resume_customization_service_dependency(
    extraction_service: Annotated[ResumeExtractionService, Depends(get_resume_extraction_service_dependency)],
    storage_service: Annotated[ResumeStorageService, Depends(get_resume_storage_service_dependency)],
    task_repository: Annotated[TaskRepository, Depends(get_task_repository_dependency)]
) -> ResumeCustomizationService:
    """Get resume customization service instance.
    
    Args:
        extraction_service: Resume extraction service dependency
        storage_service: Resume storage service dependency
        task_repository: Task repository dependency
        
    Returns:
        ResumeCustomizationService: Resume customization service instance
    """
    return get_resume_customization_service(
        extraction_service=extraction_service,
        storage_service=storage_service,
        task_repository=task_repository
    )


def get_resume_service_dependency(
    storage_service: Annotated[ResumeStorageService, Depends(get_resume_storage_service_dependency)],
    extraction_service: Annotated[ResumeExtractionService, Depends(get_resume_extraction_service_dependency)],
    customization_service: Annotated[ResumeCustomizationService, Depends(get_resume_customization_service_dependency)]
) -> ResumeService:
    """Get resume service instance using refactored services.
    
    This dependency maintains backward compatibility with the original resume service
    interface, while leveraging the improvements of the refactored architecture.
    
    Args:
        storage_service: Resume storage service dependency
        extraction_service: Resume extraction service dependency
        customization_service: Resume customization service dependency
        
    Returns:
        ResumeService: Resume service instance
    """
    return get_resume_service(
        storage_service=storage_service,
        extraction_service=extraction_service,
        customization_service=customization_service
    )


# Backward compatibility aliases
get_refactored_resume_service = get_resume_service_dependency
