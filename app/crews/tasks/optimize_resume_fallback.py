"""Fallback task definition for resume optimization."""
from typing import Dict, Any, Optional

from crewai import Agent, Task

from app.core.logging import logger


def create_resume_optimization_fallback_task(
    agent: Agent, 
    resume_text: str, 
    job_description_text: str,
    customize_level: str = "standard"
) -> Task:
    """Create a fallback task for optimizing a resume based on job description.
    
    This task is a simplified version that doesn't rely on job analysis results.
    It works directly with the job description text instead.
    
    Args:
        agent: The agent assigned to the task
        resume_text: The original resume text
        job_description_text: The original job description text
        customize_level: The level of customization to apply (minimal, standard, comprehensive)
        
    Returns:
        Task: Configured resume optimization fallback task
    """
    logger.info(f"Creating fallback resume optimization task with {customize_level} customization level")
    
    # Define customization levels
    customization_guidance = {
        "minimal": (
            "Make only the most essential changes to highlight relevant skills and experiences. "
            "Focus on keyword matching and minor reorganization. "
            "Maintain at least 90% of the original content."
        ),
        "standard": (
            "Make moderate changes to highlight relevant skills and experiences. "
            "Adjust wording, reorganize content, and emphasize matching qualifications. "
            "Maintain at least 75% of the original content while ensuring a good match."
        ),
        "comprehensive": (
            "Make extensive changes to optimize the resume for this specific position. "
            "Rewrite sections, reorganize content, and tailor the presentation for maximum impact. "
            "Maintain the factual accuracy but feel free to completely restructure and reframe. "
            "Ensure the resume directly addresses at least 90% of the job requirements."
        )
    }
    
    level_guidance = customization_guidance.get(
        customize_level.lower(), customization_guidance["standard"]
    )
    
    task_description = (
        f"You are tasked with customizing a resume to match a specific job description.\n\n"
        f"ORIGINAL RESUME:\n{resume_text}\n\n"
        f"JOB DESCRIPTION:\n{job_description_text}\n\n"
        f"CUSTOMIZATION LEVEL: {customize_level}\n{level_guidance}\n\n"
        f"Your task is to:\n"
        f"1. Analyze the job description to identify key requirements, skills, and qualifications\n"
        f"2. Review the resume to find relevant experience and skills\n"
        f"3. Create a tailored version of the resume that highlights aspects that match the job description\n"
        f"4. Add relevant keywords from the job description where appropriate\n"
        f"5. Reorganize content to prioritize the most relevant information\n"
        f"6. Adjust language to better match the terminology in the job description\n"
        f"7. Ensure the resume will pass ATS screening systems\n"
        f"8. Remove or downplay less relevant information\n\n"
        f"IMPORTANT: Maintain absolute factual accuracy - do not invent experiences, "
        f"skills, or qualifications that are not present in the original resume."
    )
    
    expected_output = (
        "A complete, optimized resume in plain text format that highlights the "
        "candidate's relevant skills and experiences for this specific job. "
        "The resume should maintain the candidate's authentic background while "
        "presenting it in the most compelling way for this opportunity."
    )
    
    # Create the simplified task
    return Task(
        description=task_description,
        expected_output=expected_output,
        agent=agent,
        async_execution=False,  # Disable async execution to simplify debugging
        output_file=None  # Don't write to file automatically, we'll handle storage
    )
