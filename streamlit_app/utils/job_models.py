"""Data models for job description customization."""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set
from datetime import datetime


class JobDescriptionValidationError(Exception):
    """Exception raised when job description validation fails."""
    pass


class CustomizationRequestError(Exception):
    """Exception raised when customization request fails."""
    pass


class CustomizationStatusError(Exception):
    """Exception raised when customization status check fails."""
    pass


class CustomizationResultError(Exception):
    """Exception raised when retrieving customization result fails."""
    pass


@dataclass
class JobDescriptionValidationResult:
    """Result of job description validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    character_count: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobDescriptionValidationResult':
        """Create a result object from a dictionary."""
        return cls(
            is_valid=data.get('is_valid', False),
            errors=data.get('errors', []),
            warnings=data.get('warnings', []),
            suggestions=data.get('suggestions', []),
            character_count=data.get('character_count', 0)
        )


@dataclass
class CustomizationRequest:
    """Request data for resume customization API."""
    resume_id: str
    job_description: str
    customize_level: str = "standard"
    industry: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        request_dict = {
            "resume_id": self.resume_id,
            "job_description": self.job_description,
            "customize_level": self.customize_level
        }
        
        if self.industry:
            request_dict["industry"] = self.industry
            
        if self.keywords:
            request_dict["keywords"] = self.keywords
            
        return request_dict


@dataclass
class CustomizationResponse:
    """Response data for customization request API."""
    task_id: str
    status: str
    customization_level: str
    estimated_completion_time: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomizationResponse':
        """Create a response object from a dictionary."""
        return cls(
            task_id=data.get('task_id', ''),
            status=data.get('status', ''),
            customization_level=data.get('customization_level', 'standard'),
            estimated_completion_time=data.get('estimated_completion_time')
        )


@dataclass
class CustomizationStatusResponse:
    """Response data for customization status API."""
    task_id: str
    status: str
    progress: float
    resume_id: str
    message: Optional[str] = None
    processing_time_ms: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomizationStatusResponse':
        """Create a response object from a dictionary."""
        return cls(
            task_id=data.get('task_id', ''),
            status=data.get('status', ''),
            progress=data.get('progress', 0.0),
            resume_id=data.get('resume_id', ''),
            message=data.get('message'),
            processing_time_ms=data.get('processing_time_ms')
        )


@dataclass
class CustomizationResultResponse:
    """Response data for customization result API."""
    task_id: str
    original_resume_id: str
    customized_text: str
    customization_level: str
    changes_summary: Dict[str, Any]
    optimization_metrics: Dict[str, Any]
    completion_timestamp: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomizationResultResponse':
        """Create a response object from a dictionary."""
        return cls(
            task_id=data.get('task_id', ''),
            original_resume_id=data.get('original_resume_id', ''),
            customized_text=data.get('customized_text', ''),
            customization_level=data.get('customization_level', 'standard'),
            changes_summary=data.get('changes_summary', {}),
            optimization_metrics=data.get('optimization_metrics', {}),
            completion_timestamp=data.get('completion_timestamp', '')
        )


@dataclass
class SavedJobDescription:
    """Model for storing saved job descriptions."""
    id: str
    title: str
    description: str
    processed_description: str
    company: Optional[str] = None
    source_url: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
