"""Resume API route handlers with controller pattern."""
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse

from app.api.dependencies import (
    get_document_processor, 
    get_resume_service, 
    get_document_storage_service, 
    get_task_service
)
from app.api.controllers.resume_controller import ResumeController
from app.models.schemas import requests, responses
from app.services.resume_service import ResumeService
from app.services.task_service import TaskService
from app.services.document_storage_service import DocumentStorageService
from app.infrastructure.document_processor import DocumentProcessor

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


def get_resume_controller(
    resume_service: Annotated[ResumeService, Depends(get_resume_service)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
    storage_service: Annotated[DocumentStorageService, Depends(get_document_storage_service)],
    document_processor: Annotated[DocumentProcessor, Depends(get_document_processor)]
) -> ResumeController:
    """Get resume controller with injected dependencies."""
    return ResumeController(
        resume_service=resume_service,
        task_service=task_service,
        storage_service=storage_service,
        document_processor=document_processor
    )


@router.post("/upload", response_model=responses.ResumeUploadResponse)
async def upload_resume(
    resume: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    controller: Annotated[ResumeController, Depends(get_resume_controller)] = None
):
    """Upload a resume for processing.
    
    This endpoint accepts resume files in PDF, DOCX, or TXT formats.
    The file is processed asynchronously and the extracted text is stored
    for later retrieval and customization.
    
    Args:
        resume: The resume file to upload
        background_tasks: FastAPI background tasks manager
        controller: Resume controller dependency
        
    Returns:
        ResumeUploadResponse: Response with task ID and status
        
    Raises:
        HTTPException: If file validation fails
    """
    return await controller.upload_resume(resume, background_tasks)


@router.get("/{task_id}", response_model=responses.TaskStatusResponse)
async def get_resume_status(
    task_id: str,
    controller: Annotated[ResumeController, Depends(get_resume_controller)]
):
    """Get the status of a resume processing task.
    
    Args:
        task_id: The task ID of the resume processing task
        controller: Resume controller dependency
        
    Returns:
        TaskStatusResponse: Response with task status details
        
    Raises:
        HTTPException: If the task is not found
    """
    return await controller.get_resume_status(task_id)


@router.get("/{task_id}/text", response_model=dict)
async def get_resume_text(
    task_id: str,
    controller: Annotated[ResumeController, Depends(get_resume_controller)]
):
    """Get the extracted text from a processed resume.
    
    Args:
        task_id: The task ID of the resume processing task
        controller: Resume controller dependency
        
    Returns:
        dict: The extracted text and metadata
        
    Raises:
        HTTPException: If the task is not found or processing is not complete
    """
    return await controller.get_resume_text(task_id)


@router.post("/customize", response_model=responses.CustomizationResponse)
async def customize_resume(
    request: requests.CustomizationRequest,
    background_tasks: BackgroundTasks,
    controller: Annotated[ResumeController, Depends(get_resume_controller)]
):
    """Customize a resume based on a job description.
    
    This endpoint creates a customization task that tailors a previously 
    uploaded resume to match the provided job description. The customization
    is performed asynchronously, and the result can be retrieved using the
    returned task ID.
    
    Args:
        request: Customization request with resume ID and job description
        background_tasks: FastAPI background tasks manager
        controller: Resume controller dependency
        
    Returns:
        CustomizationResponse: Response with task ID and status
        
    Raises:
        HTTPException: If resume validation fails
    """
    return await controller.customize_resume(request, background_tasks)


@router.get("/customization/{task_id}", response_model=responses.TaskStatusResponse)
async def get_customization_status(
    task_id: str,
    controller: Annotated[ResumeController, Depends(get_resume_controller)]
):
    """Get the status of a resume customization task.
    
    Args:
        task_id: The task ID of the customization task
        controller: Resume controller dependency
        
    Returns:
        TaskStatusResponse: Response with task status details
        
    Raises:
        HTTPException: If the task is not found
    """
    return await controller.get_customization_status(task_id)


@router.get("/customization/{task_id}/result", response_model=dict)
async def get_customization_result(
    task_id: str,
    controller: Annotated[ResumeController, Depends(get_resume_controller)]
):
    """Get the result of a completed customization task.
    
    Args:
        task_id: The task ID of the customization task
        controller: Resume controller dependency
        
    Returns:
        dict: The customized resume text and metadata
        
    Raises:
        HTTPException: If the task is not found or not completed
    """
    return await controller.get_customization_result(task_id)
