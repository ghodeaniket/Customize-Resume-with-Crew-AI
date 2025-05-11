"""Dependency injection module."""
from typing import Annotated

from fastapi import Depends

from app.infrastructure.document_processor import DocumentProcessor
from app.services.document_storage_service import DocumentStorageService
from app.services.task_service import TaskService
from app.services.resume_service import ResumeService
from app.services.resume_service_repository import ResumeServiceRepository

from app.repositories.document_repository import DocumentRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.filesystem.document_filesystem_repository import FileSystemDocumentRepository
from app.repositories.filesystem.task_repository import FileSystemTaskRepository
from app.repositories.filesystem.customization_repository import CustomizationRepository
from app.repositories.factory import get_document_repository, get_task_repository

from app.services.resume.storage_service import ResumeStorageService, get_resume_storage_service
from app.services.resume.extraction_service import ResumeExtractionService, get_resume_extraction_service
from app.services.resume.customization_service import ResumeCustomizationService, get_resume_customization_service
from app.services.resume.service import ResumeService as NewResumeService, get_resume_service as get_new_resume_service


# Original dependencies
def get_document_processor() -> DocumentProcessor:
    """Get document processor instance."""
    return DocumentProcessor()


def get_document_storage_service() -> DocumentStorageService:
    """Get document storage service instance."""
    return DocumentStorageService()


def get_task_service(
    storage_service: DocumentStorageService = Depends(get_document_storage_service)
) -> TaskService:
    """Get task service instance."""
    return TaskService(storage_service)


def get_resume_service(
    document_processor: DocumentProcessor = Depends(get_document_processor),
    storage_service: DocumentStorageService = Depends(get_document_storage_service),
    task_service: TaskService = Depends(get_task_service)
) -> ResumeService:
    """Get resume service instance."""
    return ResumeService(
        document_processor=document_processor,
        storage_service=storage_service,
        task_service=task_service
    )


def get_resume_service_repository(
    document_processor: Annotated[DocumentProcessor, Depends(get_document_processor)],
    document_repository: Annotated[DocumentRepository, Depends(get_document_repository)],
    task_repository: Annotated[TaskRepository, Depends(get_task_repository)]
) -> ResumeServiceRepository:
    """Get repository-based resume service instance."""
    return ResumeServiceRepository(
        document_processor=document_processor,
        document_repository=document_repository,
        task_repository=task_repository
    )


# New dependencies for customization repository
def get_customization_repository() -> CustomizationRepository:
    """Get customization repository instance."""
    return CustomizationRepository()


# New service dependencies (not used in the main application yet)
def get_storage_service(
    document_repository: DocumentRepository = Depends(get_document_repository)
) -> ResumeStorageService:
    """Get storage service instance."""
    return get_resume_storage_service(document_repository)


def get_extraction_service(
    document_repository: DocumentRepository = Depends(get_document_repository),
    storage_service: ResumeStorageService = Depends(get_storage_service)
) -> ResumeExtractionService:
    """Get extraction service instance."""
    return get_resume_extraction_service(document_repository, storage_service)


def get_customization_service(
    extraction_service: ResumeExtractionService = Depends(get_extraction_service),
    storage_service: ResumeStorageService = Depends(get_storage_service),
    task_repository: TaskRepository = Depends(get_task_repository),
    customization_repository: CustomizationRepository = Depends(get_customization_repository)
) -> ResumeCustomizationService:
    """Get customization service instance."""
    return get_resume_customization_service(
        extraction_service, 
        storage_service, 
        task_repository,
        customization_repository
    )


def get_new_resume_service_instance(
    storage_service: ResumeStorageService = Depends(get_storage_service),
    extraction_service: ResumeExtractionService = Depends(get_extraction_service),
    customization_service: ResumeCustomizationService = Depends(get_customization_service)
) -> NewResumeService:
    """Get unified resume service instance."""
    return get_new_resume_service(storage_service, extraction_service, customization_service)
