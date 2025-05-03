"""Refactored resume service that delegates to specialized services."""
from typing import Dict, Any, Optional

from app.core.logging import logger
from app.infrastructure.document_processor import DocumentProcessor
from app.services.document_storage_service import DocumentStorageService
from app.services.task_service import TaskService
from app.services.resume.core.resume_extractor_service import ResumeExtractorService
from app.services.resume.core.resume_retrieval_service import ResumeRetrievalService
from app.services.resume.core.task_status_service import TaskStatusService
from app.services.resume.core.resume_orchestrator_service import ResumeOrchestratorService
from app.services.resume.customization_service import ResumeCustomizationService, get_resume_customization_service
from app.services.resume.extraction_service import ResumeExtractionService
from app.services.resume.storage_service import ResumeStorageService
from app.repositories.file_system_repository import FileSystemTaskRepository


class ResumeService:
    """Refactored resume service that composes specialized services."""
    
    def __init__(
        self, 
        document_processor: DocumentProcessor,
        storage_service: DocumentStorageService,
        task_service: TaskService
    ):
        """Initialize the resume service with composed services.
        
        Args:
            document_processor: Document processor for text extraction
            storage_service: Storage service for document persistence
            task_service: Task service for tracking progress
        """
        # Initialize specialized services
        self.extractor_service = ResumeExtractorService(
            document_processor=document_processor,
            storage_service=storage_service
        )
        
        self.retrieval_service = ResumeRetrievalService(
            storage_service=storage_service
        )
        
        self.task_status_service = TaskStatusService(
            task_service=task_service
        )
        
        self.orchestrator_service = ResumeOrchestratorService(
            extractor_service=self.extractor_service,
            retrieval_service=self.retrieval_service,
            task_status_service=self.task_status_service,
            storage_service=storage_service
        )
        
        # For customization service compatibility, we need additional services
        from app.core.config import settings
        base_path = settings.UPLOADS_DIR
        self.task_repository = FileSystemTaskRepository(base_path)
        self.extraction_service = ResumeExtractionService(storage_service=storage_service)
        self.storage_wrapper = ResumeStorageService(storage_service=storage_service)
        
        self.customization_service = get_resume_customization_service(
            extraction_service=self.extraction_service,
            storage_service=self.storage_wrapper,
            task_repository=self.task_repository
        )
        
        logger.info("Initialized ResumeService with specialized services")
    
    async def process_resume(
        self, file_content: bytes, filename: str, task_id: str
    ) -> Dict[str, Any]:
        """Process a resume file.
        
        Delegates to the orchestrator service for processing.
        """
        return await self.orchestrator_service.process_resume(
            file_content, filename, task_id
        )
    
    async def resume_exists(self, task_id: str) -> bool:
        """Check if a resume exists.
        
        Delegates to the retrieval service.
        """
        return await self.retrieval_service.resume_exists(task_id)
    
    async def get_resume_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get resume data by task ID.
        
        Delegates to the retrieval service.
        """
        return await self.retrieval_service.get_resume_data(task_id)
    
    async def customize_resume(
        self, 
        resume_id: str, 
        job_description: str, 
        task_id: str,
        customize_level: str = "standard"
    ) -> str:
        """Customize a resume based on a job description.
        
        Delegates to the customization service.
        """
        return await self.customization_service.customize_resume(
            resume_id=resume_id,
            job_description=job_description,
            task_id=task_id,
            customize_level=customize_level
        )
    
    async def get_customization_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get customization result by task ID.
        
        Delegates to the customization service.
        """
        return await self.customization_service.get_by_id(task_id)


# Backward compatibility: factory function
def get_resume_service(
    document_processor: DocumentProcessor,
    storage_service: DocumentStorageService,
    task_service: TaskService
) -> ResumeService:
    """Factory function for backward compatibility.
    
    Returns the refactored ResumeService instance.
    """
    return ResumeService(
        document_processor=document_processor,
        storage_service=storage_service,
        task_service=task_service
    )
