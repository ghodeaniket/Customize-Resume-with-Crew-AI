"""Resume Optimizer agent for customizing resumes based on job descriptions."""
from crewai import Agent

from app.core.config import settings


def create_resume_optimizer_agent():
    """Create an agent for optimizing resumes based on job descriptions."""
    return Agent(
        role="Resume Optimizer",
        goal="Create tailored resumes that match job requirements",
        backstory=(
            "You are a professional resume writer with expertise in customizing "
            "resumes to match specific job descriptions. You excel at highlighting "
            "relevant experience and skills to increase a candidate's chances."
        ),
        verbose=True
    )
