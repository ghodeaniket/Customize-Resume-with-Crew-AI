"""Base flow implementation with common functionality.

This module provides a base flow class with common functionality
shared by all Resume Customizer flows.
"""
import os
from typing import Optional, TypeVar, Generic, Dict, Any
from datetime import datetime

from crewai.flow.flow import Flow
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import CustomizationError

T = TypeVar('T', bound=BaseModel)


class BaseResumeFlow(Flow[T], Generic[T]):
    """Base class for Resume Customizer flows.
    
    This class provides common functionality for all flows including:
    - LLM environment setup
    - Error handling
    - Logging
    - State management
    - Performance monitoring
    """
    
    def __init__(
        self,
        task_id: str,
        initial_state: T,
        services: Optional[Dict[str, Any]] = None
    ):
        """Initialize the base flow.
        
        Args:
            task_id: Unique identifier for the task
            initial_state: Initial state for the flow
            services: Optional dictionary of services for dependency injection
        """
        super().__init__()
        
        self.task_id = task_id
        self.services = services or {}
        
        # Set initial state
        self.set_initial_state(initial_state)
        
        # Initialize timing
        self.start_time = None
        self.end_time = None
        
        logger.info(f"Initialized flow for task {task_id}")
    
    def _setup_llm_environment(self) -> None:
        """Set up environment variables for LLM API keys.
        
        This method ensures that API keys are properly set in the environment
        for CrewAI components to access them.
        """
        # Get API keys from settings
        llm_api_key = settings.LLM_API_KEY
        openai_api_key = settings.OPENAI_API_KEY
        
        # Log environment status without exposing keys
        logger.info(
            f"Setting up LLM environment. "
            f"LLM_API_KEY exists: {bool(llm_api_key)}, "
            f"OPENAI_API_KEY exists: {bool(openai_api_key)}"
        )
        
        # Set environment variables if they exist in settings
        if llm_api_key:
            os.environ["LLM_API_KEY"] = llm_api_key
            logger.debug("Set LLM_API_KEY in environment")
        
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
            logger.debug("Set OPENAI_API_KEY in environment")
        
        # Validate that we have at least one API key
        if not (llm_api_key or openai_api_key):
            logger.error("No API keys found in settings or environment")
            raise CustomizationError(
                "No LLM API keys configured. Please set LLM_API_KEY or OPENAI_API_KEY."
            )
        
        # Set LLM model in environment if specified
        if settings.AGENT_LLM:
            os.environ["AGENT_LLM"] = settings.AGENT_LLM
            logger.debug(f"Set AGENT_LLM in environment: {settings.AGENT_LLM}")
        
        # Set verbosity settings
        os.environ["AGENT_VERBOSE"] = str(settings.AGENT_VERBOSE).lower()
        os.environ["CREW_VERBOSE"] = str(settings.CREW_VERBOSE).lower()
        
        logger.info("LLM environment setup complete")
    
    def get_service(self, service_name: str) -> Any:
        """Get a service by name.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            Any: Service instance if found
            
        Raises:
            ValueError: If service not found
        """
        service = self.services.get(service_name)
        if not service:
            raise ValueError(f"Service '{service_name}' not found")
        return service
    
    def start_flow(self) -> None:
        """Start the flow execution and record start time."""
        self.start_time = datetime.now()
        logger.info(f"Starting flow execution for task {self.task_id}")
    
    def end_flow(self) -> None:
        """End the flow execution and record end time."""
        self.end_time = datetime.now()
        logger.info(f"Ended flow execution for task {self.task_id}")
    
    def get_execution_time(self) -> Optional[float]:
        """Get the total execution time in seconds.
        
        Returns:
            Optional[float]: Execution time in seconds if flow has completed
        """
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def handle_error(self, error: Exception, context: str = "") -> None:
        """Handle errors in a standardized way.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
        """
        error_msg = f"Error in flow {self.task_id}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        
        logger.error(error_msg, exc_info=True)
        
        # Update state if it has error fields
        if hasattr(self.state, 'status'):
            self.state.status = 'failed'
        if hasattr(self.state, 'error_message'):
            self.state.error_message = str(error)
    
    def validate_state(self) -> bool:
        """Validate the current state.
        
        Returns:
            bool: True if state is valid
        """
        try:
            # Pydantic models validate themselves
            self.state.model_validate(self.state.model_dump())
            return True
        except Exception as e:
            logger.error(f"State validation failed: {str(e)}")
            return False
    
    def get_flow_metrics(self) -> Dict[str, Any]:
        """Get metrics about the flow execution.
        
        Returns:
            Dict[str, Any]: Flow execution metrics
        """
        metrics = {
            "task_id": self.task_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time_seconds": self.get_execution_time(),
            "state_valid": self.validate_state()
        }
        
        # Add state-specific metrics if available
        if hasattr(self.state, 'progress'):
            metrics["progress"] = self.state.progress
        if hasattr(self.state, 'status'):
            metrics["status"] = self.state.status
        
        return metrics
