"""Application configuration."""
import os
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings


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
    
    # CrewAI settings
    AGENT_LLM: str = "gpt-4o"  # Default model for agents
    AGENT_VERBOSE: bool = True  # Enable verbose output for agents
    CREW_VERBOSE: bool = True   # Enable verbose output for crews
    MEMORY_ENABLED: bool = True  # Enable memory for agents
    MAX_EXECUTION_TIME: int = 300  # Maximum execution time in seconds
    MAX_RPM: Optional[int] = None  # Maximum requests per minute (None = no limit)
    
    class Config:
        """Pydantic configuration."""
        
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure uploads directory exists
Path(settings.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)
