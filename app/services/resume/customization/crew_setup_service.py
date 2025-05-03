"""Service for setting up CrewAI agents and tools."""
from typing import Dict, List, Any
from crewai import Agent, Crew, Process

from app.core.logging import logger
from app.core.config import settings
from app.core.exceptions import CustomizationError
from app.services.resume.core.crew_environment_service import CrewEnvironmentService


class CrewSetupService:
    """Service for setting up CrewAI components."""
    
    def __init__(self):
        """Initialize the CrewAI setup service."""
        self.environment_service = CrewEnvironmentService()
    
    def setup_environment(self) -> None:
        """Set up the LLM environment for CrewAI."""
        self.environment_service.setup_llm_environment()
    
    def create_llm(self) -> Dict[str, str]:
        """Create LLM configuration for CrewAI.
        
        Returns:
            Dict[str, str]: LLM configuration dictionary
            
        Raises:
            CustomizationError: If no API key is configured
        """
        api_key = self.environment_service.get_api_key()
        if not api_key:
            raise CustomizationError("No LLM API key configured")
        
        model_name = self.environment_service.get_model_name()
        
        # Return configuration dictionary instead of LLM instance
        llm_config = {
            "api_key": api_key,
            "model": model_name
        }
        logger.info(f"Created LLM configuration with model: {model_name}")
        
        return llm_config
    
    async def create_tools(self, resume_service_instance: Any) -> List[Any]:
        """Create tools for CrewAI agents.
        
        Args:
            resume_service_instance: Resume service instance for tool creation
            
        Returns:
            List[Any]: List of tools
        """
        # Use function-based tools directly as they are more compatible with CrewAI
        logger.info("Creating function-based tools for CrewAI integration")
        
        from app.crews.tools.resume_processor import (
            create_resume_processor_tool, 
            create_job_matcher_tool
        )
        
        # Create function-based tool instances
        resume_processor = create_resume_processor_tool(resume_service_instance)
        job_matcher = create_job_matcher_tool()
        
        # These are already proper Tool instances - no need to log their types
        logger.info("Created function-based tools: resume_processor and job_matcher")
        
        return [resume_processor, job_matcher]
    
    async def create_agents(self, llm_config: Dict[str, str], tools: List[Any]) -> Dict[str, Agent]:
        """Create agents for CrewAI.
        
        Args:
            llm_config: LLM configuration dictionary
            tools: List of tools
            
        Returns:
            Dict[str, Agent]: Dictionary of agent name to agent
        """
        # Use the new agent factory functions that properly handle LLM configuration
        from app.crews.agents import (
            create_resume_analyzer_agent_v2, 
            create_resume_optimizer_agent_v2
        )
        
        # Create analyzer agent
        analyzer_agent = create_resume_analyzer_agent_v2(tools=tools)
        
        # Create optimizer agent
        optimizer_agent = create_resume_optimizer_agent_v2(tools=tools)
        
        logger.info("Created analyzer and optimizer agents")
        
        return {
            "analyzer": analyzer_agent,
            "optimizer": optimizer_agent
        }
    
    def create_crew(self, agents: List[Agent], tasks: List[Any]) -> Crew:
        """Create a CrewAI crew instance.
        
        Args:
            agents: List of agents
            tasks: List of tasks
            
        Returns:
            Crew: Configured crew instance
        """
        crew = Crew(
            agents=agents,
            tasks=tasks,
            verbose=settings.CREW_VERBOSE,
            process=Process.sequential
        )
        
        logger.info("Created CrewAI crew with sequential process")
        return crew
