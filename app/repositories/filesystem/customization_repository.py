"""Customization repository for storing customized resumes."""
import time
from pathlib import Path
from typing import Dict, Any, Optional

import aiofiles

from app.core.logging import logger
from app.core.config import settings
from app.core.exceptions import DocumentProcessingError


class CustomizationRepository:
    """Repository for storing customized resumes."""
    
    def __init__(self, base_path: str = settings.CUSTOMIZATIONS_DIR):
        """Initialize the customization repository.
        
        Args:
            base_path: Base directory for storing customized resumes
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized customization repository at {self.base_path}")
    
    def get_task_directory(self, task_id: str) -> Path:
        """Get the directory for a customization task.
        
        Args:
            task_id: Customization task identifier
            
        Returns:
            Path: Task directory path
        """
        task_dir = self.base_path / task_id
        task_dir.mkdir(exist_ok=True)
        return task_dir
    
    async def save_customized_text(self, text: str, task_id: str) -> Path:
        """Save customized resume text to disk.
        
        Args:
            text: Customized resume text content
            task_id: Customization task identifier
            
        Returns:
            Path: Path to the saved text file
            
        Raises:
            DocumentProcessingError: If saving fails
        """
        task_dir = self.get_task_directory(task_id)
        text_path = task_dir / "customized.txt"
        
        try:
            async with aiofiles.open(text_path, "w", encoding="utf-8") as f:
                await f.write(text)
            
            # Save basic metadata
            metadata_path = task_dir / "metadata.json"
            metadata = {
                "task_id": task_id,
                "customized_text_size": len(text),
                "created_at": time.time()
            }
            
            async with aiofiles.open(metadata_path, "w", encoding="utf-8") as f:
                import json
                await f.write(json.dumps(metadata, indent=2))
            
            logger.info(f"Saved customized text to {text_path}, size: {len(text)} characters")
            return text_path
            
        except Exception as e:
            logger.error(f"Error saving customized text: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Error saving customized text: {str(e)}")
    
    async def get_customized_text(self, task_id: str) -> Optional[str]:
        """Get customized text for a task.
        
        Args:
            task_id: Customization task identifier
            
        Returns:
            Optional[str]: Customized text if available
        """
        text_path = self.base_path / task_id / "customized.txt"
        
        if not text_path.exists():
            logger.warning(f"Customized text file does not exist: {text_path}")
            return None
        
        try:
            async with aiofiles.open(text_path, "r", encoding="utf-8") as f:
                return await f.read()
                
        except Exception as e:
            logger.error(f"Error reading customized text: {str(e)}", exc_info=True)
            return None
    
    async def exists(self, task_id: str) -> bool:
        """Check if a customization task exists.
        
        Args:
            task_id: Customization task identifier
            
        Returns:
            bool: True if exists, False otherwise
        """
        task_dir = self.base_path / task_id
        return task_dir.exists()
