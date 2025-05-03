"""Base repository for file system operations."""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

import aiofiles

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError


class FileSystemBaseRepository:
    """Base repository for common file system operations."""
    
    def __init__(self, base_path: str):
        """Initialize the base repository.
        
        Args:
            base_path: Base directory for storing files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized file system base repository at {self.base_path}")
    
    async def save_metadata(self, task_id: str, metadata: Dict[str, Any]) -> Path:
        """Save metadata for a task.
        
        Args:
            task_id: Task identifier
            metadata: Metadata dictionary
            
        Returns:
            Path: Path to the metadata file
        """
        task_dir = self.base_path / task_id
        task_dir.mkdir(exist_ok=True)
        
        metadata_path = task_dir / "metadata.json"
        
        # Load existing metadata if it exists
        existing_metadata = {}
        if metadata_path.exists():
            try:
                async with aiofiles.open(metadata_path, "r", encoding="utf-8") as f:
                    content = await f.read()
                    existing_metadata = json.loads(content)
            except Exception as e:
                logger.warning(f"Error reading existing metadata: {str(e)}")
        
        # Update with new metadata
        existing_metadata.update(metadata)
        
        # Write updated metadata
        try:
            async with aiofiles.open(metadata_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(existing_metadata, indent=2))
            
            logger.debug(f"Saved metadata to {metadata_path}")
            return metadata_path
            
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Error saving metadata: {str(e)}")
    
    async def get_metadata(self, task_id: str) -> Dict[str, Any]:
        """Get metadata for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Dict: Metadata dictionary
        """
        metadata_path = self.base_path / task_id / "metadata.json"
        
        if not metadata_path.exists():
            logger.warning(f"Metadata file does not exist: {metadata_path}")
            return {}
        
        try:
            async with aiofiles.open(metadata_path, "r", encoding="utf-8") as f:
                content = await f.read()
                return json.loads(content)
                
        except Exception as e:
            logger.error(f"Error reading metadata: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Error reading metadata: {str(e)}")
    
    async def delete(self, id: str) -> bool:
        """Delete all files for an ID.
        
        Args:
            id: Task/document ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        task_dir = self.base_path / id
        if not task_dir.exists():
            return False
        
        # Delete all files in the directory
        for file in task_dir.iterdir():
            file.unlink()
        
        # Delete the directory
        task_dir.rmdir()
        
        return True
    
    async def exists(self, id: str) -> bool:
        """Check if an ID exists.
        
        Args:
            id: Task/document ID
            
        Returns:
            bool: True if exists, False otherwise
        """
        task_dir = self.base_path / id
        return task_dir.exists()
    
    def get_task_directory(self, task_id: str) -> Path:
        """Get the directory for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Path: Task directory path
        """
        task_dir = self.base_path / task_id
        task_dir.mkdir(exist_ok=True)
        return task_dir
