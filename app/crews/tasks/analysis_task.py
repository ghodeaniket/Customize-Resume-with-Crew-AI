"""Job description analysis task implementation.

This module provides the task for analyzing job descriptions
to extract key requirements and preferences.
"""
from typing import Dict, Any

from crewai import Agent

from app.crews.tasks.base import BaseResumeTask
from app.crews.tasks.base.base_task import TaskConfig
from app.core.logging import logger


class JobAnalysisTask(BaseResumeTask):
    """Task for analyzing job descriptions.
    
    This task is responsible for extracting key information from job
    descriptions including skills, experience requirements, and keywords.
    """
    
    def __init__(self, job_description: str):
        """Initialize the job analysis task.
        
        Args:
            job_description: Job description text to analyze
        """
        logger.info("Initializing JobAnalysisTask")
        
        # Define task configuration
        config = TaskConfig(
            name="Job Analysis",
            description=(
                f"Analyze the following job description to extract key requirements, "
                f"skills, experiences, and qualifications:\n\n{job_description}\n\n"
                f"Your analysis should include:\n"
                f"1. Required technical skills\n"
                f"2. Required soft skills\n"
                f"3. Years of experience required\n"
                f"4. Education requirements\n"
                f"5. Key responsibilities\n"
                f"6. Job title and seniority level\n"
                f"7. Important keywords for ATS optimization\n"
                f"8. Any preferred but not required qualifications\n"
                f"9. Company culture indicators if present\n"
                f"10. Salary range or compensation details if mentioned"
            ),
            expected_output=(
                "A structured analysis of the job requirements including:\n"
                "- Technical skills list\n"
                "- Soft skills list\n"
                "- Experience level and years required\n"
                "- Education requirements\n"
                "- Key responsibilities\n"
                "- Important keywords for ATS\n"
                "- Preferred qualifications\n"
                "- Any additional relevant information"
            ),
            async_execution=False
        )
        
        super().__init__(config)
        self.job_description = job_description
    
    def validate_result(self, result: Any) -> bool:
        """Validate the job analysis result.
        
        Args:
            result: Result to validate
            
        Returns:
            bool: True if result is valid
        """
        if not result:
            return False
        
        # Check if result contains key analysis components
        required_components = [
            "skills", "experience", "education", "keywords"
        ]
        
        # For text results, check if key phrases are present
        if isinstance(result, str):
            has_components = any(
                component.lower() in result.lower()
                for component in required_components
            )
            return has_components
        
        # For structured results, check for required fields
        if isinstance(result, dict):
            has_components = any(
                component in result
                for component in required_components
            )
            return has_components
        
        return True
    
    def parse_result(self, result: str) -> Dict[str, Any]:
        """Parse the analysis result into structured data.
        
        Args:
            result: Raw analysis result
            
        Returns:
            Dict[str, Any]: Structured analysis data
        """
        # This is a placeholder for parsing logic
        # In a real implementation, this would use NLP or pattern matching
        # to extract structured data from the agent's output
        return {
            "raw_analysis": result,
            "technical_skills": [],
            "soft_skills": [],
            "experience_years": 0,
            "education": [],
            "keywords": []
        }


def create_job_analysis_task(agent: Agent, job_description: str) -> Any:
    """Create and return a configured job analysis task.
    
    This factory function maintains backward compatibility with the
    existing codebase while using the new task architecture.
    
    Args:
        agent: Agent to assign to the task
        job_description: Job description text to analyze
        
    Returns:
        Task: Configured job analysis task
    """
    task_creator = JobAnalysisTask(job_description)
    return task_creator.get_task(agent)
