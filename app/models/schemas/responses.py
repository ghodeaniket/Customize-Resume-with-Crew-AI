"""Response schemas for the API with enhanced structure and validation."""
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Generic, TypeVar

from pydantic import BaseModel, Field, ConfigDict, field_validator


T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """Base response model for all API responses."""
    
    success: bool = Field(default=True, description="Indicates if the request was successful")
    data: Optional[T] = Field(default=None, description="Response payload")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Error details if any")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "data": {},
                "error": None,
                "meta": {"timestamp": "2025-05-03T00:00:00Z"}
            }
        }
    )


class ErrorDetail(BaseModel):
    """Model for error details."""
    
    code: str = Field(..., description="Error code for client handling")
    message: str = Field(..., description="Human-readable error message")
    error_id: str = Field(..., description="Unique error ID for tracking")
    path: str = Field(..., description="API path where error occurred")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    suggestion: Optional[str] = Field(None, description="Suggestion for fixing the error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ResumeUploadData(BaseModel):
    """Response data for resume upload."""
    
    task_id: str = Field(..., description="Unique identifier for the uploaded resume task")
    filename: str = Field(..., description="Original filename of the uploaded resume")
    status: str = Field(..., description="Status of the upload (processing, completed, failed)")
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")


class ResumeUploadResponse(BaseResponse[ResumeUploadData]):
    """Response model for resume upload."""
    pass


class CustomizationData(BaseModel):
    """Response data for resume customization request."""
    
    task_id: str = Field(..., description="Unique identifier for the customization task")
    status: str = Field(..., description="Status of the customization task")
    customization_level: str = Field(..., description="Level of customization requested")
    estimated_completion_time: Optional[int] = Field(None, description="Estimated time to completion in seconds")


class CustomizationResponse(BaseResponse[CustomizationData]):
    """Response model for resume customization request."""
    pass


class TaskStatusData(BaseModel):
    """Response data for task status."""
    
    task_id: str = Field(..., description="Unique identifier for the task")
    status: str = Field(..., description="Current status of the task")
    progress: float = Field(..., description="Progress percentage of the task", ge=0, le=100)
    created_at: Union[datetime, str] = Field(..., description="Time when the task was created")
    updated_at: Union[datetime, str] = Field(..., description="Time when the task was last updated")
    result_url: Optional[str] = Field(None, description="URL to download the result if available")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    message: Optional[str] = Field(None, description="Status message")
    
    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
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


class TaskStatusResponse(BaseResponse[TaskStatusData]):
    """Response model for task status."""
    pass


class ResumeAnalysisData(BaseModel):
    """Response data for resume analysis."""
    
    resume_id: str = Field(..., description="Unique identifier for the resume")
    skills: List[str] = Field(..., description="Skills extracted from the resume")
    experience: List[Dict[str, Any]] = Field(..., description="Experience extracted from the resume")
    education: List[Dict[str, Any]] = Field(..., description="Education extracted from the resume")
    metrics: Dict[str, Any] = Field(..., description="Metrics and statistics about the resume")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")


class ResumeAnalysisResponse(BaseResponse[ResumeAnalysisData]):
    """Response model for resume analysis."""
    pass


class ExtractedTextData(BaseModel):
    """Response data for extracted text."""
    
    task_id: str = Field(..., description="Unique identifier for the task")
    text: str = Field(..., description="Extracted text content")
    metadata: Dict[str, Any] = Field(..., description="Metadata about the extraction")
    word_count: int = Field(..., description="Word count of extracted text")
    character_count: int = Field(..., description="Character count of extracted text")


class ExtractedTextResponse(BaseResponse[ExtractedTextData]):
    """Response model for extracted text."""
    pass


class CustomizationResultData(BaseModel):
    """Response data for customization result."""
    
    task_id: str = Field(..., description="Unique identifier for the customization task")
    original_resume_id: str = Field(..., description="ID of the original resume")
    customized_text: str = Field(..., description="Customized resume text")
    customization_level: str = Field(..., description="Level of customization applied")
    changes_summary: Dict[str, Any] = Field(..., description="Summary of changes made")
    optimization_metrics: Dict[str, Any] = Field(..., description="Metrics about the optimization")
    completion_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")


class CustomizationResultResponse(BaseResponse[CustomizationResultData]):
    """Response model for customization result."""
    pass


class HealthCheckData(BaseModel):
    """Response data for health check."""
    
    status: str = Field(..., description="Health status (healthy/unhealthy)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Current environment")
    checks: Dict[str, Dict[str, Any]] = Field(..., description="Individual health check results")


class HealthCheckResponse(BaseResponse[HealthCheckData]):
    """Response model for health check."""
    pass


class PaginationMeta(BaseModel):
    """Metadata for pagination."""
    
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    current_page: int = Field(..., description="Current page number")
    items_per_page: int = Field(..., description="Number of items per page")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseResponse[List[T]], Generic[T]):
    """Base response model for paginated results."""
    
    meta: Optional[PaginationMeta] = Field(None, description="Pagination metadata")


# Backward compatibility aliases
ResumeUploadResponse = ResumeUploadData
CustomizationResponse = CustomizationData
TaskStatusResponse = TaskStatusData
ResumeAnalysisResponse = ResumeAnalysisData
ExtractedTextResponse = ExtractedTextData
