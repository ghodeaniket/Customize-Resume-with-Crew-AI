"""Service for setting up CrewAI agents and tools."""
from typing import Dict, List, Any
from crewai import LLM, Agent, Crew, Process

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
    
    def create_llm(self) -> LLM:
        """Create an LLM instance for CrewAI.
        
        Returns:
            LLM: LLM instance
            
        Raises:
            CustomizationError: If no API key is configured
        """
        api_key = self.environment_service.get_api_key()
        if not api_key:
            raise CustomizationError("No LLM API key configured")
        
        model_name = self.environment_service.get_model_name()
        
        # Initialize LLM with explicit parameters
        llm = LLM(api_key=api_key, model=model_name)
        logger.info(f"Initialized LLM with model: {model_name}")
        
        return llm
    
    async def create_tools(self, resume_service_instance: Any) -> List[Any]:
        """Create tools for CrewAI agents.
        
        Args:
            resume_service_instance: Resume service instance for tool creation
            
        Returns:
            List[Any]: List of tools
        """
        # Try with class-based tools first
        try:
            from app.crews.tools.resume_processor import ResumeProcessorTool, JobMatcherTool
            
            # Create class-based tool instances
            resume_processor_tool = ResumeProcessorTool(resume_service=resume_service_instance)
            job_matcher_tool = JobMatcherTool() 
            
            logger.info("Created class-based tools for CrewAI integration")
            return [resume_processor_tool, job_matcher_tool]
            
        except Exception as tool_error:
            # Fallback to function-based tools if class-based tools fail
            logger.warning(
                f"Class-based tools failed: {str(tool_error)}, "
                "falling back to function-based tools"
            )
            
            from app.crews.tools.resume_processor import (
                create_resume_processor_tool, 
                create_job_matcher_tool
            )
            
            # Create function-based tool instances
            resume_processor = create_resume_processor_tool(resume_service_instance)
            job_matcher = create_job_matcher_tool()
            
            logger.info(
                f"Created function-based tools: {type(resume_processor)}, "
                f"{type(job_matcher)}"
            )
            return [resume_processor, job_matcher]
    
    async def create_agents(self, llm: LLM, tools: List[Any]) -> Dict[str, Agent]:
        """Create agents for CrewAI.
        
        Args:
            llm: LLM instance
            tools: List of tools
            
        Returns:
            Dict[str, Agent]: Dictionary of agent name to agent
        """
        from app.crews.agents import (
            create_resume_analyzer_agent, 
            create_resume_optimizer_agent
        )
        
        # Create analyzer agent
        analyzer_agent = create_resume_analyzer_agent(tools=tools)
        analyzer_agent.llm = llm
        
        # Create optimizer agent
        optimizer_agent = create_resume_optimizer_agent(tools=tools)
        optimizer_agent.llm = llm
        
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
