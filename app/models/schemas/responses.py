"""Response schemas for the API."""
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class ResumeUploadResponse(BaseModel):
    """Response model for resume upload."""
    
    task_id: str = Field(..., description="Unique identifier for the uploaded resume task")
    filename: str = Field(..., description="Original filename of the uploaded resume")
    status: str = Field(..., description="Status of the upload (processing, completed, failed)")


class CustomizationResponse(BaseModel):
    """Response model for resume customization request."""
    
    task_id: str = Field(..., description="Unique identifier for the customization task")
    status: str = Field(..., description="Status of the customization task")


class TaskStatusResponse(BaseModel):
    """Response model for task status."""
    
    task_id: str = Field(..., description="Unique identifier for the task")
    status: str = Field(..., description="Current status of the task")
    progress: float = Field(..., description="Progress percentage of the task")
    created_at: datetime = Field(..., description="Time when the task was created")
    updated_at: datetime = Field(..., description="Time when the task was last updated")
    result_url: Optional[str] = Field(None, description="URL to download the result if available")


class ResumeAnalysisResponse(BaseModel):
    """Response model for resume analysis."""
    
    resume_id: str = Field(..., description="Unique identifier for the resume")
    skills: List[str] = Field(..., description="Skills extracted from the resume")
    experience: List[Dict[str, Any]] = Field(..., description="Experience extracted from the resume")
    education: List[Dict[str, Any]] = Field(..., description="Education extracted from the resume")
    metrics: Dict[str, Any] = Field(..., description="Metrics and statistics about the resume")
