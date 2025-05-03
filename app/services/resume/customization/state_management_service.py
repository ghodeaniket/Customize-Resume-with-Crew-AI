"""Service for managing customization state."""
import time
from typing import Dict, Any, Optional

from app.core.logging import logger
from app.services.resume.customization.state_models import CustomizationState


class StateManagementService:
    """Service for managing customization state changes."""
    
    @staticmethod
    def update_job_analysis_state(
        state: CustomizationState,
        job_description: str,
        analysis_result: Optional[str] = None,
        completed: bool = False,
        error: Optional[str] = None
    ) -> None:
        """Update the job analysis portion of state.
        
        Args:
            state: Customization state to update
            job_description: Job description text
            analysis_result: Optional analysis result
            completed: Whether analysis is completed
            error: Optional error message
        """
        state.job_analysis.job_description = job_description
        
        if analysis_result:
            state.job_analysis.analysis_result = analysis_result
        
        if completed:
            state.job_analysis.completed = True
            state.progress = 60.0
        
        if error:
            state.job_analysis.error = error
            state.error_message = f"Job analysis failed: {error}"
        
        logger.debug(f"Updated job analysis state - completed: {completed}")
    
    @staticmethod
    def update_optimization_state(
        state: CustomizationState,
        resume_text: Optional[str] = None,
        optimized_resume: Optional[str] = None,
        completed: bool = False,
        error: Optional[str] = None
    ) -> None:
        """Update the resume optimization portion of state.
        
        Args:
            state: Customization state to update
            resume_text: Optional original resume text
            optimized_resume: Optional optimized resume text
            completed: Whether optimization is completed
            error: Optional error message
        """
        if resume_text:
            state.resume_optimization.resume_text = resume_text
        
        if optimized_resume:
            state.resume_optimization.optimized_resume = optimized_resume
        
        if completed:
            state.resume_optimization.completed = True
            state.progress = 100.0
        
        if error:
            state.resume_optimization.error = error
            state.error_message = f"Resume optimization failed: {error}"
        
        logger.debug(f"Updated optimization state - completed: {completed}")
    
    @staticmethod
    def update_progress(state: CustomizationState, progress: float) -> None:
        """Update the overall progress.
        
        Args:
            state: Customization state to update
            progress: Progress percentage (0-100)
        """
        state.progress = progress
        logger.debug(f"Updated state progress to {progress}%")
    
    @staticmethod
    def mark_completed(state: CustomizationState) -> None:
        """Mark the state as completed.
        
        Args:
            state: Customization state to update
        """
        state.status = "completed"
        state.progress = 100.0
        state.completed_at = time.time()
        logger.debug("Marked state as completed")
    
    @staticmethod
    def mark_failed(state: CustomizationState, error_message: str) -> None:
        """Mark the state as failed.
        
        Args:
            state: Customization state to update
            error_message: Error message to record
        """
        state.status = "failed"
        state.error_message = error_message
        state.completed_at = time.time()
        logger.debug(f"Marked state as failed: {error_message}")
