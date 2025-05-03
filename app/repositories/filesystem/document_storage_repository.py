"""Document storage repository for file system operations."""
import time
from pathlib import Path
from typing import Dict, Any, Optional

import aiofiles

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError
from app.repositories.filesystem.base_repository import FileSystemBaseRepository


class DocumentStorageRepository(FileSystemBaseRepository):
    """Repository for storing documents and related files."""
    
    async def save_document(
        self, content: bytes, task_id: str, original_filename: str
    ) -> Path:
        """Save document content to disk.
        
        Args:
            content: Document content bytes
            task_id: Unique task identifier
            original_filename: Original filename
            
        Returns:
            Path: Path to the saved document
            
        Raises:
            DocumentProcessingError: If saving fails
        """
        task_dir = self.get_task_directory(task_id)
        
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
        task_dir = self.get_task_directory(task_id)
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
    
    async def save_result(self, task_id: str, result: str) -> Path:
        """Save task result to disk.
        
        Args:
            task_id: Task identifier
            result: Task result content
            
        Returns:
            Path: Path to the saved result file
            
        Raises:
            DocumentProcessingError: If saving fails
        """
        task_dir = self.get_task_directory(task_id)
        result_path = task_dir / "result.txt"
        
        try:
            async with aiofiles.open(result_path, "w", encoding="utf-8") as f:
                await f.write(result)
            
            # Update metadata
            metadata = await self.get_metadata(task_id)
            metadata.update({
                "result_path": str(result_path),
                "result_size": len(result),
                "result_created_at": time.time()
            })
            await self.save_metadata(task_id, metadata)
            
            logger.info(f"Saved task result to {result_path}, size: {len(result)} characters")
            return result_path
            
        except Exception as e:
            logger.error(f"Error saving task result: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Error saving task result: {str(e)}")
    
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
    
    async def get_result(self, task_id: str) -> Optional[str]:
        """Get task result for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[str]: Task result if available
        """
        result_path = self.base_path / task_id / "result.txt"
        
        if not result_path.exists():
            logger.warning(f"Result file does not exist: {result_path}")
            return None
        
        try:
            async with aiofiles.open(result_path, "r", encoding="utf-8") as f:
                return await f.read()
                
        except Exception as e:
            logger.error(f"Error reading task result: {str(e)}", exc_info=True)
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
