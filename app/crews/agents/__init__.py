"""Agent initialization module for CrewAI integration.

This module provides both the factory functions for backward compatibility
and access to the new agent classes.
"""
from app.crews.agents.analyzer import create_resume_analyzer_agent
from app.crews.agents.optimizer import create_resume_optimizer_agent

# Import new agent classes
from app.crews.agents.analyzer_agent import ResumeAnalyzerAgent, create_resume_analyzer_agent as create_resume_analyzer_agent_v2
from app.crews.agents.optimizer_agent import ResumeOptimizerAgent, create_resume_optimizer_agent as create_resume_optimizer_agent_v2
from app.crews.agents.base import BaseResumAgent

__all__ = [
    # Legacy factory functions (backward compatible)
    "create_resume_analyzer_agent",
    "create_resume_optimizer_agent",
    
    # New agent classes and factories
    "ResumeAnalyzerAgent",
    "ResumeOptimizerAgent", 
    "BaseResumAgent",
    "create_resume_analyzer_agent_v2",
    "create_resume_optimizer_agent_v2"
]
