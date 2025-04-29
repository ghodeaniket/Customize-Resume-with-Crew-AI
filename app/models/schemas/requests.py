"""Request schemas for the API."""
from typing import Optional

from pydantic import BaseModel, Field


class CustomizationRequest(BaseModel):
    """Request model for resume customization."""
    
    resume_id: str = Field(..., description="The ID of the uploaded resume to customize")
    job_description: str = Field(
        ..., description="The job description to tailor the resume for"
    )
    customize_level: Optional[str] = Field(
        "standard",
        description="Customization level (minimal, standard, comprehensive)",
    )
