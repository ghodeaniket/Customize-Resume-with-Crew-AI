#!/usr/bin/env python3
"""
Implementation script for CrewAI integration fixes.

This script creates and updates the necessary files to fix the CrewAI integration
issues in the Resume Customizer application.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define project root
PROJECT_ROOT = Path(os.getcwd())

# Ensure necessary directories exist
DIRS = [
    PROJECT_ROOT / "app",
    PROJECT_ROOT / "app/api",
    PROJECT_ROOT / "app/core", 
    PROJECT_ROOT / "app/crews",
    PROJECT_ROOT / "app/crews/agents",
    PROJECT_ROOT / "app/crews/tasks",
    PROJECT_ROOT / "app/crews/tools",
    PROJECT_ROOT / "app/infrastructure",
    PROJECT_ROOT / "app/models",
    PROJECT_ROOT / "app/services",
    PROJECT_ROOT / "uploads"
]

# Create directories
for dir_path in DIRS:
    dir_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created directory: {dir_path}")

# File contents

# 1. Resume Processor Tool - Fixed implementation
RESUME_PROCESSOR_TOOL = """"""

# 2. Resume Service - Fixed implementation
RESUME_SERVICE = """"""

# 3. Config with environment validation
CONFIG = """"""

# 4. Main with startup validation
MAIN = """"""

# 5. Validation script
VALIDATION_SCRIPT = """"""

# 6. Test script for CrewAI integration
TEST_SCRIPT = """"""

# 7. Fixed agents
ANALYZER_AGENT = """import os
from typing import List, Optional, Any
from crewai import Agent, LLM
from app.core.config import settings
from app.core.logging import logger

def create_resume_analyzer_agent(tools: Optional[List[Any]] = None) -> Agent:
    """Create an agent for analyzing resumes and job descriptions."""
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
"""

OPTIMIZER_AGENT = """import os
from typing import List, Optional, Any
from crewai import Agent, LLM
from app.core.config import settings
from app.core.logging import logger

def create_resume_optimizer_agent(tools: Optional[List[Any]] = None) -> Agent:
    """Create an agent for optimizing resumes based on job descriptions."""
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
"""

# Apply changes
def write_file(path: Path, content: str):
    """Write content to file."""
    path.write_text(content)
    logger.info(f"Created/updated file: {path}")

# Write agent files
write_file(PROJECT_ROOT / "app/crews/agents/analyzer.py", ANALYZER_AGENT)
write_file(PROJECT_ROOT / "app/crews/agents/optimizer.py", OPTIMIZER_AGENT)

logger.info("CrewAI integration fixes implemented successfully!")
