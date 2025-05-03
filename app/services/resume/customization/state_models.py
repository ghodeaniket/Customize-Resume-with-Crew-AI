"""State models for resume customization process."""
import time
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class JobAnalysisState(BaseModel):
    """State for job analysis phase of resume customization."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    job_description: str = ""
    analysis_result: str = ""
    required_skills: List[str] = Field(default_factory=list)
    required_experience: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    completed: bool = False
    error: Optional[str] = None


class ResumeOptimizationState(BaseModel):
    """State for resume optimization phase of customization."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    resume_text: str = ""
    optimized_resume: str = ""
    completed: bool = False
    error: Optional[str] = None


class CustomizationState(BaseModel):
    """Complete state for resume customization process."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    task_id: str
    resume_id: str
    customize_level: str = "standard"
    job_analysis: JobAnalysisState = Field(default_factory=JobAnalysisState)
    resume_optimization: ResumeOptimizationState = Field(default_factory=ResumeOptimizationState)
    status: str = "processing"
    progress: float = 0.0
    error_message: Optional[str] = None
    started_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
