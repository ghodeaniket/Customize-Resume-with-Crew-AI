"""Pydantic state models for resume customization flows.

This module contains the state models used for managing the resume customization
process with CrewAI Flows. Each model represents a specific state in the workflow
and includes validation rules for state transitions.
"""
from enum import Enum
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

# Define enums for constrained values
class JobAnalysisStatus(str, Enum):
    """Status of job analysis process."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ResumeOptimizationStatus(str, Enum):
    """Status of resume optimization process."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CustomizationLevel(str, Enum):
    """Level of resume customization to apply."""
    MINIMAL = "minimal"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class TaskStatus(str, Enum):
    """Overall status of the customization task."""
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Component state models for hierarchical state composition
class DocumentInfo(BaseModel):
    """Information about a document (resume or job description)."""
    document_id: str = Field(..., description="Unique identifier for the document")
    filename: Optional[str] = Field(None, description="Original filename")
    content: Optional[str] = Field(None, description="Document content (text)")
    content_path: Optional[str] = Field(None, description="Path to document content on disk")
    size_bytes: Optional[int] = Field(None, description="Size of document in bytes")
    extracted_at: Optional[datetime] = Field(None, description="When text was extracted")
    
    def has_content(self) -> bool:
        """Check if document has available content."""
        return bool(self.content) or bool(self.content_path)


class JobAnalysisState(BaseModel):
    """State for job description analysis process."""
    status: JobAnalysisStatus = Field(default=JobAnalysisStatus.PENDING)
    job_description: Optional[DocumentInfo] = Field(None, description="Job description document info")
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    required_experience: Dict[str, Any] = Field(default_factory=dict)
    education_requirements: List[str] = Field(default_factory=list)
    job_title: Optional[str] = Field(None)
    seniority_level: Optional[str] = Field(None)
    keywords: List[str] = Field(default_factory=list)
    analysis_result: Optional[str] = Field(None, description="Full analysis result")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
    
    def is_ready_for_analysis(self) -> bool:
        """Check if job description is ready for analysis."""
        return (self.job_description is not None and 
                self.job_description.has_content() and 
                self.status in [JobAnalysisStatus.PENDING, JobAnalysisStatus.FAILED])
    
    def is_analysis_complete(self) -> bool:
        """Check if job analysis is complete and successful."""
        return self.status == JobAnalysisStatus.COMPLETED and self.analysis_result is not None


class ResumeOptimizationState(BaseModel):
    """State for resume optimization process."""
    status: ResumeOptimizationStatus = Field(default=ResumeOptimizationStatus.PENDING)
    resume: Optional[DocumentInfo] = Field(None, description="Resume document info")
    customization_level: CustomizationLevel = Field(default=CustomizationLevel.STANDARD)
    optimized_resume: Optional[str] = Field(None, description="Optimized resume content")
    ats_score_before: Optional[float] = Field(None, description="ATS match score before optimization")
    ats_score_after: Optional[float] = Field(None, description="ATS match score after optimization")
    error_message: Optional[str] = Field(None, description="Error message if optimization failed")
    
    def is_ready_for_optimization(self, job_analysis_complete: bool) -> bool:
        """Check if resume is ready for optimization.
        
        Args:
            job_analysis_complete: Whether job analysis is complete
            
        Returns:
            bool: True if ready for optimization
        """
        return (self.resume is not None and 
                self.resume.has_content() and 
                job_analysis_complete and
                self.status in [ResumeOptimizationStatus.PENDING, ResumeOptimizationStatus.FAILED])
    
    def is_optimization_complete(self) -> bool:
        """Check if resume optimization is complete and successful."""
        return (self.status == ResumeOptimizationStatus.COMPLETED and 
                self.optimized_resume is not None)


