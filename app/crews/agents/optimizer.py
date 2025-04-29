"""Resume optimization agent for customizing resumes to match job requirements."""
from typing import Dict, List, Optional, Any

from crewai import Agent
from crewai_tools import BaseTool

from app.core.config import settings
from app.core.logging import logger


def create_resume_optimizer_agent(tools: Optional[List[BaseTool]] = None) -> Agent:
    """Create an agent for optimizing resumes based on job descriptions.
    
    The optimizer agent is responsible for:
    1. Tailoring resume content to highlight relevant skills and experiences
    2. Reorganizing resume sections to emphasize job-relevant information
    3. Adding keywords and phrases that match the job description
    4. Ensuring the resume passes ATS screening systems
    
    Args:
        tools: Optional list of tools for the agent to use
        
    Returns:
        Agent: Configured resume optimizer agent
    """
    logger.info("Creating resume optimizer agent")
    
    backstory = (
        "You are a professional resume writer with expertise in customizing "
        "resumes to match specific job descriptions. You excel at highlighting "
        "relevant experience and skills to increase a candidate's chances of "
        "getting past ATS systems and impressing hiring managers. "
        "You understand the importance of maintaining authenticity while "
        "presenting the candidate's background in the most favorable light. "
        "You know exactly what recruiters and hiring managers look for and "
        "how to structure information to catch their attention."
    )
    
    return Agent(
        role="Resume Optimizer",
        goal=(
            "Create tailored resumes that match specific job requirements "
            "while accurately representing the candidate's background"
        ),
        backstory=backstory,
        tools=tools or [],
        verbose=settings.AGENT_VERBOSE,
        llm=settings.AGENT_LLM,
        memory=True  # Enable memory for the optimizer to remember previous customizations
    )
