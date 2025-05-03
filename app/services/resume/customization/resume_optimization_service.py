"""Service for optimizing resumes with CrewAI agents."""
from typing import Dict, Any
from crewai import Crew, Agent, Task

from app.core.logging import logger
from app.core.exceptions import CustomizationError
from app.services.resume.core.crew_result_extractor import CrewResultExtractor


class ResumeOptimizationService:
    """Service for optimizing resumes using CrewAI."""
    
    async def optimize_resume(
        self,
        crew: Crew,
        optimizer_agent: Agent,
        resume_text: str,
        job_analysis_result: str,
        customize_level: str
    ) -> str:
        """Run resume optimization task with the crew.
        
        Args:
            crew: The CrewAI crew instance
            optimizer_agent: The resume optimizer agent
            resume_text: The original resume text
            job_analysis_result: The result of job analysis
            customize_level: The level of customization
            
        Returns:
            str: Optimized resume text
            
        Raises:
            CustomizationError: If the optimization fails
        """
        logger.info(f"Running resume optimization with customize level: {customize_level}")
        try:
            # Create and add the optimization task
            optimization_task = await self.create_optimization_task(
                agent=optimizer_agent,
                resume_text=resume_text,
                job_analysis_result=job_analysis_result,
                customize_level=customize_level
            )
            
            # Replace crew tasks with the optimization task
            crew.tasks = [optimization_task]
            
            # Run the optimization task
            logger.info("Kicking off resume optimization crew")
            crew_output = crew.kickoff()
            logger.info(f"Received optimization crew output type: {type(crew_output)}")
            
            # Extract the result using specialized extractor
            result = CrewResultExtractor.extract_optimization_result(crew_output)
            
            if result:
                logger.info("Resume optimization completed successfully")
                return result
            else:
                # Fallback if we couldn't extract a result
                logger.warning("Could not extract structured output from optimization, returning string representation")
                return str(crew_output)
            
        except Exception as e:
            logger.error(f"Error during resume optimization: {str(e)}", exc_info=True)
            raise CustomizationError(f"Resume optimization failed: {str(e)}")
    
    async def optimize_resume_fallback(
        self,
        crew: Crew,
        optimizer_agent: Agent,
        resume_text: str,
        job_description_text: str,
        customize_level: str
    ) -> str:
        """Run resume optimization with a fallback approach.
        
        This method is used when the standard approach fails, typically due to
        formatting issues with the job analysis result.
        
        Args:
            crew: The CrewAI crew instance
            optimizer_agent: The resume optimizer agent
            resume_text: The original resume text
            job_description_text: The original job description text
            customize_level: The level of customization
            
        Returns:
            str: Optimized resume text
            
        Raises:
            CustomizationError: If the optimization fails
        """
        logger.info(f"Running FALLBACK resume optimization with customize level: {customize_level}")
        try:
            # Create the fallback optimization task
            fallback_task = await self.create_fallback_optimization_task(
                agent=optimizer_agent,
                resume_text=resume_text,
                job_description_text=job_description_text,
                customize_level=customize_level
            )
            
            # Replace crew tasks with the fallback task
            crew.tasks = [fallback_task]
            
            # Run the optimization task
            logger.info("Kicking off fallback resume optimization crew")
            crew_output = crew.kickoff()
            logger.info(f"Received fallback optimization crew output type: {type(crew_output)}")
            
            # Extract the result
            result = CrewResultExtractor.extract_optimization_result(crew_output)
            
            if result:
                logger.info("Fallback resume optimization completed successfully")
                return result
            else:
                # Fallback if we couldn't extract a result  
                logger.warning("Could not extract structured output from fallback optimization, returning string representation")
                return str(crew_output)
            
        except Exception as e:
            logger.error(f"Error during fallback resume optimization: {str(e)}", exc_info=True)
            raise CustomizationError(f"Fallback resume optimization failed: {str(e)}")
    
    async def create_optimization_task(
        self,
        agent: Agent,
        resume_text: str,
        job_analysis_result: str,
        customize_level: str
    ) -> Task:
        """Create a task for optimizing a resume.
        
        Args:
            agent: The CrewAI agent to assign the task to
            resume_text: The original resume text
            job_analysis_result: The job analysis result
            customize_level: The level of customization
            
        Returns:
            Task: The resume optimization task
        """
        from app.crews.tasks.optimize_resume import create_resume_optimization_task
        
        return create_resume_optimization_task(
            agent=agent,
            resume_text=resume_text,
            job_analysis_result=job_analysis_result,
            customize_level=customize_level
        )
    
    async def create_fallback_optimization_task(
        self,
        agent: Agent,
        resume_text: str,
        job_description_text: str,
        customize_level: str
    ) -> Task:
        """Create a fallback task for optimizing a resume.
        
        Args:
            agent: The CrewAI agent to assign the task to
            resume_text: The original resume text
            job_description_text: The original job description text
            customize_level: The level of customization
            
        Returns:
            Task: The fallback resume optimization task
        """
        from app.crews.tasks.optimize_resume_fallback import create_resume_optimization_fallback_task
        
        return create_resume_optimization_fallback_task(
            agent=agent,
            resume_text=resume_text,
            job_description_text=job_description_text,
            customize_level=customize_level
        )
