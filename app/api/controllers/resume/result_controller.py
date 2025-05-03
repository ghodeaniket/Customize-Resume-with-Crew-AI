"""Controller for retrieving resume processing results."""
from typing import Dict, Any
from fastapi import HTTPException, status

from app.core.logging import logger
from app.models.schemas import responses
from app.api.controllers.resume.base_controller import BaseResumeController


class ResumeResultController(BaseResumeController):
    """Controller for handling resume result retrieval operations."""
    
    async def get_resume_status(
        self,
        task_id: str
    ) -> responses.TaskStatusResponse:
        """Get the status of a resume processing task.
        
        Args:
            task_id: The task ID of the resume processing task
            
        Returns:
            TaskStatusResponse: Task status details
            
        Raises:
            HTTPException: If task is not found
        """
        resume_data = await self.resume_service.get_resume_data(task_id)
        
        if not resume_data:
            logger.warning(f"Resume task not found: {task_id}", extra={
                "task_id": task_id,
                "error": "task_not_found"
            })
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume task with ID {task_id} not found"
            )
        
        metadata = resume_data.get("metadata", {})
        status_value = metadata.get("status", "unknown")
        
        # Calculate progress
        progress = self._calculate_progress(status_value)
        
        # Get timestamps
        created_at = metadata.get("created_at", "")
        updated_at = metadata.get("updated_at", "")
        
        logger.info(f"Retrieved resume task status: {task_id}, status: {status_value}", extra={
            "task_id": task_id,
            "status": status_value,
            "progress": progress
        })
        
        return responses.TaskStatusResponse(
            task_id=task_id,
            status=status_value,
            progress=progress,
            created_at=created_at,
            updated_at=updated_at,
            result_url=f"/api/resumes/{task_id}/download" if status_value == "completed" else None
        )
    
    async def get_resume_text(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """Get the extracted text from a processed resume.
        
        Args:
            task_id: The task ID of the resume processing task
            
        Returns:
            Dict containing extracted text and metadata
            
        Raises:
            HTTPException: If task is not found or not completed
        """
        resume_data = await self.resume_service.get_resume_data(task_id)
        
        if not resume_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume task with ID {task_id} not found"
            )
        
        metadata = resume_data.get("metadata", {})
        status_value = metadata.get("status", "unknown")
        
        if status_value != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Resume processing is not complete. Current status: {status_value}"
            )
        
        extracted_text = resume_data.get("text", "")
        
        if not extracted_text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Extracted text not found"
            )
        
        logger.info(f"Retrieved resume text for task: {task_id}", extra={
            "task_id": task_id,
            "text_length": len(extracted_text)
        })
        
        return {
            "task_id": task_id,
            "text": extracted_text,
            "metadata": metadata
        }
