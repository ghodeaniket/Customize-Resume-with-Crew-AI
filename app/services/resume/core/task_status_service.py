"""Service dedicated to managing task status updates."""
import time
from typing import Dict, Any, Optional

from app.core.logging import logger
from app.services.task_service import TaskService


class TaskStatusService:
    """Service focused on task status management and progress tracking."""
    
    def __init__(self, task_service: TaskService):
        """Initialize the task status service.
        
        Args:
            task_service: Base task service for status updates
        """
        self.task_service = task_service
        logger.info("Initialized TaskStatusService")
    
    async def mark_task_started(
        self, 
        task_id: str, 
        task_type: str,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Mark a task as started.
        
        Args:
            task_id: Task identifier
            task_type: Type of task (processing, customization, etc.)
            additional_metadata: Any additional metadata for the task
        """
        metadata = {
            "status": "processing",
            "progress": 0.0,
            "started_at": time.time(),
            "task_type": task_type,
            **(additional_metadata or {})
        }
        
        await self.task_service.update_task(task_id=task_id, **metadata)
        logger.info(f"Task {task_id} marked as started with type {task_type}")
    
    async def update_task_progress(
        self, 
        task_id: str, 
        progress: float, 
        message: Optional[str] = None
    ) -> None:
        """Update task progress.
        
        Args:
            task_id: Task identifier
            progress: Progress percentage (0-100)
            message: Optional status message
        """
        update_data = {
            "status": "processing",
            "progress": progress,
            "updated_at": time.time()
        }
        
        if message:
            update_data["message"] = message
        
        await self.task_service.update_task(task_id=task_id, **update_data)
        logger.info(f"Task {task_id} progress updated to {progress}%")
    
    async def mark_task_completed(
        self, 
        task_id: str, 
        start_time: float,
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """Mark a task as completed.
        
        Args:
            task_id: Task identifier
            start_time: Task start time (from time.time())
            result: Optional result data
        """
        completion_time = time.time()
        processing_time_ms = (completion_time - start_time) * 1000
        
        update_data = {
            "status": "completed",
            "progress": 100.0,
            "processing_time_ms": processing_time_ms,
            "completion_time": completion_time,
            "message": "Task completed successfully"
        }
        
        if result:
            update_data["result"] = result
        
        await self.task_service.update_task(task_id=task_id, **update_data)
        logger.info(f"Task {task_id} marked as completed. Processing time: {processing_time_ms:.2f}ms")
    
    async def mark_task_failed(
        self, 
        task_id: str, 
        error: str,
        start_time: float,
        error_type: Optional[str] = None
    ) -> None:
        """Mark a task as failed.
        
        Args:
            task_id: Task identifier
            error: Error message
            start_time: Task start time (from time.time())
            error_type: Optional error type classification
        """
        completion_time = time.time()
        processing_time_ms = (completion_time - start_time) * 1000
        
        update_data = {
            "status": "failed",
            "progress": 100.0,
            "error": error,
            "processing_time_ms": processing_time_ms,
            "failed_at": completion_time
        }
        
        if error_type:
            update_data["error_type"] = error_type
        
        await self.task_service.update_task(task_id=task_id, **update_data)
        logger.error(f"Task {task_id} marked as failed: {error}")
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current task status.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Task status if available
        """
        try:
            task = await self.task_service.get_task(task_id)
            return task
        except Exception as e:
            logger.error(f"Error getting task status for {task_id}: {str(e)}")
            return None
