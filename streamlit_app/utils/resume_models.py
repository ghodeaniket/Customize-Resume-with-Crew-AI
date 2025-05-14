"""Data models for the resume customizer application."""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List


class ResumeUploadError(Exception):
    """Exception raised when resume upload fails."""
    pass


class ResumeStatusError(Exception):
    """Exception raised when resume status check fails."""
    pass


class ResumeTextError(Exception):
    """Exception raised when retrieving resume text fails."""
    pass


@dataclass
class ResumeUploadResponse:
    """Response data for resume upload API."""
    task_id: str
    filename: str
    status: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResumeUploadResponse':
        """Create a response object from a dictionary."""
        return cls(
            task_id=data.get('task_id', ''),
            filename=data.get('filename', ''),
            status=data.get('status', '')
        )


@dataclass
class TaskStatusResponse:
    """Response data for task status API."""
    task_id: str
    status: str
    progress: float
    message: Optional[str] = None
    processing_time_ms: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskStatusResponse':
        """Create a response object from a dictionary."""
        return cls(
            task_id=data.get('task_id', ''),
            status=data.get('status', ''),
            progress=data.get('progress', 0.0),
            message=data.get('message'),
            processing_time_ms=data.get('processing_time_ms')
        )


@dataclass
class ResumeTextResponse:
    """Response data for resume text API."""
    task_id: str
    text: str
    metadata: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResumeTextResponse':
        """Create a response object from a dictionary."""
        return cls(
            task_id=data.get('task_id', ''),
            text=data.get('text', ''),
            metadata=data.get('metadata', {})
        )
