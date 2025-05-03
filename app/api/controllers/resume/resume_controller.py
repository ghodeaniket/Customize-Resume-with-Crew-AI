"""Unified resume controller that combines all sub-controllers."""
from typing import Dict, Any
from fastapi import HTTPException, status, UploadFile, BackgroundTasks

from app.models.schemas import requests, responses
from app.api.controllers.resume.upload_controller import ResumeUploadController
from app.api.controllers.resume.result_controller import ResumeResultController
from app.api.controllers.resume.customization_controller import ResumeCustomizationController


class UnifiedResumeController:
    """Unified controller that combines all resume operations."""
    
    def __init__(
        self,
        resume_service,
        task_service,
        storage_service,
        document_processor
    ):
        """Initialize with shared dependencies."""
        # Initialize sub-controllers
        self.upload_controller = ResumeUploadController(
            resume_service, task_service, storage_service, document_processor
        )
        self.result_controller = ResumeResultController(
            resume_service, task_service, storage_service, document_processor
        )
        self.customization_controller = ResumeCustomizationController(
            resume_service, task_service, storage_service, document_processor
        )
    
    # Upload operations
    async def upload_resume(
        self, resume: UploadFile, background_tasks: BackgroundTasks
    ) -> responses.ResumeUploadResponse:
        """Handle resume upload."""
        return await self.upload_controller.upload_resume(resume, background_tasks)
    
    # Result operations  
    async def get_resume_status(self, task_id: str) -> responses.TaskStatusResponse:
        """Get the status of a resume processing task."""
        return await self.result_controller.get_resume_status(task_id)
    
    async def get_resume_text(self, task_id: str) -> Dict[str, Any]:
        """Get the extracted text from a processed resume."""
        return await self.result_controller.get_resume_text(task_id)
    
    # Customization operations
    async def customize_resume(
        self, request: requests.CustomizationRequest, background_tasks: BackgroundTasks
    ) -> responses.CustomizationResponse:
        """Create a resume customization task."""
        return await self.customization_controller.customize_resume(request, background_tasks)
    
    async def get_customization_status(self, task_id: str) -> responses.TaskStatusResponse:
        """Get the status of a customization task."""
        return await self.customization_controller.get_customization_status(task_id)
    
    async def get_customization_result(self, task_id: str) -> Dict[str, Any]:
        """Get the result of a completed customization task."""
        return await self.customization_controller.get_customization_result(task_id)
