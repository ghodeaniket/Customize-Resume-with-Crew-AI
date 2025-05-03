"""Base agent implementation with common functionality.

This module provides a base agent class with common functionality
shared by all Resume Customizer agents.
"""
import os
from typing import Optional, List, Any, Dict
from dataclasses import dataclass

from crewai import Agent, LLM
from crewai.tools import BaseTool

from app.core.config import settings
from app.core.logging import logger


@dataclass
class AgentConfig:
    """Configuration for a Resume Customizer agent."""
    role: str
    goal: str
    backstory: str
    verbose: bool = True
    allow_delegation: bool = False
    memory: bool = True
    memory_config: Optional[Dict] = None


class BaseResumAgent:
    """Base class for Resume Customizer agents.
    
    This class provides common functionality for all agents including:
    - LLM configuration
    - Memory setup  
    - Tool management
    - Error handling
    - Logging
    """
    
    def __init__(
        self,
        config: AgentConfig,
        tools: Optional[List[Any]] = None
    ):
        """Initialize the base agent with configuration and tools.
        
        Args:
            config: Agent configuration
            tools: List of tools for the agent to use
        """
        self.config = config
        self.tools = tools or []
        self._llm = None
        self._agent = None
        
        logger.info(f"Initializing {config.role} agent")
    
    def _setup_llm(self) -> LLM:
        """Set up LLM instance with proper API key and configuration.
        
        Returns:
            LLM: Configured LLM instance
        """
        logger.info(f"Setting up LLM for {self.config.role} agent")
        
        # Get API key from environment or settings
        api_key = (
            os.environ.get("OPENAI_API_KEY") or 
            settings.OPENAI_API_KEY or 
            settings.LLM_API_KEY
        )
        
        if not api_key:
            logger.warning(f"No API key found for LLM in {self.config.role} agent")
        
        # Get model name from settings or default
        model_name = settings.AGENT_LLM or "gpt-4o"
        
        # Create LLM instance
        llm = LLM(api_key=api_key, model=model_name)
        logger.info(f"Created LLM instance for {self.config.role} agent with model: {model_name}")
        
        return llm
    
    def _setup_memory_config(self) -> Optional[Dict]:
        """Set up memory configuration for the agent.
        
        Returns:
            Optional[Dict]: Memory configuration if enabled
        """
        if not self.config.memory:
            return None
        
        # Use provided memory config or default
        if self.config.memory_config:
            return self.config.memory_config
        
        # Default memory configuration
        return {
            "max_tokens": 8000,  # Reasonable token limit
            "importance_threshold": 0.6  # Only retain important information
        }
    
    def create_agent(self) -> Agent:
        """Create and return the CrewAI agent.
        
        Returns:
            Agent: Configured CrewAI agent
        """
        if self._agent:
            return self._agent
        
        logger.info(f"Creating {self.config.role} agent")
        
        # Set up LLM
        self._llm = self._setup_llm()
        
        # Set up memory config
        memory_config = self._setup_memory_config()
        
        # Create agent
        self._agent = Agent(
            role=self.config.role,
            goal=self.config.goal,
            backstory=self.config.backstory,
            tools=self.tools,
            verbose=self.config.verbose,
            llm=self._llm,
            memory=self.config.memory,
            memory_config=memory_config,
            allow_delegation=self.config.allow_delegation
        )
        
        logger.info(f"Successfully created {self.config.role} agent")
        return self._agent
    
    def add_tool(self, tool: Any) -> None:
        """Add a tool to the agent.
        
        Args:
            tool: Tool to add
        """
        self.tools.append(tool)
        
        # Update agent tools if agent is already created
        if self._agent:
            self._agent.tools = self.tools
    
    def remove_tool(self, tool_name: str) -> None:
        """Remove a tool from the agent by name.
        
        Args:
            tool_name: Name of the tool to remove
        """
        self.tools = [
            tool for tool in self.tools 
            if getattr(tool, 'name', '') != tool_name
        ]
        
        # Update agent tools if agent is already created
        if self._agent:
            self._agent.tools = self.tools
    
    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance, creating it if necessary.
        
        Returns:
            Agent: CrewAI agent instance
        """
        if not self._agent:
            self._agent = self.create_agent()
        return self._agent
    
    def reset_agent(self) -> None:
        """Reset the agent instance.
        
        This forces recreation of the agent on next use.
        """
        self._agent = None
        self._llm = None
        logger.info(f"Reset {self.config.role} agent")
