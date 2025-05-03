"""Task initialization module for CrewAI integration.

This module provides both the legacy task functions for backward compatibility
and access to the new task classes.
"""
from app.crews.tasks.analyze_job import create_job_analysis_task
from app.crews.tasks.optimize_resume import create_resume_optimization_task

# Import new task classes
from app.crews.tasks.analysis_task import JobAnalysisTask, create_job_analysis_task as create_job_analysis_task_v2
from app.crews.tasks.optimization_task import ResumeOptimizationTask, create_resume_optimization_task as create_resume_optimization_task_v2
from app.crews.tasks.base import BaseResumeTask

__all__ = [
    # Legacy task functions (backward compatible)
    "create_job_analysis_task",
    "create_resume_optimization_task",
    
    # New task classes and factories
    "JobAnalysisTask",
    "ResumeOptimizationTask",
    "BaseResumeTask",
    "create_job_analysis_task_v2",
    "create_resume_optimization_task_v2"
]
