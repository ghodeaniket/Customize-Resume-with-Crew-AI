"""Resume analysis agent for extracting key information from resumes and job descriptions."""
from typing import Dict, List, Optional, Any, Union
import os

from crewai import Agent, LLM
from crewai.tools import BaseTool  # Import from crewai.tools instead of crewai_tools

from app.core.config import settings
from app.core.logging import logger


def create_resume_analyzer_agent(tools: Optional[List[Any]] = None) -> Agent:
    """Create an agent for analyzing resumes and job descriptions.
    
    The analyzer agent is responsible for:
    1. Extracting key skills, experiences, and qualifications from resumes
    2. Identifying requirements and preferences from job descriptions
    3. Performing gap analysis between resumes and job descriptions
    
    Args:
        tools: Optional list of tools for the agent to use
        
    Returns:
        Agent: Configured resume analyzer agent
    """
    logger.info("Creating resume analyzer agent")
    
    backstory = (
        "You are an expert in parsing and analyzing documents related to job applications. "
        "Your specialty is identifying the most important skills, experiences, and "
        "qualifications in both resumes and job descriptions. "
        "You have years of experience working with ATS (Applicant Tracking Systems) "
        "and understand how these systems evaluate resumes against job descriptions. "
        "You are meticulous in your analysis and can recognize both explicit and "
        "implicit requirements in job postings."
    )
    
    # Get API key from environment or settings
    api_key = os.environ.get("OPENAI_API_KEY") or settings.OPENAI_API_KEY or settings.LLM_API_KEY
    if not api_key:
        logger.warning("No API key found for LLM in analyzer agent")
    
    # Get model name from settings or default
    model_name = settings.AGENT_LLM or "gpt-4o"
    
    # Create LLM instance with explicit parameters
    llm = LLM(api_key=api_key, model=model_name)
    logger.info(f"Created LLM instance for analyzer agent with model: {model_name}")
    
    return Agent(
        role="Resume Analyzer",
        goal=(
            "Analyze resumes and job descriptions to identify key skills, "
            "experiences, qualifications, and potential gaps"
        ),
        backstory=backstory,
        tools=tools or [],
        verbose=settings.AGENT_VERBOSE,
        llm=llm,  # Pass explicit LLM instance
        allow_delegation=False  # Disable delegation to simplify flow
    )
