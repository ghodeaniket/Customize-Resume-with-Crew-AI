"""Custom exception classes for the application."""
from fastapi import HTTPException, status


class DocumentProcessingError(Exception):
    """Raised when there's an error processing a document."""
    
    def __init__(self, detail: str = "Error processing document"):
        self.detail = detail
        super().__init__(self.detail)


class UnsupportedFileTypeError(Exception):
    """Raised when an unsupported file type is detected."""
    
    def __init__(self, detail: str = "Unsupported file type"):
        self.detail = detail
        super().__init__(self.detail)


class ResumeNotFoundError(Exception):
    """Raised when a resume is not found."""
    
    def __init__(self, resume_id: str):
        self.detail = f"Resume with ID {resume_id} not found"
        super().__init__(self.detail)


class TaskNotFoundError(Exception):
    """Raised when a task is not found."""
    
    def __init__(self, task_id: str):
        self.detail = f"Task with ID {task_id} not found"
        super().__init__(self.detail)


class CustomizationError(Exception):
    """Raised when there's an error during resume customization."""
    
    def __init__(self, detail: str = "Error customizing resume"):
        self.detail = detail
        super().__init__(self.detail)
