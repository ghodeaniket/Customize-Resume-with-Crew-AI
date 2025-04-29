"""Task for optimizing resumes based on job analysis."""
from crewai import Task

from app.core.logging import logger


def create_resume_optimization_task(agent, resume_id: str, job_analysis_result: str):
    """Create a task for optimizing a resume based on job analysis."""
    logger.debug(f"Creating resume optimization task for resume {resume_id}")
    
    return Task(
        description=(
            f"Using the resume with ID {resume_id} and the job analysis results, "
            f"create a tailored resume that highlights the most relevant skills "
            f"and experiences:\n\n{job_analysis_result}"
        ),
        expected_output=(
            "A tailored resume that emphasizes the candidate's qualifications "
            "that match the job requirements."
        ),
        agent=agent,
        context=[job_analysis_result]
    )
