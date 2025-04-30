"""Application configuration."""
import os
from pathlib import Path
from typing import List, Optional, Dict

from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger


class Settings(BaseSettings):
    """Application settings."""
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Resume Customizer"
    DEBUG: bool = True
    
    # File storage settings
    UPLOADS_DIR: str = os.path.join(os.getcwd(), "uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # External API settings
    LLM_PROVIDER: str = "openai"  # or "anthropic", "google", etc.
    LLM_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None  # Added for compatibility
    
    # CrewAI settings
    AGENT_LLM: str = "gpt-4o"  # Default model for agents
    AGENT_VERBOSE: bool = True  # Enable verbose output for agents
    CREW_VERBOSE: bool = True   # Enable verbose output for crews
    MEMORY_ENABLED: bool = True  # Enable memory for agents
    MAX_EXECUTION_TIME: int = 300  # Maximum execution time in seconds
    MAX_RPM: Optional[int] = None  # Maximum requests per minute (None = no limit)
    
    # Use SettingsConfigDict instead of Config class for Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Allow extra fields in settings
    )


settings = Settings()

# Ensure uploads directory exists
Path(settings.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)


def validate_environment() -> Dict[str, bool]:
    """Validate required environment variables for the application.
    
    Returns:
        Dict[str, bool]: Dictionary with validation results for each requirement
    """
    validation_results = {}
    
    # Check for LLM API keys
    has_llm_api_key = bool(settings.LLM_API_KEY or os.environ.get("LLM_API_KEY"))
    has_openai_api_key = bool(settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY"))
    validation_results["has_llm_api_key"] = has_llm_api_key or has_openai_api_key
    
    if not validation_results["has_llm_api_key"]:
        logger.warning("No LLM API keys found. Set LLM_API_KEY or OPENAI_API_KEY in environment or .env file.")
    
    # Check for LLM model specification
    has_agent_llm = bool(settings.AGENT_LLM or os.environ.get("AGENT_LLM"))
    validation_results["has_agent_llm"] = has_agent_llm
    
    if not validation_results["has_agent_llm"]:
        logger.warning("No AGENT_LLM model specified. Using default.")
    
    # Check for upload directory
    uploads_dir_exists = Path(settings.UPLOADS_DIR).exists()
    validation_results["uploads_dir_exists"] = uploads_dir_exists
    
    if not uploads_dir_exists:
        logger.warning(f"Uploads directory {settings.UPLOADS_DIR} does not exist.")
        try:
            Path(settings.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created uploads directory: {settings.UPLOADS_DIR}")
            validation_results["uploads_dir_exists"] = True
        except Exception as e:
            logger.error(f"Failed to create uploads directory: {str(e)}")
    
    # Overall validation status
    validation_results["all_validated"] = all([
        validation_results["has_llm_api_key"],
        validation_results["uploads_dir_exists"]
    ])
    
    # Print validation summary
    logger.info(f"Environment validation results: {validation_results}")
    
    return validation_results
