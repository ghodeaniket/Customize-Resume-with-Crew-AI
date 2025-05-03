"""Resume optimization task implementation.

This module provides the task for optimizing resumes based on
job description analysis results.
"""
from typing import Dict, Any, Optional

from crewai import Agent

from app.crews.tasks.base import BaseResumeTask
from app.crews.tasks.base.base_task import TaskConfig
from app.core.logging import logger


class ResumeOptimizationTask(BaseResumeTask):
    """Task for optimizing resumes based on job analysis.
    
    This task is responsible for tailoring resume content to match
    the requirements identified in the job description analysis.
    """
    
    def __init__(
        self, 
        resume_text: str, 
        job_analysis_result: str,
        customize_level: str = "standard"
    ):
        """Initialize the resume optimization task.
        
        Args:
            resume_text: Original resume text
            job_analysis_result: Result of job analysis task
            customize_level: Level of customization (minimal, standard, comprehensive)
        """
        logger.info(f"Initializing ResumeOptimizationTask with {customize_level} customization")
        
        # Get customization guidance
        level_guidance = self._get_customization_guidance(customize_level)
        
        # Define task configuration
        config = TaskConfig(
            name="Resume Optimization",
            description=(
                f"Using the original resume text and the job analysis results, "
                f"create a tailored resume that highlights the most relevant skills "
                f"and experiences for this specific job opportunity.\n\n"
                f"ORIGINAL RESUME:\n{resume_text}\n\n"
                f"JOB ANALYSIS RESULTS:\n{job_analysis_result}\n\n"
                f"CUSTOMIZATION LEVEL: {customize_level}\n{level_guidance}\n\n"
                f"Your task is to:\n"
                f"1. Identify the most relevant parts of the resume that match job requirements\n"
                f"2. Highlight key skills and experiences that align with the job description\n"
                f"3. Add relevant keywords from the job description where appropriate\n"
                f"4. Reorganize content to prioritize the most relevant information\n"
                f"5. Adjust language to better match the terminology in the job description\n"
                f"6. Ensure the resume will pass ATS screening systems\n"
                f"7. Remove or downplay less relevant information\n\n"
                f"IMPORTANT: Maintain absolute factual accuracy - do not invent experiences, "
                f"skills, or qualifications that are not present in the original resume."
            ),
            expected_output=(
                "A complete, optimized resume in plain text format that highlights the "
                "candidate's relevant skills and experiences for this specific job. "
                "The resume should maintain the candidate's authentic background while "
                "presenting it in the most compelling way for this opportunity."
            ),
            async_execution=False
        )
        
        super().__init__(config)
        self.resume_text = resume_text
        self.job_analysis_result = job_analysis_result
        self.customize_level = customize_level.lower()
    
    def _get_customization_guidance(self, level: str) -> str:
        """Get customization guidance based on level.
        
        Args:
            level: Customization level
            
        Returns:
            str: Guidance for the specified level
        """
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
        
        return customization_guidance.get(
            level.lower(), customization_guidance["standard"]
        )
    
    def validate_result(self, result: Any) -> bool:
        """Validate the optimization result.
        
        Args:
            result: Result to validate
            
        Returns:
            bool: True if result is valid
        """
        if not result:
            return False
        
        # Check if result contains resume content
        if isinstance(result, str):
            # Check for minimum length
            if len(result) < 100:  # Arbitrary minimum for a valid resume
                return False
            
            # Check for basic resume components
            components = ["experience", "skills", "education"]
            has_components = any(
                component.lower() in result.lower()
                for component in components
            )
            return has_components
        
        return True
    
    def calculate_optimization_score(self, original: str, optimized: str) -> float:
        """Calculate how much the resume was optimized.
        
        Args:
            original: Original resume text
            optimized: Optimized resume text
            
        Returns:
            float: Optimization score (0.0 to 1.0)
        """
        # This is a placeholder for scoring logic
        # In a real implementation, this would analyze the changes made
        if not original or not optimized:
            return 0.0
        
        # Simple length-based score for now
        length_change = abs(len(optimized) - len(original)) / len(original)
        return min(length_change, 1.0)


def create_resume_optimization_task(
    agent: Agent, 
    resume_text: str, 
    job_analysis_result: str,
    customize_level: str = "standard"
) -> Any:
    """Create and return a configured resume optimization task.
    
    This factory function maintains backward compatibility with the
    existing codebase while using the new task architecture.
    
    Args:
        agent: Agent to assign to the task
        resume_text: Original resume text
        job_analysis_result: Result of job analysis task
        customize_level: Level of customization
        
    Returns:
        Task: Configured resume optimization task
    """
    task_creator = ResumeOptimizationTask(
        resume_text=resume_text,
        job_analysis_result=job_analysis_result,
        customize_level=customize_level
    )
    return task_creator.get_task(agent)
