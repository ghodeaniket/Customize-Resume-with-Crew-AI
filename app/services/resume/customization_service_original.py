"""Service for resume customization operations - Refactored.

This module serves as a compatibility layer after refactoring. 
The original large service has been split into smaller, focused services.
"""
from typing import Dict, Any, Optional

from app.services.resume.base import BaseService
from app.services.resume.storage_service import ResumeStorageService
from app.services.resume.extraction_service import ResumeExtractionService
from app.repositories.task_repository import TaskRepository
from app.services.resume.customization.orchestrator_slim import (
    ResumeCustomizationService as _ResumeCustomizationService,
    get_resume_customization_service
)
from app.services.resume.customization.state_models import (
    CustomizationState,
    JobAnalysisState,
    ResumeOptimizationState
)

# Re-export for backward compatibility
ResumeCustomizationService = _ResumeCustomizationService

__all__ = [
    "ResumeCustomizationService",
    "get_resume_customization_service",  
    "CustomizationState",
    "JobAnalysisState",
    "ResumeOptimizationState",
]
