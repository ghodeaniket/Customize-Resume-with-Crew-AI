"""Custom CrewAI tool for resume processing."""
from typing import Dict, Any, Optional, List
import json
import asyncio

from crewai_tools import BaseTool, Tool
from langchain.pydantic_v1 import Field
from app.api.dependencies import get_resume_service, get_document_storage_service
from app.core.logging import logger


class ResumeProcessorTool(BaseTool):
    """Tool for processing resumes in various formats."""
    
    name: str = "ResumeProcessor"
    description: str = """
    Processes resumes in PDF or DOCX format and extracts text.
    Can extract skills, experience, education, and other information from resumes.
    Useful for analyzing resumes and comparing them to job descriptions.
    """
    
    async def _run(self, task_id: str) -> Dict[str, Any]:
        """Process a resume by task ID.
        
        Args:
            task_id: The ID of the uploaded resume task
            
        Returns:
            Dict: Extracted resume content and metadata
        """
        # Import within method to avoid circular imports
        from app.api.dependencies import get_resume_service
        
        logger.info(f"Running ResumeProcessorTool for task {task_id}", extra={
            "task_id": task_id,
            "tool": "ResumeProcessorTool",
            "action": "extract_text"
        })
        
        resume_service = get_resume_service()
        resume_data = await resume_service.get_resume_data(task_id)
        
        if not resume_data:
            logger.warning(f"Resume data not found for task {task_id}", extra={
                "task_id": task_id,
                "tool": "ResumeProcessorTool",
                "error": "resume_not_found"
            })
            return {
                "error": "Resume not found or processing not complete",
                "success": False,
                "task_id": task_id
            }
        
        metadata = resume_data.get("metadata", {})
        status = metadata.get("status", "unknown")
        
        # Check if processing is complete
        if status != "completed":
            logger.warning(f"Resume processing not complete for task {task_id}: {status}", extra={
                "task_id": task_id,
                "status": status,
                "tool": "ResumeProcessorTool",
                "error": "processing_not_complete"
            })
            return {
                "error": f"Resume processing not complete. Current status: {status}",
                "success": False,
                "task_id": task_id,
                "status": status
            }
        
        extracted_text = resume_data.get("text", "")
        
        if not extracted_text:
            logger.warning(f"No extracted text found for task {task_id}", extra={
                "task_id": task_id,
                "tool": "ResumeProcessorTool",
                "error": "no_extracted_text"
            })
            return {
                "error": "No extracted text found",
                "success": False,
                "task_id": task_id
            }
        
        # Log success
        logger.info(f"Successfully retrieved resume text for task {task_id}", extra={
            "task_id": task_id,
            "text_length": len(extracted_text),
            "tool": "ResumeProcessorTool",
            "status": "success"
        })
        
        return {
            "text": extracted_text,
            "metadata": metadata,
            "task_id": task_id,
            "success": True,
            "status": status,
            "text_length": len(extracted_text)
        }


# Factory function to create the tool with correct dependencies
def get_resume_processor_tool() -> Tool:
    """Get instance of the ResumeProcessorTool.
    
    Returns:
        Tool: Configured ResumeProcessorTool instance
    """
    return ResumeProcessorTool()


class ResumeSectionExtractorTool(BaseTool):
    """Tool for extracting specific sections from a resume."""
    
    name: str = "ResumeSectionExtractor"
    description: str = """
    Extracts specific sections from a resume.
    Can extract skills, experience, education, and other standard resume sections.
    Useful for targeted analysis of specific parts of a resume.
    """
    
    section_name: str = Field(
        description="The name of the section to extract (e.g., 'skills', 'experience', 'education')"
    )
    
    async def _run(self, task_id: str, section_name: str) -> Dict[str, Any]:
        """Extract a specific section from a resume.
        
        Args:
            task_id: The ID of the uploaded resume task
            section_name: The name of the section to extract
            
        Returns:
            Dict: Extracted section content and metadata
        """
        # First get the entire resume
        processor_tool = ResumeProcessorTool()
        resume_data = await processor_tool._run(task_id)
        
        if "error" in resume_data and resume_data.get("success", False) is False:
            return resume_data
            
        # Extract the requested section
        # Note: This is a simple implementation that can be enhanced with NLP or more
        # sophisticated section detection algorithms
        text = resume_data.get("text", "")
        sections = self._extract_sections(text)
        
        target_section = section_name.lower()
        extracted_section = None
        
        # Find the requested section
        for section in sections:
            if section["name"].lower() == target_section:
                extracted_section = section
                break
        
        if not extracted_section:
            logger.warning(f"Section '{section_name}' not found in resume {task_id}", extra={
                "task_id": task_id,
                "section": section_name,
                "tool": "ResumeSectionExtractorTool",
                "error": "section_not_found"
            })
            return {
                "error": f"Section '{section_name}' not found in the resume",
                "success": False,
                "task_id": task_id,
                "available_sections": [s["name"] for s in sections]
            }
        
        logger.info(f"Extracted section '{section_name}' from resume {task_id}", extra={
            "task_id": task_id,
            "section": section_name,
            "content_length": len(extracted_section["content"]),
            "tool": "ResumeSectionExtractorTool",
            "status": "success"
        })
        
        return {
            "section_name": section_name,
            "content": extracted_section["content"],
            "task_id": task_id,
            "success": True
        }
    
    def _extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """Extract sections from resume text using naive heading detection.
        
        Args:
            text: The resume text
            
        Returns:
            List[Dict[str, Any]]: List of sections with name and content
        """
        lines = text.split("\n")
        sections = []
        current_section = None
        current_content = []
        
        common_section_names = [
            "summary", "objective", "skills", "experience", "employment",
            "work history", "education", "certifications", "projects",
            "publications", "awards", "references", "languages",
            "interests", "volunteer", "personal"
        ]
        
        for line in lines:
            line = line.strip()
            
            if not line:
                # Add empty line to current section
                if current_section:
                    current_content.append("")
                continue
            
            # Check if this line is a potential section header
            is_header = False
            line_lower = line.lower()
            
            # Check if line is all uppercase
            if line.isupper() and len(line) > 3:
                is_header = True
            
            # Check if line matches common section names
            elif any(name in line_lower for name in common_section_names):
                # Check if it's short (likely a header)
                if len(line) < 30:
                    is_header = True
            
            # Check if line ends with a colon
            elif line.endswith(":"):
                is_header = True
            
            if is_header:
                # Save previous section
                if current_section and current_content:
                    sections.append({
                        "name": current_section,
                        "content": "\n".join(current_content)
                    })
                
                # Start new section
                current_section = line.rstrip(":")
                current_content = []
            else:
                # Add line to current section
                if current_section:
                    current_content.append(line)
                else:
                    # No section header yet, create default section
                    current_section = "Header"
                    current_content.append(line)
        
        # Add final section
        if current_section and current_content:
            sections.append({
                "name": current_section,
                "content": "\n".join(current_content)
            })
        
        return sections


# Factory function to create the section extractor tool
def get_resume_section_extractor_tool() -> Tool:
    """Get instance of the ResumeSectionExtractorTool.
    
    Returns:
        Tool: Configured ResumeSectionExtractorTool instance
    """
    return ResumeSectionExtractorTool()
