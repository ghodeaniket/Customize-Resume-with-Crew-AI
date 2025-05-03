"""Service for handling errors during customization."""
import time
from typing import Optional

from app.core.logging import logger
from app.core.exceptions import CustomizationError
from app.repositories.task_repository import TaskRepository
from app.services.resume.customization.state_models import CustomizationState


class ErrorHandlingService:
    """Service for handling and categorizing errors during customization."""
    
    def __init__(self, task_repository: TaskRepository):
        """Initialize the error handling service.
        
        Args:
            task_repository: Repository for task data access
        """
        self.task_repository = task_repository
    
    async def handle_customization_error(
        self, 
        error: Exception, 
        task_id: str, 
        start_time: float,
        state: Optional[CustomizationState] = None
    ) -> None:
        """Handle and categorize customization errors.
        
        Args:
            error: The exception that occurred
            task_id: Task identifier
            start_time: Task start time
            state: Optional customization state
        """
        error_str = str(error)
        
        # Categorize error type
        if "api_key" in error_str.lower() or "authentication" in error_str.lower():
            await self._handle_api_error(error, task_id, start_time, state)
        else:
            await self._handle_general_error(error, task_id, start_time, state)
    
    async def _handle_api_error(
        self, 
        error: Exception, 
        task_id: str, 
        start_time: float,
        state: Optional[CustomizationState] = None
    ) -> None:
        """Handle API-related errors.
        
        Args:
            error: The exception that occurred
            task_id: Task identifier
            start_time: Task start time
            state: Optional customization state
        """
        error_message = f"LLM API authentication failed: {str(error)}"
        logger.error(error_message, exc_info=True)
        
        # Update state if available
        if state:
            state.status = "failed"
            state.error_message = "API key authentication failed. Please check your API key configuration."
        
        # Update task
        await self.task_repository.update_task(
            task_id=task_id,
            status="failed",
            progress=100.0,
            error="API key authentication failed. Please check your API key configuration.",
            processing_time_ms=(time.time() - start_time) * 1000
        )
    
    async def _handle_general_error(
        self, 
        error: Exception, 
        task_id: str, 
        start_time: float,
        state: Optional[CustomizationState] = None
    ) -> None:
        """Handle general errors.
        
        Args:
            error: The exception that occurred
            task_id: Task identifier
            start_time: Task start time
            state: Optional customization state
        """
        error_message = f"Resume customization failed: {str(error)}"
        logger.error(error_message, exc_info=True)
        
        # Update state if available
        if state:
            state.status = "failed"
            state.error_message = str(error)
            state.completed_at = time.time()
        
        # Update task status to failed
        await self.task_repository.update_task(
            task_id=task_id,
            status="failed",
            progress=100.0,
            error=str(error),
            processing_time_ms=(time.time() - start_time) * 1000
        )
    
    def categorize_error_for_retry(self, error: Exception) -> bool:
        """Determine if an error is retryable.
        
        Args:
            error: The exception to categorize
            
        Returns:
            bool: True if the error is potentially retryable
        """
        error_str = str(error).lower()
        
        # API timeout or network errors are retryable
        retryable_patterns = [
            "timeout", 
            "connection", 
            "network", 
            "temporary", 
            "retry",
            "rate limit"
        ]
        
        for pattern in retryable_patterns:
            if pattern in error_str:
                return True
        
        # Authentication errors are not retryable
        non_retryable_patterns = [
            "api_key", 
            "authentication", 
            "unauthorized",
            "forbidden"
        ]
        
        for pattern in non_retryable_patterns:
            if pattern in error_str:
                return False
        
        # Default to not retryable for unknown errors
        return False
