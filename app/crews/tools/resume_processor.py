"""CrewAI-compatible tools for resume processing with proper async handling."""
from typing import Dict, Any, TYPE_CHECKING
import asyncio

from crewai.tools import BaseTool, tool
from pydantic import BaseModel, Field

from app.core.logging import logger

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from app.services.resume_service import ResumeService


def create_resume_processor_tool(resume_service):
    """Create and return a resume processor tool with the service attached.
    
    This creates a function-based tool that's compatible with CrewAI 0.117.0+ and
    properly handles async operations when running in a FastAPI context.
    """
    
    @tool("Resume Processor")
    def process_resume_tool(task_id: str) -> Dict[str, Any]:
        """Processes resumes and extracts text for analysis.
        
        Args:
            task_id: The ID of the uploaded resume task
            
        Returns:
            Dict: Extracted resume content and metadata
        """
        logger.info(f"ResumeProcessorTool processing resume with task ID: {task_id}")
        
        try:
            # For CrewAI tools in FastAPI, we need to handle async operations carefully.
            # Check if there's an existing event loop first
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, use asyncio.create_task
                    logger.info(f"Using existing event loop for task ID: {task_id}")
                    resume_data_future = asyncio.run_coroutine_threadsafe(
                        resume_service.get_resume_data(task_id), loop
                    )
                    resume_data = resume_data_future.result(timeout=30)  # 30 second timeout
                else:
                    # If loop exists but is not running, run the coroutine directly
                    logger.info(f"Using existing non-running loop for task ID: {task_id}")
                    resume_data = loop.run_until_complete(resume_service.get_resume_data(task_id))
            except RuntimeError:
                # If there's no event loop, create a new one
                logger.info(f"Creating new event loop for task ID: {task_id}")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    resume_data = loop.run_until_complete(resume_service.get_resume_data(task_id))
                finally:
                    loop.close()
                    asyncio.set_event_loop(None)
            
            if not resume_data:
                logger.warning(f"Resume not found or processing not complete: {task_id}")
                return {"error": "Resume not found or processing not complete"}
            
            if resume_data.get("status") != "completed":
                logger.warning(f"Resume processing not complete: {task_id}, status: {resume_data.get('status')}")
                return {"error": f"Resume processing not complete. Status: {resume_data.get('status')}"}
            
            logger.info(f"Successfully retrieved resume data for task ID: {task_id}")
            
            return {
                "text": resume_data.get("text", ""),
                "metadata": resume_data.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Error in ResumeProcessorTool for task ID {task_id}: {str(e)}", exc_info=True)
            return {"error": f"Error processing resume: {str(e)}"}
    
    return process_resume_tool


def create_job_matcher_tool():
    """Create and return a job matcher tool."""
    
    @tool("Job Matcher")
    def job_matcher_tool(resume_text: str, job_description: str) -> Dict[str, Any]:
        """Analyzes how well a resume matches job requirements.
        
        Args:
            resume_text: The resume text content
            job_description: The job description text
            
        Returns:
            Dict: Analysis of the match between resume and job description
        """
        logger.info("JobMatcherTool analyzing resume-job match")
        
        try:
            # This is a placeholder for more sophisticated matching logic
            # In a real implementation, this would use NLP or other techniques
            # to analyze the match between resume and job description
            
            # For now, we'll just return a simple structure
            return {
                "match_score": 0.75,  # Placeholder score
                "match_analysis": "Resume appears to match many of the job requirements.",
                "missing_skills": ["Python", "Docker"],  # Placeholder data
                "matching_skills": ["FastAPI", "AWS"],   # Placeholder data
                "recommendations": [
                    "Highlight Python experience more prominently",
                    "Add Docker to your skills section if you have experience"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in JobMatcherTool: {str(e)}", exc_info=True)
            return {"error": f"Error analyzing resume-job match: {str(e)}"}
    
    return job_matcher_tool


# Class-based implementations kept for backward compatibility
class ResumeProcessorTool(BaseTool):
    """Tool for processing resumes in various formats.
    
    This class-based implementation is kept for backward compatibility
    but the function-based tools above are recommended for CrewAI 0.117.0+.
    """
    
    name: str = "ResumeProcessor"
    description: str = "Processes resumes and extracts text for analysis"
    
    def __init__(self, resume_service: "ResumeService"):
        """Initialize the resume processor tool.
        
        Args:
            resume_service: Resume service for accessing resume data
        """
        self.resume_service = resume_service
        super().__init__()
        logger.info("Initialized ResumeProcessorTool")
    
    def _run(self, task_id: str) -> Dict[str, Any]:
        """Process a resume by task ID (synchronous version for compatibility).
        
        Args:
            task_id: The ID of the uploaded resume task
            
        Returns:
            Dict: Extracted resume content and metadata
        """
        logger.info(f"ResumeProcessorTool processing resume with task ID: {task_id}")
        
        try:
            # Check if there's an existing event loop first
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, use asyncio.run_coroutine_threadsafe
                    logger.info(f"Using existing event loop for task ID: {task_id}")
                    resume_data_future = asyncio.run_coroutine_threadsafe(
                        self.resume_service.get_resume_data(task_id), loop
                    )
                    resume_data = resume_data_future.result(timeout=30)  # 30 second timeout
                else:
                    # If loop exists but is not running, run the coroutine directly
                    logger.info(f"Using existing non-running loop for task ID: {task_id}")
                    resume_data = loop.run_until_complete(self.resume_service.get_resume_data(task_id))
            except RuntimeError:
                # If there's no event loop, create a new one
                logger.info(f"Creating new event loop for task ID: {task_id}")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    resume_data = loop.run_until_complete(self.resume_service.get_resume_data(task_id))
                finally:
                    loop.close()
                    asyncio.set_event_loop(None)
            
            if not resume_data:
                logger.warning(f"Resume not found or processing not complete: {task_id}")
                return {"error": "Resume not found or processing not complete"}
            
            if resume_data.get("status") != "completed":
                logger.warning(f"Resume processing not complete: {task_id}, status: {resume_data.get('status')}")
                return {"error": f"Resume processing not complete. Status: {resume_data.get('status')}"}
            
            logger.info(f"Successfully retrieved resume data for task ID: {task_id}")
            
            return {
                "text": resume_data.get("text", ""),
                "metadata": resume_data.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Error in ResumeProcessorTool for task ID {task_id}: {str(e)}", exc_info=True)
            return {"error": f"Error processing resume: {str(e)}"}


class JobMatcherTool(BaseTool):
    """Tool for matching resume content to job requirements."""
    
    name: str = "JobMatcher"
    description: str = "Analyzes how well a resume matches job requirements"
    
    def _run(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """Analyze how well a resume matches job requirements.
        
        Args:
            resume_text: The resume text content
            job_description: The job description text
            
        Returns:
            Dict: Analysis of the match between resume and job description
        """
        logger.info("JobMatcherTool analyzing resume-job match")
        
        try:
            # This is a placeholder for more sophisticated matching logic
            return {
                "match_score": 0.75,
                "match_analysis": "Resume appears to match many of the job requirements.",
                "missing_skills": ["Python", "Docker"],
                "matching_skills": ["FastAPI", "AWS"],
                "recommendations": [
                    "Highlight Python experience more prominently",
                    "Add Docker to your skills section if you have experience"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in JobMatcherTool: {str(e)}", exc_info=True)
            return {"error": f"Error analyzing resume-job match: {str(e)}"}
