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


@router.post("/customize", response_model=responses.CustomizationResponse)
async def customize_resume(
    request: requests.CustomizationRequest,
    background_tasks: BackgroundTasks,
    resume_service: ResumeService = Depends(get_resume_service),
    task_service: TaskService = Depends(get_task_service)
):
    """Customize a resume based on a job description.
    
    This endpoint creates a customization task that tailors a previously 
    uploaded resume to match the provided job description. The customization
    is performed asynchronously, and the result can be retrieved using the
    returned task ID.
    
    Args:
        request: Customization request with resume ID and job description
        background_tasks: FastAPI background tasks manager
        resume_service: Resume service dependency
        task_service: Task service dependency
        
    Returns:
        CustomizationResponse: Response with task ID and status
        
    Raises:
        HTTPException: If resume validation fails
    """
    # Validate resume ID
    if not await resume_service.resume_exists(request.resume_id):
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
    
    # Create customization task
    task = await task_service.create_task(
        task_type="resume_customization",
        related_id=request.resume_id
    )
    task_id = task["task_id"]
    
    # Start customization in background
    background_tasks.add_task(
        resume_service.customize_resume,
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


@router.get("/customization/{task_id}", response_model=responses.TaskStatusResponse)
async def get_customization_status(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
):
    """Get the status of a resume customization task.
    
    Args:
        task_id: The task ID of the customization task
        task_service: Task service dependency
        
    Returns:
        TaskStatusResponse: Response with task status details
        
    Raises:
        HTTPException: If the task is not found
    """
    task = await task_service.get_task(task_id)
    
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


@router.get("/customization/{task_id}/result", response_model=dict)
async def get_customization_result(
    task_id: str,
    resume_service: ResumeService = Depends(get_resume_service)
):
    """Get the result of a completed customization task.
    
    Args:
        task_id: The task ID of the customization task
        resume_service: Resume service dependency
        
    Returns:
        dict: The customized resume text and metadata
        
    Raises:
        HTTPException: If the task is not found or not completed
    """
    result = await resume_service.get_customization_result(task_id)
    
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
