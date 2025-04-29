"""Custom CrewAI tool for resume processing."""
from typing import Dict, Any

from crewai_tools import BaseTool

from app.core.logging import logger


class ResumeProcessorTool(BaseTool):
    """Tool for processing resumes in various formats."""
    
    name: str = "ResumeProcessor"
    description: str = "Processes resumes in PDF or DOCX format and extracts text"
    
    async def _run(self, task_id: str) -> Dict[str, Any]:
        """Process a resume by task ID.
        
        Args:
            task_id: The ID of the uploaded resume task
            
        Returns:
            Dict: Extracted resume content and metadata
        """
        from app.services.resume_service import get_resume_service
        
        logger.debug(f"Running ResumeProcessorTool for task {task_id}")
        
        resume_service = get_resume_service()
        resume_data = await resume_service.get_resume_data(task_id)
        
        if not resume_data:
            logger.warning(f"Resume data not found for task {task_id}")
            return {"error": "Resume not found or processing not complete"}
        
        return {
            "text": resume_data.get("text", ""),
            "metadata": resume_data.get("metadata", {})
        }
