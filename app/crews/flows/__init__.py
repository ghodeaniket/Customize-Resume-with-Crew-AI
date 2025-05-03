"""Flow initialization module for CrewAI integration.

This module provides access to both the legacy and new flow implementations.
"""
from app.crews.flows.resume_customization_flow import ResumeCustomizationFlow

# Import new flow implementation
from app.crews.flows.resume_flow import ResumeCustomizationFlow as ResumeCustomizationFlowV2
from app.crews.flows.base import BaseResumeFlow

__all__ = [
    # Legacy flow (backward compatible)
    "ResumeCustomizationFlow",
    
    # New flow implementation 
    "ResumeCustomizationFlowV2",
    "BaseResumeFlow"
]
