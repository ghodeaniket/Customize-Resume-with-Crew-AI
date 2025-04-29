"""Document storage service for Resume Customizer."""
import os
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import aiofiles
from fastapi import UploadFile

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError


class DocumentStorageService:
    """Service for storing and retrieving documents."""
    
    def __init__(self, base_path: str = settings.UPLOADS_DIR):
        """Initialize document storage service.
        
        Args:
            base_path: Base directory for storing documents
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized document storage at {self.base_path}")
    
    async def save_document(
        self, 
        content: bytes, 
        task_id: str, 
        original_filename: str
    ) -> Path:
        """Save document content to disk with a unique ID.
        
        Args:
            content: Document content bytes
            task_id: Unique task identifier
            original_filename: Original filename
            
        Returns:
            Path: Path to the saved document
            
        Raises:
            DocumentProcessingError: If saving fails
        """
        # Create directory for this task
        task_dir = self.base_path / task_id
        task_dir.mkdir(exist_ok=True)
        
        # Get file extension
        ext = Path(original_filename).suffix.lower() if original_filename else ""
        
        # Save original file
        file_path = task_dir / f"original{ext}"
        
        try:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
            
            # Save metadata
            await self.save_metadata(task_id, {
                "original_filename": original_filename,
                "file_size": len(content),
                "file_extension": ext
            })
            
            logger.info(f"Saved document to {file_path}, size: {len(content)} bytes")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Error saving document: {str(e)}")
    
    async def save_extracted_text(self, text: str, task_id: str) -> Path:
        """Save extracted text to disk.
        
        Args:
            text: Extracted text content
            task_id: Task identifier
            
        Returns:
            Path: Path to the saved text file
            
        Raises:
            DocumentProcessingError: If saving fails
        """
        task_dir = self.base_path / task_id
        task_dir.mkdir(exist_ok=True)
        
        text_path = task_dir / "extracted.txt"
        
        try:
            async with aiofiles.open(text_path, "w", encoding="utf-8") as f:
                await f.write(text)
            
            # Update metadata
            metadata = await self.get_metadata(task_id)
            metadata.update({
                "extracted_text_path": str(text_path),
                "extracted_text_size": len(text)
            })
            await self.save_metadata(task_id, metadata)
            
            logger.info(f"Saved extracted text to {text_path}, size: {len(text)} characters")
            return text_path
            
        except Exception as e:
            logger.error(f"Error saving extracted text: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Error saving extracted text: {str(e)}")
    
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
            
        Raises:
            DocumentProcessingError: If metadata doesn't exist or can't be read
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
    
    async def get_extracted_text(self, task_id: str) -> Optional[str]:
        """Get extracted text for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[str]: Extracted text if available
        """
        text_path = self.base_path / task_id / "extracted.txt"
        
        if not text_path.exists():
            logger.warning(f"Extracted text file does not exist: {text_path}")
            return None
        
        try:
            async with aiofiles.open(text_path, "r", encoding="utf-8") as f:
                return await f.read()
                
        except Exception as e:
            logger.error(f"Error reading extracted text: {str(e)}", exc_info=True)
            return None
    
    async def get_original_document_path(self, task_id: str) -> Optional[Path]:
        """Get the path to the original document.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Path]: Path to the original document if available
        """
        task_dir = self.base_path / task_id
        
        if not task_dir.exists():
            logger.warning(f"Task directory does not exist: {task_dir}")
            return None
        
        # Try to find the original file
        for file in task_dir.iterdir():
            if file.name.startswith("original"):
                return file
        
        logger.warning(f"Original document not found in task directory: {task_dir}")
        return None
    
    async def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks with their metadata.
        
        Returns:
            List[Dict]: List of tasks with metadata
        """
        tasks = []
        
        for task_dir in self.base_path.iterdir():
            if not task_dir.is_dir():
                continue
            
            metadata_path = task_dir / "metadata.json"
            if metadata_path.exists():
                try:
                    async with aiofiles.open(metadata_path, "r", encoding="utf-8") as f:
                        content = await f.read()
                        metadata = json.loads(content)
                        tasks.append({
                            "task_id": task_dir.name,
                            **metadata
                        })
                except Exception as e:
                    logger.warning(f"Error reading metadata for task {task_dir.name}: {str(e)}")
        
        return tasks


# Factory function for dependency injection
def get_document_storage_service() -> DocumentStorageService:
    """Get document storage service instance.
    
    Returns:
        DocumentStorageService: Document storage service instance
    """
    return DocumentStorageService()