# Main state model for the entire flow
class ResumeCustomizationState(BaseModel):
    """State for the resume customization flow."""
    model_config = ConfigDict(
        extra="allow",  # Allow extra fields for flexibility and forward-compatibility
    )
    
    # Task metadata
    task_id: str = Field(..., description="Unique identifier for the task")
    status: TaskStatus = Field(default=TaskStatus.CREATED)
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage (0-100)")
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    processing_time_ms: Optional[float] = Field(None)
    error_message: Optional[str] = Field(None)
    
    # Component states
    job_analysis: JobAnalysisState = Field(default_factory=JobAnalysisState)
    resume_optimization: ResumeOptimizationState = Field(default_factory=ResumeOptimizationState)
    
    # Validation
    @field_validator("progress")
    @classmethod
    def validate_progress(cls, value: float) -> float:
        """Validate progress is between 0 and 100."""
        if value < 0.0 or value > 100.0:
            raise ValueError("Progress must be between 0 and 100")
        return round(value, 1)  # Round to 1 decimal place
    
    def update_progress(self) -> None:
        """Update overall progress based on component states."""
        # Calculate weighted progress based on component states
        job_analysis_weight = 0.4  # 40% of the overall progress
        resume_optimization_weight = 0.6  # 60% of the overall progress
        
        job_analysis_progress = 0.0
        if self.job_analysis.status == JobAnalysisStatus.PENDING:
            job_analysis_progress = 0.0
        elif self.job_analysis.status == JobAnalysisStatus.IN_PROGRESS:
            job_analysis_progress = 50.0
        elif self.job_analysis.status == JobAnalysisStatus.COMPLETED:
            job_analysis_progress = 100.0
        elif self.job_analysis.status == JobAnalysisStatus.FAILED:
            job_analysis_progress = 100.0  # Consider failed as "complete" for progress purposes
        
        resume_optimization_progress = 0.0
        if self.resume_optimization.status == ResumeOptimizationStatus.PENDING:
            resume_optimization_progress = 0.0
        elif self.resume_optimization.status == ResumeOptimizationStatus.IN_PROGRESS:
            resume_optimization_progress = 50.0
        elif self.resume_optimization.status == ResumeOptimizationStatus.COMPLETED:
            resume_optimization_progress = 100.0
        elif self.resume_optimization.status == ResumeOptimizationStatus.FAILED:
            resume_optimization_progress = 100.0  # Consider failed as "complete" for progress purposes
        
        # Calculate weighted progress
        self.progress = (
            job_analysis_weight * job_analysis_progress +
            resume_optimization_weight * resume_optimization_progress
        )
        
        # Update overall task status based on component states
        self._update_task_status()
    
    def _update_task_status(self) -> None:
        """Update task status based on component states."""
        # Check for failure cases first
        if (self.job_analysis.status == JobAnalysisStatus.FAILED or
                self.resume_optimization.status == ResumeOptimizationStatus.FAILED):
            self.status = TaskStatus.FAILED
            # Collect error messages
            error_messages = []
            if self.job_analysis.error_message:
                error_messages.append(f"Job analysis: {self.job_analysis.error_message}")
            if self.resume_optimization.error_message:
                error_messages.append(f"Resume optimization: {self.resume_optimization.error_message}")
            self.error_message = " ".join(error_messages) if error_messages else "Task failed"
            return
        
        # Check for completion
        if (self.job_analysis.status == JobAnalysisStatus.COMPLETED and
                self.resume_optimization.status == ResumeOptimizationStatus.COMPLETED):
            self.status = TaskStatus.COMPLETED
            if not self.completed_at:
                self.completed_at = datetime.now()
            return
        
        # If any component is in progress, the task is in progress
        if (self.job_analysis.status == JobAnalysisStatus.IN_PROGRESS or
                self.resume_optimization.status == ResumeOptimizationStatus.IN_PROGRESS):
            self.status = TaskStatus.PROCESSING
            if not self.started_at:
                self.started_at = datetime.now()
            return
        
        # Default case (pending components)
        self.status = TaskStatus.PROCESSING if self.progress > 0.0 else TaskStatus.CREATED
