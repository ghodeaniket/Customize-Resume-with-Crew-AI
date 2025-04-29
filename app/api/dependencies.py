"""FastAPI dependency injection functions."""
from typing import Annotated

from fastapi import Depends

from app.infrastructure.document_processor import DocumentProcessor
from app.services.document_storage_service import DocumentStorageService, get_document_storage_service
from app.services.resume_service import ResumeService


def get_document_processor() -> DocumentProcessor:
    """Dependency for document processor.
    
    Returns:
        DocumentProcessor: Instance of document processor
    """
    return DocumentProcessor()


def get_resume_service(
    document_processor: DocumentProcessor = Depends(get_document_processor),
    storage_service: DocumentStorageService = Depends(get_document_storage_service)
) -> ResumeService:
    """Dependency for resume service.
    
    Args:
        document_processor: Document processor instance
        storage_service: Document storage service instance
        
    Returns:
        ResumeService: Instance of resume service
    """
    return ResumeService(document_processor, storage_service)
