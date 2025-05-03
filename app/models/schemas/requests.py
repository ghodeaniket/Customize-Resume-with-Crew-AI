"""Request schemas for the API with enhanced validation."""
from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class CustomizationRequest(BaseModel):
    """Request model for resume customization."""
    
    resume_id: str = Field(
        ..., 
        description="The ID of the uploaded resume to customize",
        min_length=1,
        max_length=100
    )
    job_description: str = Field(
        ..., 
        description="The job description to tailor the resume for",
        min_length=10,
        max_length=50000
    )
    customize_level: Optional[str] = Field(
        "standard",
        description="Customization level (minimal, standard, comprehensive)",
        pattern="^(minimal|standard|comprehensive)$"
    )
    industry: Optional[str] = Field(
        None,
        description="Target industry for optimized terminology",
        max_length=100
    )
    keywords: Optional[List[str]] = Field(
        None,
        description="Additional keywords to emphasize",
        max_length=20  # Changed from max_items to max_length
    )
    preferences: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional customization preferences"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "resume_id": "550e8400-e29b-41d4-a716-446655440000",
                "job_description": "We are looking for a Python developer with FastAPI experience...",
                "customize_level": "standard",
                "industry": "Technology",
                "keywords": ["Python", "FastAPI", "Docker"],
                "preferences": {
                    "emphasize_remote_work": True,
                    "highlight_leadership": False
                }
            }
        }
    )
    
    @field_validator('job_description')
    @classmethod
    def validate_job_description(cls, v: str) -> str:
        """Validate job description has meaningful content."""
        # Remove whitespace and check length
        cleaned = ' '.join(v.split())
        if len(cleaned) < 10:
            raise ValueError("Job description must contain at least 10 characters of meaningful text")
        return cleaned
    
    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and clean keywords."""
        if v is None:
            return v
        
        # Remove duplicates and empty strings
        cleaned = list(set(k.strip() for k in v if k.strip()))
        
        # Limit length of each keyword
        for keyword in cleaned:
            if len(keyword) > 50:
                raise ValueError(f"Keyword too long: {keyword[:50]}...")
        
        return cleaned


class ResumeAnalysisRequest(BaseModel):
    """Request model for resume analysis."""
    
    resume_id: str = Field(
        ..., 
        description="The ID of the resume to analyze",
        min_length=1,
        max_length=100
    )
    analysis_type: Optional[str] = Field(
        "comprehensive",
        description="Type of analysis to perform (basic, comprehensive, ats)",
        pattern="^(basic|comprehensive|ats)$"
    )
    target_role: Optional[str] = Field(
        None,
        description="Target role for role-specific analysis",
        max_length=100
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "resume_id": "550e8400-e29b-41d4-a716-446655440000",
                "analysis_type": "comprehensive",
                "target_role": "Senior Software Engineer"
            }
        }
    )


class PaginationParams(BaseModel):
    """Common pagination parameters."""
    
    page: int = Field(
        1,
        description="Page number",
        ge=1,
        le=10000
    )
    page_size: int = Field(
        10,
        description="Number of items per page",
        ge=1,
        le=100
    )
    sort_by: Optional[str] = Field(
        None,
        description="Field to sort by",
        max_length=50
    )
    sort_order: Optional[str] = Field(
        "desc",
        description="Sort order (asc/desc)",
        pattern="^(asc|desc)$"
    )


class FilterParams(BaseModel):
    """Common filter parameters."""
    
    created_after: Optional[datetime] = Field(
        None,
        description="Filter by creation date after"
    )
    created_before: Optional[datetime] = Field(
        None,
        description="Filter by creation date before"
    )
    status: Optional[List[str]] = Field(
        None,
        description="Filter by status values",
        max_length=10  # Changed from max_items to max_length
    )
    
    @model_validator(mode='after')
    def validate_date_range(self) -> 'FilterParams':
        """Validate date range if both dates are provided."""
        if self.created_after and self.created_before:
            if self.created_after >= self.created_before:
                raise ValueError("created_after must be before created_before")
        return self


class TaskListRequest(BaseModel):
    """Request model for listing tasks."""
    
    task_type: Optional[str] = Field(
        None,
        description="Filter by task type",
        pattern="^(resume_processing|resume_customization|resume_analysis)$"
    )
    pagination: Optional[PaginationParams] = Field(
        default_factory=PaginationParams,
        description="Pagination parameters"
    )
    filters: Optional[FilterParams] = Field(
        default_factory=FilterParams,
        description="Filter parameters"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_type": "resume_customization",
                "pagination": {
                    "page": 1,
                    "page_size": 20
                },
                "filters": {
                    "status": ["completed", "processing"],
                    "created_after": "2024-01-01T00:00:00Z"
                }
            }
        }
    )


class BatchStatusRequest(BaseModel):
    """Request model for batch status check."""
    
    task_ids: List[str] = Field(
        ...,
        description="List of task IDs to check status for",
        min_length=1,  # Changed from min_items to min_length
        max_length=50  # Changed from max_items to max_length
    )
    include_metadata: bool = Field(
        False,
        description="Whether to include full metadata for each task"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_ids": [
                    "550e8400-e29b-41d4-a716-446655440001",
                    "550e8400-e29b-41d4-a716-446655440002"
                ],
                "include_metadata": True
            }
        }
    )
    
    @field_validator('task_ids')
    @classmethod
    def validate_task_ids(cls, v: List[str]) -> List[str]:
        """Validate task IDs format and remove duplicates."""
        # Remove duplicates
        unique_ids = list(set(v))
        
        # Validate format (basic UUID validation)
        import re
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
        
        for task_id in unique_ids:
            if not uuid_pattern.match(task_id):
                raise ValueError(f"Invalid task ID format: {task_id}")
        
        return unique_ids
