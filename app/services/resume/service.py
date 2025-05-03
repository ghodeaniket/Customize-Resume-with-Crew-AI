"""Main resume service that coordinates specialized services."""
from typing import Dict, Optional, Any, List
from pathlib import Path

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError, ResumeNotFoundError, CustomizationError
from app.services.resume.base import BaseService
from app.services.resume.storage_service import ResumeStorageService
from app.services.resume.extraction_service import ResumeExtractionService
from app.services.resume.customization_service import ResumeCustomizationService


class ResumeService(BaseService[Dict[str, Any], str]):
    """Main resume service that coordinates specialized services.
    
    This service provides a unified interface for resume operations by
    delegating to specialized services for storage, extraction, and customization.
    It maintains backward compatibility with the original implementation
    while leveraging the improved architecture.
    """
    
    def __init__(
        self, 
        storage_service: ResumeStorageService,
        extraction_service: ResumeExtractionService,
        customization_service: ResumeCustomizationService
    ):
        """Initialize the resume service.
        
        Args:
            storage_service: Service for resume storage operations
            extraction_service: Service for resume extraction operations
            customization_service: Service for resume customization operations
        """
        self.storage_service = storage_service
        self.extraction_service = extraction_service
        self.customization_service = customization_service
        logger.info("Initialized ResumeService with specialized services")
    
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get resume data by ID.
        
        Args:
            id: Resume identifier
            
        Returns:
            Optional[Dict[str, Any]]: Resume data if found
        """
        return await self.get_resume_data(id)
    
    async def exists(self, id: str) -> bool:
        """Check if a resume exists.
        
        Args:
            id: Resume identifier
            
        Returns:
            bool: True if the resume exists, False otherwise
        """
        return await self.resume_exists(id)
    
    async def process_resume(
        self, file_content: bytes, filename: str, task_id: str
    ) -> Dict[str, Any]:
        """Process a resume file.
        
        This method maintains backward compatibility with the original
        implementation by delegating to the extraction service.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            task_id: Unique task identifier
            
        Returns:
            Dict[str, Any]: Processing result with metadata
            
        Raises:
            DocumentProcessingError: If processing fails
        """
        logger.info(f"Delegating resume processing to extraction service: {filename}, task: {task_id}")
        return await self.extraction_service.process_resume(
            file_content=file_content,
            filename=filename,
            task_id=task_id
        )
    
    async def resume_exists(self, task_id: str) -> bool:
        """Check if a resume exists.
        
        This method maintains backward compatibility with the original
        implementation by delegating to the storage service.
        
        Args:
            task_id: Task identifier
            
        Returns:
            bool: True if the resume exists, False otherwise
        """
        return await self.storage_service.exists(task_id)
    
    async def get_resume_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get resume data by task ID.
        
        This method maintains backward compatibility with the original
        implementation by delegating to the extraction service.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Resume data if available
        """
        return await self.extraction_service.get_by_id(task_id)
    
    async def customize_resume(
        self, 
        resume_id: str, 
        job_description: str, 
        task_id: str,
        customize_level: str = "standard"
    ) -> str:
        """Customize a resume based on a job description.
        
        This method maintains backward compatibility with the original
        implementation by delegating to the customization service.
        
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
        logger.info(f"Delegating resume customization to customization service: resume: {resume_id}, task: {task_id}")
        return await self.customization_service.customize_resume(
            resume_id=resume_id,
            job_description=job_description,
            task_id=task_id,
            customize_level=customize_level
        )
    
    async def get_customization_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get customization result by task ID.
        
        This method maintains backward compatibility with the original
        implementation by delegating to the customization service.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Customization result if available
        """
        return await self.customization_service.get_by_id(task_id)


# Factory function for dependency injection
def get_resume_service(
    storage_service: ResumeStorageService,
    extraction_service: ResumeExtractionService,
    customization_service: ResumeCustomizationService
) -> ResumeService:
    """Get resume service instance.
    
    Args:
        storage_service: Resume storage service
        extraction_service: Resume extraction service
        customization_service: Resume customization service
        
    Returns:
        ResumeService: Resume service instance
    """
    return ResumeService(
        storage_service=storage_service,
        extraction_service=extraction_service,
        customization_service=customization_service
    )
