"""Tool initialization module for CrewAI integration.

This module provides both the legacy tools for backward compatibility
and access to the new tool implementation.
"""
from app.crews.tools.resume_processor import ResumeProcessorTool, JobMatcherTool

# Import new tool implementation
from app.crews.tools.resume_tools import (
    ResumeTools, 
    create_resume_tools,
    create_resume_processor_tool,  # Now available as standalone function
    create_job_matcher_tool        # Now available as standalone function
)
from app.crews.tools.base import BaseResumeTool
from app.crews.tools.base.base_tool import ToolRegistry

__all__ = [
    # Legacy tools (backward compatible)
    "ResumeProcessorTool",
    "JobMatcherTool",
    
    # New tool system
    "ResumeTools",
    "create_resume_tools",
    "create_resume_processor_tool",  
    "create_job_matcher_tool",
    "BaseResumeTool",
    "ToolRegistry"
]
