"""Resume Analyzer agent for analyzing resumes and job descriptions."""
from crewai import Agent

from app.core.config import settings


def create_resume_analyzer_agent():
    """Create an agent for analyzing resumes and job descriptions."""
    return Agent(
        role="Resume Analyzer",
        goal="Analyze resumes and job descriptions to identify key skills and requirements",
        backstory=(
            "You are an expert in parsing and analyzing documents related to job applications. "
            "Your specialty is identifying the most important skills, experiences, and "
            "qualifications in both resumes and job descriptions."
        ),
        verbose=True
    )
