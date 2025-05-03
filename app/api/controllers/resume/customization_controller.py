"""Controller for resume customization operations."""
from typing import Dict, Any
from fastapi import HTTPException, status, BackgroundTasks

from app.core.logging import logger
from app.models.schemas import requests, responses
from app.api.controllers.resume.base_controller import BaseResumeController


class ResumeCustomizationController(BaseResumeController):
    """Controller for handling resume customization operations."""
    
    async def customize_resume(
        self,
        request: requests.CustomizationRequest,
        background_tasks: BackgroundTasks
    ) -> responses.CustomizationResponse:
        """Create a resume customization task.
        
        Args:
            request: Customization request details
            background_tasks: FastAPI background tasks manager
            
        Returns:
            CustomizationResponse: Task ID and status
            
        Raises:
            HTTPException: On validation errors
        """
        # Validate resume exists
        await self._validate_resume_exists(request.resume_id)
        
        # Validate job description
        self._validate_job_description(request.job_description)
        
        # Create task
        task = await self.task_service.create_task(
            task_type="resume_customization",
            related_id=request.resume_id
        )
        task_id = task["task_id"]
        
        # Start customization in background
        background_tasks.add_task(
            self.resume_service.customize_resume,
            resume_id=request.resume_id,
            job_description=request.job_description,
            task_id=task_id,
            customize_level=request.customize_level or "standard"
        )
        
        logger.info(
            f"Started resume customization: resume={request.resume_id}, "
            f"task={task_id}, level={request.customize_level or 'standard'}", 
            extra={
                "resume_id": request.resume_id,
                "task_id": task_id,
                "customize_level": request.customize_level or "standard",
                "job_description_length": len(request.job_description)
            }
        )
        
        return responses.CustomizationResponse(
            task_id=task_id,
            status="processing"
        )
    
    async def get_customization_status(
        self,
        task_id: str
    ) -> responses.TaskStatusResponse:
        """Get the status of a customization task.
        
        Args:
            task_id: The task ID of the customization task
            
        Returns:
            TaskStatusResponse: Task status details
            
        Raises:
            HTTPException: If task is not found
        """
        task = await self._validate_task_exists(task_id)
        
        status_value = task.get("status", "unknown")
        progress = task.get("progress", 0.0)
        created_at = task.get("created_at", "")
        updated_at = task.get("updated_at", "")
        
        result_url = None
        if status_value == "completed":
            result_url = f"/api/resumes/customization/{task_id}/result"
        
        logger.info(f"Retrieved customization task status: {task_id}, status: {status_value}", extra={
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
            result_url=result_url
        )
    
    async def get_customization_result(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """Get the result of a completed customization task.
        
        Args:
            task_id: The task ID of the customization task
            
        Returns:
            Dict containing customization result
            
        Raises:
            HTTPException: If task is not found or not completed
        """
        result = await self.resume_service.get_customization_result(task_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customization task with ID {task_id} not found"
            )
        
        if result.get("status") != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Customization is not complete. "
                    f"Current status: {result.get('status')}, "
                    f"Progress: {result.get('progress', 0)}%"
                )
            )
        
        logger.info(f"Retrieved customization result for task: {task_id}", extra={
            "task_id": task_id,
            "result_length": len(result.get("result", ""))
        })
        
        return result
