"""Service for analyzing job descriptions with CrewAI agents."""
from typing import Dict, Any, Optional
from crewai import Crew, Agent, Task

from app.core.logging import logger
from app.core.exceptions import CustomizationError
from app.services.resume.core.crew_result_extractor import CrewResultExtractor


class JobAnalysisService:
    """Service for analyzing job descriptions using CrewAI."""
    
    async def analyze_job_description(
        self, crew: Crew, job_description: str
    ) -> str:
        """Run job analysis task with the crew.
        
        Args:
            crew: The CrewAI crew instance
            job_description: The job description to analyze
            
        Returns:
            str: Job analysis result
            
        Raises:
            CustomizationError: If the job analysis fails
        """
        logger.info("Running job analysis with CrewAI")
        try:
            # Run the first task (job analysis)
            logger.info("Kicking off job analysis crew")
            crew_output = crew.kickoff()
            logger.info(f"Received crew output type: {type(crew_output)}")
            
            # Extract the result using specialized extractor
            result = CrewResultExtractor.extract_job_analysis_result(crew_output)
            
            if result:
                logger.info("Job analysis completed successfully")
                return result
            else:
                # Fallback if we couldn't extract a result
                logger.warning("Could not extract structured output, returning string representation")
                return str(crew_output)
            
        except Exception as e:
            logger.error(f"Error during job analysis: {str(e)}", exc_info=True)
            raise CustomizationError(f"Job analysis failed: {str(e)}")
    
    async def create_analysis_task(
        self, agent: Agent, job_description: str
    ) -> Task:
        """Create a task for analyzing a job description.
        
        Args:
            agent: The CrewAI agent to assign the task to
            job_description: The job description text
            
        Returns:
            Task: The job analysis task
        """
        from app.crews.tasks.analyze_job import create_job_analysis_task
        
        return create_job_analysis_task(
            agent=agent,
            job_description=job_description
        )
    
    def log_analysis_result(self, result: str) -> None:
        """Log the job analysis result for debugging.
        
        Args:
            result: The job analysis result
        """
        result_preview = (
            str(result)[:200] + "..." 
            if len(str(result)) > 200 
            else str(result)
        )
        logger.info(f"Job analysis result: {result_preview}")
