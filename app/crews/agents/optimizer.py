"""Resume optimization agent for customizing resumes to match job requirements."""
from typing import Dict, List, Optional, Any, Union
import os

from crewai import Agent, LLM
from crewai.tools import BaseTool  # Import from crewai.tools instead of crewai_tools

from app.core.config import settings
from app.core.logging import logger


def create_resume_optimizer_agent(tools: Optional[List[Any]] = None) -> Agent:
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
    
    # Get API key from environment or settings
    api_key = os.environ.get("OPENAI_API_KEY") or settings.OPENAI_API_KEY or settings.LLM_API_KEY
    if not api_key:
        logger.warning("No API key found for LLM in optimizer agent")
    
    # Get model name from settings or default
    model_name = settings.AGENT_LLM or "gpt-4o"
    
    # Create LLM instance with explicit parameters
    llm = LLM(api_key=api_key, model=model_name)
    logger.info(f"Created LLM instance for optimizer agent with model: {model_name}")
    
    # Set memory config
    memory_enabled = settings.MEMORY_ENABLED if hasattr(settings, 'MEMORY_ENABLED') else True
    memory_config = None
    if memory_enabled:
        memory_config = {
            "max_tokens": 8000,  # Reasonable token limit
            "importance_threshold": 0.6  # Only retain important information
        }
    
    return Agent(
        role="Resume Optimizer",
        goal=(
            "Create tailored resumes that match specific job requirements "
            "while accurately representing the candidate's background"
        ),
        backstory=backstory,
        tools=tools or [],
        verbose=settings.AGENT_VERBOSE,
        llm=llm,  # Pass explicit LLM instance
        memory=memory_enabled,  # Enable memory for the optimizer
        memory_config=memory_config,  # Configure memory parameters
        allow_delegation=False  # Disable delegation to simplify flow
    )
