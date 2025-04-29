"""Agent initialization module for CrewAI integration."""
from app.crews.agents.analyzer import create_resume_analyzer_agent
from app.crews.agents.optimizer import create_resume_optimizer_agent

__all__ = [
    "create_resume_analyzer_agent",
    "create_resume_optimizer_agent"
]
