"""Resume optimization agent implementation.

This module provides the optimizer agent specialized for customizing
resumes to match specific job requirements.
"""
from typing import Optional, List, Any, Dict

from app.crews.agents.base import BaseResumAgent
from app.crews.agents.base.base_agent import AgentConfig
from app.core.config import settings
from app.core.logging import logger


class ResumeOptimizerAgent(BaseResumAgent):
    """Agent specialized for optimizing resumes based on job descriptions.
    
    The optimizer agent is responsible for:
    1. Tailoring resume content to highlight relevant skills and experiences
    2. Reorganizing resume sections to emphasize job-relevant information
    3. Adding keywords and phrases that match the job description
    4. Ensuring the resume passes ATS screening systems
    """
    
    def __init__(self, tools: Optional[List[Any]] = None):
        """Initialize the resume optimizer agent.
        
        Args:
            tools: Optional list of tools for the agent to use
        """
        logger.info("Initializing ResumeOptimizerAgent")
        
        # Define optimizer agent configuration
        config = AgentConfig(
            role="Resume Optimizer",
            goal=(
                "Create tailored resumes that match specific job requirements "
                "while accurately representing the candidate's background"
            ),
            backstory=(
                "You are a professional resume writer with expertise in customizing "
                "resumes to match specific job descriptions. You excel at highlighting "
                "relevant experience and skills to increase a candidate's chances of "
                "getting past ATS systems and impressing hiring managers. "
                "You understand the importance of maintaining authenticity while "
                "presenting the candidate's background in the most favorable light. "
                "You know exactly what recruiters and hiring managers look for and "
                "how to structure information to catch their attention."
            ),
            verbose=settings.AGENT_VERBOSE,
            allow_delegation=False,  # Disable delegation to simplify flow
            memory=True,
            memory_config={
                "max_tokens": 8000,
                "importance_threshold": 0.6
            }
        )
        
        super().__init__(config, tools)
    
    def optimize_for_ats(self, resume_text: str, keywords: List[str]) -> str:
        """Optimize resume content for ATS systems.
        
        Args:
            resume_text: Original resume text
            keywords: Keywords to incorporate
            
        Returns:
            str: ATS-optimized resume text
        """
        # This is a placeholder for ATS optimization
        # In a real implementation, this would use the agent to optimize
        return resume_text
    
    def reorder_sections(self, resume_text: str, priorities: List[str]) -> str:
        """Reorder resume sections based on priorities.
        
        Args:
            resume_text: Original resume text
            priorities: List of section priorities
            
        Returns:
            str: Resume with reordered sections
        """
        # This is a placeholder for section reordering
        # In a real implementation, this would use the agent to reorder
        return resume_text
    
    def get_customization_strategy(self, level: str) -> Dict[str, Any]:
        """Get customization strategy based on level.
        
        Args:
            level: Customization level (minimal, standard, comprehensive)
            
        Returns:
            Dict[str, Any]: Customization strategy parameters
        """
        strategies = {
            "minimal": {
                "content_preservation": 0.90,
                "keyword_density": "low",
                "structural_changes": "minimal",
                "description": (
                    "Make only the most essential changes to highlight relevant skills "
                    "and experiences. Focus on keyword matching and minor reorganization. "
                    "Maintain at least 90% of the original content."
                )
            },
            "standard": {
                "content_preservation": 0.75,
                "keyword_density": "medium",
                "structural_changes": "moderate",
                "description": (
                    "Make moderate changes to highlight relevant skills and experiences. "
                    "Adjust wording, reorganize content, and emphasize matching qualifications. "
                    "Maintain at least 75% of the original content while ensuring a good match."
                )
            },
            "comprehensive": {
                "content_preservation": 0.50,
                "keyword_density": "high",
                "structural_changes": "extensive",
                "description": (
                    "Make extensive changes to optimize the resume for this specific position. "
                    "Rewrite sections, reorganize content, and tailor the presentation for "
                    "maximum impact. Maintain factual accuracy but feel free to completely "
                    "restructure and reframe. Ensure the resume directly addresses at least "
                    "90% of the job requirements."
                )
            }
        }
        
        return strategies.get(level.lower(), strategies["standard"])


def create_resume_optimizer_agent(tools: Optional[List[Any]] = None) -> Any:
    """Create and return a configured resume optimizer agent.
    
    This factory function maintains backward compatibility with the
    existing codebase while using the new agent architecture.
    
    Args:
        tools: Optional list of tools for the agent to use
        
    Returns:
        CrewAI Agent: Configured resume optimizer agent
    """
    optimizer = ResumeOptimizerAgent(tools=tools)
    return optimizer.get_agent()
