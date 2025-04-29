"""Resume customization API endpoints."""
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, BackgroundTasks, HTTPException, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_document_processor, get_resume_service, get_document_storage_service
from app.core.exceptions import DocumentProcessingError, UnsupportedFileTypeError
from app.core.logging import logger
from app.core.utils.file_detection import is_supported_file_type
from app.infrastructure.document_processor import DocumentProcessor
from app.models.schemas import requests, responses
from app.services.resume_service import ResumeService
from app.services.document_storage_service import DocumentStorageService

router = APIRouter(prefix="/api/resumes", tags=["resumes"])

@router.post("/upload", response_model=responses.ResumeUploadResponse)
async def upload_resume(
    resume: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    document_processor: DocumentProcessor = Depends(get_document_processor),
    resume_service: ResumeService = Depends(get_resume_service),
    storage_service: DocumentStorageService = Depends(get_document_storage_service)
):
    """Upload a resume for processing.
    
    This endpoint accepts resume files in PDF, DOCX, or TXT formats.
    The file is processed asynchronously and the extracted text is stored
    for later retrieval and customization.
    
    Args:
        resume: The resume file to upload
        background_tasks: FastAPI background tasks manager
        document_processor: Document processor dependency
        resume_service: Resume service dependency
        storage_service: Document storage service dependency
        
    Returns:
        ResumeUploadResponse: Response with task ID and status
        
    Raises:
        HTTPException: If file validation fails
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
        # Read file content
        content = await resume.read()
        
        # Validate file size
        if len(content) > 10 * 1024 * 1024:  # 10 MB limit
            logger.warning(f"File too large: {len(content)} bytes", extra={
                "file_size": len(content),
                "error": "file_too_large"
            })
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large. Maximum size is 10 MB."
            )
        
        # Start document processing in background
        background_tasks.add_task(
            resume_service.process_resume,
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
        await storage_service.save_metadata(task_id, {
            "status": "failed",
            "error": str(e),
            "filename": resume.filename
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading resume: {str(e)}"
        )


@router.get("/{task_id}", response_model=responses.TaskStatusResponse)
async def get_resume_status(
    task_id: str,
    resume_service: ResumeService = Depends(get_resume_service)
):
    """Get the status of a resume processing task.
    
    Args:
        task_id: The task ID of the resume processing task
        resume_service: Resume service dependency
        
    Returns:
        TaskStatusResponse: Response with task status details
        
    Raises:
        HTTPException: If the task is not found
    """
    resume_data = await resume_service.get_resume_data(task_id)
    
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
    
    # Calculate progress based on status
    progress = 0.0
    if status_value == "completed":
        progress = 100.0
    elif status_value == "processing":
        progress = 50.0
    elif status_value == "failed":
        progress = 100.0
    
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


@router.get("/{task_id}/text", response_model=dict)
async def get_resume_text(
    task_id: str,
    resume_service: ResumeService = Depends(get_resume_service)
):
    """Get the extracted text from a processed resume.
    
    Args:
        task_id: The task ID of the resume processing task
        resume_service: Resume service dependency
        
    Returns:
        dict: The extracted text and metadata
        
    Raises:
        HTTPException: If the task is not found or processing is not complete
    """
    resume_data = await resume_service.get_resume_data(task_id)
    
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
