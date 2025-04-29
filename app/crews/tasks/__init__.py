"""Task initialization module for CrewAI integration."""
from app.crews.tasks.analyze_job import create_job_analysis_task
from app.crews.tasks.optimize_resume import create_resume_optimization_task

__all__ = [
    "create_job_analysis_task",
    "create_resume_optimization_task"
]
