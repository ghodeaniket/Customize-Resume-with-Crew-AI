"""Resume operations controller with business logic separated from routes.

This module serves as a compatibility layer after refactoring.
The original large controller has been split into smaller, focused controllers.
"""
from .resume.resume_controller import UnifiedResumeController as ResumeController

__all__ = ["ResumeController"]
