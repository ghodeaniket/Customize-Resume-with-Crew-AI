"""Task definition for job description analysis."""
from typing import Dict, Any

from crewai import Agent, Task

from app.core.logging import logger


def create_job_analysis_task(agent: Agent, job_description: str) -> Task:
    """Create a task for analyzing a job description.
    
    This task is responsible for extracting key requirements, skills,
    and qualifications from the job description to guide the resume
    customization process.
    
    Args:
        agent: The agent assigned to the task
        job_description: The job description text to analyze
        
    Returns:
        Task: Configured job analysis task
    """
    logger.info("Creating job analysis task")
    
    task_description = (
        f"Analyze the following job description to extract all key information "
        f"that would be relevant for tailoring a resume:\n\n"
        f"{job_description}\n\n"
        f"Your analysis should identify and categorize the following elements:\n"
        f"1. Required technical skills and technologies\n"
        f"2. Required soft skills and personal attributes\n"
        f"3. Required education and certifications\n"
        f"4. Required experience (years and type)\n"
        f"5. Preferred qualifications (nice-to-have)\n"
        f"6. Company values and culture indicators\n"
        f"7. Key responsibilities of the role\n"
        f"8. Industry-specific terminology and keywords\n"
        f"9. Seniority level and career stage\n"
        f"10. Potential red flags or challenging requirements\n\n"
        f"For each identified element, provide specific details and note "
        f"whether it appears to be a must-have requirement or a preference."
    )
    
    expected_output = (
        "A comprehensive, structured analysis of the job description "
        "with all key requirements, skills, and qualifications categorized "
        "according to importance and relevance for resume tailoring. "
        "The output should be in JSON format for easy processing."
    )
    
    return Task(
        description=task_description,
        expected_output=expected_output,
        agent=agent
    )
