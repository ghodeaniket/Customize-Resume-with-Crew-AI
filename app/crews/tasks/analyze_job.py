"""Task for analyzing job descriptions."""
from crewai import Task

from app.core.logging import logger


def create_job_analysis_task(agent, job_description: str):
    """Create a task for analyzing a job description."""
    logger.debug("Creating job analysis task")
    
    return Task(
        description=(
            f"Analyze the following job description to extract key requirements, "
            f"skills, and qualifications:\n\n{job_description}"
        ),
        expected_output=(
            "A structured analysis of the job requirements including technical skills, "
            "experience level, soft skills, and any specific qualifications."
        ),
        agent=agent
    )
