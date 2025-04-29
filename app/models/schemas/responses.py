"""Response schemas for the API."""
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field, validator


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
    created_at: Union[datetime, str] = Field(..., description="Time when the task was created")
    updated_at: Union[datetime, str] = Field(..., description="Time when the task was last updated")
    result_url: Optional[str] = Field(None, description="URL to download the result if available")
    
    @validator('created_at', 'updated_at', pre=True)
    def parse_datetime(cls, value):
        """Parse datetime string or timestamp to datetime object."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        if not value:
            return datetime.now()
        # Leave as string if we can't parse it
        return value


class ResumeAnalysisResponse(BaseModel):
    """Response model for resume analysis."""
    
    resume_id: str = Field(..., description="Unique identifier for the resume")
    skills: List[str] = Field(..., description="Skills extracted from the resume")
    experience: List[Dict[str, Any]] = Field(..., description="Experience extracted from the resume")
    education: List[Dict[str, Any]] = Field(..., description="Education extracted from the resume")
    metrics: Dict[str, Any] = Field(..., description="Metrics and statistics about the resume")


class ExtractedTextResponse(BaseModel):
    """Response model for extracted text."""
    
    task_id: str = Field(..., description="Unique identifier for the task")
    text: str = Field(..., description="Extracted text content")
    metadata: Dict[str, Any] = Field(..., description="Metadata about the extraction")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    
    detail: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    path: Optional[str] = Field(None, description="Path that caused the error")
