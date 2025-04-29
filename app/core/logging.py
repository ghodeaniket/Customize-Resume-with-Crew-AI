"""Logging configuration using loguru."""
import sys
import os
from pathlib import Path

from loguru import logger

from app.core.config import settings


def setup_logging():
    """Configure logging for the application."""
    # Remove default loguru handler
    logger.remove()
    
    # Configure console output
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True,
    )
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Add file logger
    logger.add(
        "logs/resume_customizer.log",
        rotation="10 MB",
        retention="1 week",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )
    
    return logger


# Export configured logger
logger = setup_logging()
