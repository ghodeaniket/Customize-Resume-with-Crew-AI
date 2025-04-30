"""Custom tool for processing resumes in CrewAI."""
from typing import Dict, Any, Optional, TYPE_CHECKING

from crewai.tools import BaseTool, tool
from pydantic import BaseModel, Field

from app.core.logging import logger

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from app.services.resume_service import ResumeService


# Function to create the resume processor tool
def create_resume_processor_tool(resume_service):
    """Create and return a resume processor tool with the service attached."""
    
    @tool("Resume Processor")
    def process_resume_tool(task_id: str) -> Dict[str, Any]:
        """Processes resumes and extracts text for analysis.
        
        Args:
            task_id: The ID of the uploaded resume task
            
        Returns:
            Dict: Extracted resume content and metadata
        """
        import asyncio
        
        logger.info(f"ResumeProcessorTool processing resume with task ID: {task_id}")
        
        try:
            # Run the async function in a synchronous context for the tool
            resume_data = asyncio.run(resume_service.get_resume_data(task_id))
            
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


# Still keep the class-based implementation as a fallback option
class ResumeProcessorTool(BaseTool):
    """Tool for processing resumes in various formats."""
    
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
        import asyncio
        
        logger.info(f"ResumeProcessorTool processing resume with task ID: {task_id}")
        
        try:
            # Run the async function in a synchronous context
            resume_data = asyncio.run(self.resume_service.get_resume_data(task_id))
            
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
    
    async def _arun(self, task_id: str) -> Dict[str, Any]:
        """Process a resume by task ID.
        
        Args:
            task_id: The ID of the uploaded resume task
            
        Returns:
            Dict: Extracted resume content and metadata
        """
        logger.info(f"ResumeProcessorTool processing resume with task ID: {task_id}")
        
        try:
            resume_data = await self.resume_service.get_resume_data(task_id)
            
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


# Function to create a job matcher tool
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


# Keep class-based version as a fallback option
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
