"""Service for validating customization inputs."""
from typing import Dict, Any, Optional

from app.core.logging import logger
from app.core.exceptions import ResumeNotFoundError, CustomizationError
from app.services.resume.extraction_service import ResumeExtractionService


class CustomizationValidationService:
    """Service for validating customization inputs and prerequisites."""
    
    def __init__(self, extraction_service: ResumeExtractionService):
        """Initialize the validation service.
        
        Args:
            extraction_service: Service for extracting resume data
        """
        self.extraction_service = extraction_service
    
    async def validate_resume_exists(self, resume_id: str) -> None:
        """Validate that a resume exists.
        
        Args:
            resume_id: Resume identifier
            
        Raises:
            ResumeNotFoundError: If the resume doesn't exist
        """
        if not await self.extraction_service.exists(resume_id):
            logger.error(f"Resume {resume_id} not found for customization")
            raise ResumeNotFoundError(resume_id)
        
        logger.debug(f"Resume {resume_id} exists")
    
    async def validate_resume_has_text(self, resume_id: str) -> str:
        """Validate that a resume has extractable text.
        
        Args:
            resume_id: Resume identifier
            
        Returns:
            str: The resume text
            
        Raises:
            CustomizationError: If resume text is not available
        """
        resume_data = await self.extraction_service.get_by_id(resume_id)
        if not resume_data or "text" not in resume_data:
            logger.error(f"Resume {resume_id} does not have extractable text")
            raise CustomizationError("Resume text not available")
        
        resume_text = resume_data["text"]
        if not resume_text.strip():
            logger.error(f"Resume {resume_id} has empty text content")
            raise CustomizationError("Resume text is empty")
        
        logger.info(f"Retrieved resume text for customization, length: {len(resume_text)}")
        return resume_text
    
    def validate_job_description(self, job_description: str) -> None:
        """Validate the job description content.
        
        Args:
            job_description: Job description text
            
        Raises:
            CustomizationError: If job description is invalid
        """
        if not job_description.strip():
            logger.error("Job description is empty")
            raise CustomizationError("Job description cannot be empty")
        
        # Check minimum length requirement
        min_length = 50  # Minimum reasonable length for a job description
        if len(job_description.strip()) < min_length:
            logger.error(f"Job description too short: {len(job_description)} chars")
            raise CustomizationError(
                f"Job description is too short. Please provide at least {min_length} characters."
            )
    
    def validate_customize_level(self, customize_level: str) -> None:
        """Validate the customization level.
        
        Args:
            customize_level: Level of customization
            
        Raises:
            CustomizationError: If customize level is invalid
        """
        valid_levels = ["minimal", "standard", "comprehensive"]
        if customize_level not in valid_levels:
            logger.error(f"Invalid customize level: {customize_level}")
            raise CustomizationError(
                f"Invalid customize level '{customize_level}'. "
                f"Must be one of: {', '.join(valid_levels)}"
            )
