"""Service for managing task progress during customization."""
import time
from typing import Dict, Any

from app.core.logging import logger
from app.repositories.task_repository import TaskRepository
from app.services.resume.customization.state_models import CustomizationState


class TaskProgressService:
    """Service for managing task progress updates during customization."""
    
    def __init__(self, task_repository: TaskRepository):
        """Initialize the task progress service.
        
        Args:
            task_repository: Repository for task data access
        """
        self.task_repository = task_repository
    
    async def initialize_task(
        self, 
        task_id: str, 
        resume_id: str, 
        customize_level: str
    ) -> None:
        """Initialize task status for customization.
        
        Args:
            task_id: Task identifier
            resume_id: Resume identifier
            customize_level: Level of customization
        """
        await self.task_repository.update_task(
            task_id=task_id,
            status="processing",
            progress=0.0,
            resume_id=resume_id,
            customization_type="job_description",
            customize_level=customize_level,
            started_at=time.time()
        )
        logger.info(f"Initialized task {task_id} for resume customization")
    
    async def update_progress(
        self, 
        task_id: str, 
        progress: float, 
        message: str
    ) -> None:
        """Update task progress.
        
        Args:
            task_id: Task identifier
            progress: Progress percentage (0-100)
            message: Status message
        """
        await self.task_repository.update_task(
            task_id=task_id,
            status="processing",
            progress=progress,
            message=message
        )
        logger.info(f"Updated task {task_id} progress to {progress}%: {message}")
    
    async def mark_completed(
        self, 
        task_id: str, 
        start_time: float
    ) -> None:
        """Mark task as completed.
        
        Args:
            task_id: Task identifier
            start_time: Task start time
        """
        completion_time = time.time() - start_time
        await self.task_repository.update_task(
            task_id=task_id,
            status="completed",
            progress=100.0,
            message="Resume customization completed",
            processing_time_ms=completion_time * 1000,
            completion_time=time.time()
        )
        logger.info(f"Task {task_id} completed in {completion_time:.2f} seconds")
    
    async def mark_failed(
        self, 
        task_id: str, 
        error_message: str, 
        start_time: float
    ) -> None:
        """Mark task as failed.
        
        Args:
            task_id: Task identifier
            error_message: Error message
            start_time: Task start time
        """
        processing_time = (time.time() - start_time) * 1000
        await self.task_repository.update_task(
            task_id=task_id,
            status="failed",
            progress=100.0,
            error=error_message,
            processing_time_ms=processing_time
        )
        logger.error(f"Task {task_id} failed: {error_message}")
    
    async def update_state_progress(
        self, 
        task_id: str, 
        state: CustomizationState
    ) -> None:
        """Update task progress based on state.
        
        Args:
            task_id: Task identifier
            state: Customization state
        """
        message = ""
        if state.job_analysis.completed and not state.resume_optimization.completed:
            message = "Job analysis completed, optimizing resume"
        elif state.resume_optimization.completed:
            message = "Resume customization completed"
        
        if message:
            await self.update_progress(task_id, state.progress, message)
