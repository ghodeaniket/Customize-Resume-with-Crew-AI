"""Base task implementation with common functionality.

This module provides a base task class with common functionality
shared by all Resume Customizer tasks.
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass

from crewai import Agent, Task

from app.core.logging import logger


@dataclass
class TaskConfig:
    """Configuration for a Resume Customizer task."""
    name: str
    description: str
    expected_output: str
    async_execution: bool = False
    output_file: Optional[str] = None


class BaseResumeTask:
    """Base class for Resume Customizer tasks.
    
    This class provides common functionality for all tasks including:
    - Task configuration management
    - Error handling
    - Logging
    - Result validation
    """
    
    def __init__(self, config: TaskConfig):
        """Initialize the base task with configuration.
        
        Args:
            config: Task configuration
        """
        self.config = config
        self._task = None
        
        logger.info(f"Initializing {config.name} task")
    
    def create_task(self, agent: Agent, **kwargs) -> Task:
        """Create and return the CrewAI task.
        
        Args:
            agent: Agent to assign to the task
            **kwargs: Additional task parameters
            
        Returns:
            Task: Configured CrewAI task
        """
        logger.info(f"Creating {self.config.name} task")
        
        # Create task with configuration
        self._task = Task(
            description=self.config.description,
            expected_output=self.config.expected_output,
            agent=agent,
            async_execution=self.config.async_execution,
            output_file=self.config.output_file,
            **kwargs
        )
        
        logger.info(f"Successfully created {self.config.name} task")
        return self._task
    
    def get_task(self, agent: Agent, **kwargs) -> Task:
        """Get the CrewAI task instance, creating it if necessary.
        
        Args:
            agent: Agent to assign to the task
            **kwargs: Additional task parameters
            
        Returns:
            Task: CrewAI task instance
        """
        if not self._task:
            self._task = self.create_task(agent, **kwargs)
        return self._task
    
    def reset_task(self) -> None:
        """Reset the task instance.
        
        This forces recreation of the task on next use.
        """
        self._task = None
        logger.info(f"Reset {self.config.name} task")
    
    def validate_result(self, result: Any) -> bool:
        """Validate the task result.
        
        Args:
            result: Result to validate
            
        Returns:
            bool: True if result is valid
        """
        # Base validation - override in subclasses for specific validation
        return result is not None
