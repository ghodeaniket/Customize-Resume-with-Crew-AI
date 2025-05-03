"""Service for resume processing and customization."""
import time
from typing import Dict, Optional, Any, BinaryIO, List
from pathlib import Path

from fastapi import UploadFile, BackgroundTasks

from app.core.logging import logger
from app.core.config import settings
from app.core.exceptions import DocumentProcessingError, ResumeNotFoundError, CustomizationError
from app.infrastructure.document_processor import DocumentProcessor
from app.services.document_storage_service import DocumentStorageService
from app.services.task_service import TaskService
from app.services.resume.core.resume_extractor_service import ResumeExtractorService
from app.services.resume.core.resume_retrieval_service import ResumeRetrievalService
from app.services.resume.core.task_status_service import TaskStatusService
from app.services.resume.core.resume_orchestrator_service import ResumeOrchestratorService
from app.services.resume.customization.orchestrator_slim import ResumeCustomizationService


class ResumeService:
    """Service for processing and customizing resumes."""
    
    def __init__(
        self, 
        document_processor: DocumentProcessor,
        storage_service: DocumentStorageService,
        task_service: TaskService
    ):
        """Initialize the resume service.
        
        Args:
            document_processor: Document processor for text extraction
            storage_service: Storage service for document persistence
            task_service: Task service for tracking progress
        """
        # Initialize core sub-services
        self.extractor_service = ResumeExtractorService(document_processor, storage_service)
        self.retrieval_service = ResumeRetrievalService(storage_service)
        self.task_status_service = TaskStatusService(task_service)
        
        # Initialize orchestrator service
        self.orchestrator = ResumeOrchestratorService(
            extractor_service=self.extractor_service,
            retrieval_service=self.retrieval_service,
            task_status_service=self.task_status_service,
            storage_service=storage_service
        )
        
        # Store original services for customization
        self.document_processor = document_processor
        self.storage_service = storage_service
        self.task_service = task_service
        
        logger.info("Initialized ResumeService with sub-services")
    
    async def process_resume(
        self, file_content: bytes, filename: str, task_id: str
    ) -> Dict[str, Any]:
        """Process a resume file.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            task_id: Unique task identifier
            
        Returns:
            Dict[str, Any]: Processing result with metadata
            
        Raises:
            DocumentProcessingError: If processing fails
        """
        return await self.orchestrator.process_resume(file_content, filename, task_id)
    
    async def resume_exists(self, task_id: str) -> bool:
        """Check if a resume exists.
        
        Args:
            task_id: Task identifier
            
        Returns:
            bool: True if the resume exists, False otherwise
        """
        return await self.retrieval_service.resume_exists(task_id)
    
    async def get_resume_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get resume data by task ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Resume data if available
        """
        return await self.retrieval_service.get_resume_data(task_id)
    
    async def customize_resume(
        self, 
        resume_id: str, 
        job_description: str, 
        task_id: str,
        customize_level: str = "standard"
    ) -> str:
        """Customize a resume based on a job description using CrewAI.
        
        This method delegates to the ResumeCustomizationService for
        the actual customization workflow.
        
        Args:
            resume_id: Resume task identifier
            job_description: Job description text
            task_id: New task identifier for customization
            customize_level: Level of customization (minimal, standard, comprehensive)
            
        Returns:
            str: Task ID for the customization task
            
        Raises:
            ResumeNotFoundError: If the resume doesn't exist
            CustomizationError: If the customization process fails
        """
        # Create customization service
        from app.services.resume.extraction_service import ResumeExtractionService
        from app.services.resume.storage_service import ResumeStorageService
        from app.repositories.task_repository import TaskRepository
        
        # Get dependencies
        extraction_service = ResumeExtractionService(self.document_processor)
        storage_service = ResumeStorageService(self.storage_service.storage_path)
        task_repository = TaskRepository(self.task_service)
        
        # Create customization service instance
        customization_service = ResumeCustomizationService(
            extraction_service=extraction_service,
            storage_service=storage_service,
            task_repository=task_repository
        )
        
        # Delegate to customization service
        return await customization_service.customize_resume(
            resume_id=resume_id,
            job_description=job_description,
            task_id=task_id,
            customize_level=customize_level
        )
    
    async def get_customization_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get customization result by task ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Customization result if available
        """
        return await self.orchestrator.get_customization_result(task_id)


# Factory function is now in dependencies.py
