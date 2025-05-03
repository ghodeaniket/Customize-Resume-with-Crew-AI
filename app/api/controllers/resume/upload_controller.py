"""Controller for resume upload operations."""
import uuid
from fastapi import HTTPException, status, UploadFile, BackgroundTasks

from app.core.logging import logger
from app.core.utils.file_detection import is_supported_file_type
from app.models.schemas import responses
from app.api.controllers.resume.base_controller import BaseResumeController


class ResumeUploadController(BaseResumeController):
    """Controller for handling resume uploads."""
    
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
