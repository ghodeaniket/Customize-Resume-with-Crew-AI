"""Base controller with shared functionality for resume operations."""
from fastapi import HTTPException, status

from app.core.logging import logger
from app.services.resume_service import ResumeService
from app.services.task_service import TaskService
from app.services.document_storage_service import DocumentStorageService
from app.infrastructure.document_processor import DocumentProcessor


class BaseResumeController:
    """Base controller with shared dependencies and utilities."""
    
    def __init__(
        self,
        resume_service: ResumeService,
        task_service: TaskService,
        storage_service: DocumentStorageService,
        document_processor: DocumentProcessor
    ):
        """Initialize the base controller with dependencies."""
        self.resume_service = resume_service
        self.task_service = task_service
        self.storage_service = storage_service
        self.document_processor = document_processor
    
    def _calculate_progress(self, status: str) -> float:
        """Calculate progress based on status.
        
        Args:
            status: The current status
            
        Returns:
            float: Progress percentage
        """
        if status == "completed":
            return 100.0
        elif status == "processing":
            return 50.0
        elif status == "failed":
            return 100.0
        else:
            return 0.0
    
    async def _validate_resume_exists(self, resume_id: str) -> None:
        """Validate that a resume exists.
        
        Args:
            resume_id: Resume identifier
            
        Raises:
            HTTPException: If resume doesn't exist
        """
        if not await self.resume_service.resume_exists(resume_id):
            logger.warning(f"Resume not found: {resume_id}", extra={
                "resume_id": resume_id,
                "error": "resume_not_found"
            })
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Resume with ID {resume_id} not found"
            )
    
    async def _validate_task_exists(self, task_id: str) -> dict:
        """Validate that a task exists and return task data.
        
        Args:
            task_id: Task identifier
            
        Returns:
            dict: Task data
            
        Raises:
            HTTPException: If task doesn't exist
        """
        task = await self.task_service.get_task(task_id)
        
        if not task:
            logger.warning(f"Task not found: {task_id}", extra={
                "task_id": task_id,
                "error": "task_not_found"
            })
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found"
            )
        
        return task
    
    def _validate_job_description(self, job_description: str) -> None:
        """Validate job description content.
        
        Args:
            job_description: Job description text
            
        Raises:
            HTTPException: If job description is invalid
        """
        if not job_description or len(job_description) < 10:
            logger.warning("Job description too short", extra={
                "error": "invalid_job_description",
                "length": len(job_description) if job_description else 0
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description is too short or empty"
            )
