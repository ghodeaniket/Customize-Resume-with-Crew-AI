"""
API contract definitions for the Resume Customizer application.

This module defines Pydantic models that serve as contracts for the API requests and responses.
These models are used in contract tests to ensure API stability and backward compatibility.
"""
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ========================== Base Models ==========================

class BaseResponse(BaseModel):
    """Base model for all API responses."""
    model_config = ConfigDict(
        extra="forbid"  # Disallow extra fields to ensure strict contract validation
    )


class ErrorResponse(BaseResponse):
    """Model for error responses."""
    detail: str = Field(..., description="Error details message")


class TaskStatusBase(BaseResponse):
    """Base model for task status responses."""
    task_id: str = Field(..., description="Unique identifier for the task")
    status: str = Field(..., description="Current status of the task (processing, completed, failed)")
    progress: float = Field(..., description="Progress percentage (0-100)")
    created_at: Optional[str] = Field(None, description="Task creation timestamp")
    updated_at: Optional[str] = Field(None, description="Task last update timestamp")


# ========================== Request Models ==========================

class CustomizationRequest(BaseModel):
    """Model for resume customization requests."""
    resume_id: str = Field(..., description="ID of the resume to customize")
    job_description: str = Field(..., description="Job description to customize the resume for")
    customize_level: Optional[str] = Field("standard", description="Level of customization (minimal, standard, comprehensive)")
    
    @field_validator('job_description')
    @classmethod
    def job_description_not_empty(cls, v):
        """Validate that job description is not empty."""
        if not v or len(v.strip()) < 10:
            raise ValueError("Job description must not be empty and should be meaningful")
        return v


# ========================== Response Models ==========================

class HealthResponse(BaseResponse):
    """Model for health check response."""
    status: str = Field(..., description="API health status")


class ResumeUploadResponse(BaseResponse):
    """Model for resume upload response."""
    task_id: str = Field(..., description="Unique identifier for the upload task")
    filename: str = Field(..., description="Original filename of the uploaded resume")
    status: str = Field(..., description="Status of the upload task")


class TaskStatusResponse(TaskStatusBase):
    """Model for task status response."""
    result_url: Optional[str] = Field(None, description="URL to fetch the task result (if completed)")


class ResumeTextResponse(BaseResponse):
    """Model for resume text response."""
    task_id: str = Field(..., description="Task ID of the processed resume")
    text: str = Field(..., description="Extracted text from the resume")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")


class CustomizationResponse(BaseResponse):
    """Model for customization request response."""
    task_id: str = Field(..., description="Unique identifier for the customization task")
    status: str = Field(..., description="Status of the customization task")


class CustomizationResultResponse(BaseResponse):
    """Model for customization result response."""
    task_id: str = Field(..., description="Task ID of the customization")
    status: str = Field(..., description="Status of the customization task")
    result: Optional[str] = Field(None, description="Customized resume text")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
