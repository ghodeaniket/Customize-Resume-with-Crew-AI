"""Service for setting up CrewAI environment configuration."""
import os
from typing import Optional

from app.core.logging import logger
from app.core.config import settings
from app.core.exceptions import CustomizationError


class CrewEnvironmentService:
    """Service for managing CrewAI environment setup."""
    
    @staticmethod
    def setup_llm_environment() -> None:
        """Set up environment variables for LLM API keys.
        
        This method ensures that API keys are properly set in the environment
        for CrewAI components to access them.
        
        Raises:
            CustomizationError: If no API keys are configured
        """
        # Get API keys from settings
        llm_api_key = settings.LLM_API_KEY
        openai_api_key = settings.OPENAI_API_KEY
        
        # Log environment status without exposing keys
        logger.info(
            f"Setting up LLM environment. LLM_API_KEY exists: {bool(llm_api_key)}, "
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
        
        # Set verbose flags
        os.environ["AGENT_VERBOSE"] = str(settings.AGENT_VERBOSE).lower()
        os.environ["CREW_VERBOSE"] = str(settings.CREW_VERBOSE).lower()
        
        logger.info("LLM environment setup complete")
    
    @staticmethod
    def get_api_key() -> Optional[str]:
        """Get the configured API key for LLM operations.
        
        Returns:
            Optional[str]: API key if available
        """
        return settings.LLM_API_KEY or settings.OPENAI_API_KEY
    
    @staticmethod
    def get_model_name() -> str:
        """Get the configured model name.
        
        Returns:
            str: Model name to use
        """
        model_name = settings.AGENT_LLM
        if not model_name:
            model_name = "gpt-4o"  # Default to a reasonable model if not specified
            logger.warning(f"No LLM model specified, using default: {model_name}")
        
        return model_name
    
    @staticmethod
    def validate_environment() -> None:
        """Validate that the environment is properly configured for CrewAI.
        
        Raises:
            CustomizationError: If environment is not properly configured
        """
        if not CrewEnvironmentService.get_api_key():
            raise CustomizationError("No LLM API key configured")
        
        logger.info("CrewAI environment validation passed")
