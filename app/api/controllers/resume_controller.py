"""Resume operations controller with business logic separated from routes."""
import uuid
from typing import Dict, Any, Annotated
from fastapi import HTTPException, status, UploadFile, BackgroundTasks

from app.core.logging import logger
from app.core.exceptions import (
    DocumentProcessingError, 
    UnsupportedFileTypeError,
    ResumeNotFoundError,
    TaskNotFoundError,
    CustomizationError
)
from app.core.utils.file_detection import is_supported_file_type
from app.models.schemas import requests, responses
from app.services.resume_service import ResumeService
from app.services.task_service import TaskService
from app.services.document_storage_service import DocumentStorageService
from app.infrastructure.document_processor import DocumentProcessor


class ResumeController:
    """Controller for resume-related operations."""
    
    def __init__(
        self,
        resume_service: ResumeService,
        task_service: TaskService,
        storage_service: DocumentStorageService,
        document_processor: DocumentProcessor
    ):
        """Initialize the resume controller with dependencies."""
        self.resume_service = resume_service
        self.task_service = task_service
        self.storage_service = storage_service
        self.document_processor = document_processor
    
    async def upload_resume(
        self,
        resume: UploadFile,
        background_tasks: BackgroundTasks
    ) -> responses.ResumeUploadResponse:
        """Handle resume upload with validation and processing.
        
        Args:
            resume: The uploaded resume file
            background_tasks: FastAPI background tasks manager
            
        Returns:
            ResumeUploadResponse: Response with task ID and status
            
        Raises:
            HTTPException: On validation or processing errors
        """
        # Validate file type
        if not is_supported_file_type(resume.filename):
            logger.warning(f"Unsupported file type: {resume.filename}", extra={
                "filename": resume.filename,
                "error": "unsupported_file_type"
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Unsupported file type. Please upload PDF, DOCX, or TXT files."
            )
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        try:
            # Read and validate file content
            content = await resume.read()
            
            # Validate file size (10 MB limit)
            if len(content) > 10 * 1024 * 1024:
                logger.warning(f"File too large: {len(content)} bytes", extra={
                    "file_size": len(content),
                    "error": "file_too_large"
                })
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File too large. Maximum size is 10 MB."
                )
            
            # Start processing in background
            background_tasks.add_task(
                self.resume_service.process_resume,
                file_content=content,
                filename=resume.filename,
                task_id=task_id
            )
            
            logger.info(f"Resume upload accepted: {resume.filename}, task: {task_id}", extra={
                "task_id": task_id,
                "filename": resume.filename,
                "file_size": len(content),
                "status": "processing"
            })
            
            return responses.ResumeUploadResponse(
                task_id=task_id,
                filename=resume.filename,
                status="processing"
            )
            
        except Exception as e:
            logger.error(f"Error uploading resume: {str(e)}", exc_info=True, extra={
                "filename": resume.filename,
                "error": str(e)
            })
            
            # Save error metadata
            await self.storage_service.save_metadata(task_id, {
                "status": "failed",
                "error": str(e),
                "filename": resume.filename
            })
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading resume: {str(e)}"
            )
    
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
        if not await self.resume_service.resume_exists(request.resume_id):
            logger.warning(f"Resume not found: {request.resume_id}", extra={
                "resume_id": request.resume_id,
                "error": "resume_not_found"
            })
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Resume with ID {request.resume_id} not found"
            )
        
        # Validate job description
        if not request.job_description or len(request.job_description) < 10:
            logger.warning("Job description too short", extra={
                "error": "invalid_job_description",
                "length": len(request.job_description) if request.job_description else 0
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description is too short or empty"
            )
        
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
        task = await self.task_service.get_task(task_id)
        
        if not task:
            logger.warning(f"Customization task not found: {task_id}", extra={
                "task_id": task_id,
                "error": "task_not_found"
            })
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customization task with ID {task_id} not found"
            )
        
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
