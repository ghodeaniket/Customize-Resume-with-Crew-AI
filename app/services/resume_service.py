"""Service for resume processing and customization."""
import time
from typing import Dict, Optional, Any, BinaryIO
from pathlib import Path

from fastapi import UploadFile, BackgroundTasks

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError, ResumeNotFoundError
from app.infrastructure.document_processor import DocumentProcessor
from app.services.document_storage_service import DocumentStorageService


class ResumeService:
    """Service for processing and customizing resumes."""
    
    def __init__(
        self, 
        document_processor: DocumentProcessor,
        storage_service: DocumentStorageService
    ):
        """Initialize the resume service.
        
        Args:
            document_processor: Document processor for text extraction
            storage_service: Storage service for document persistence
        """
        self.document_processor = document_processor
        self.storage_service = storage_service
        logger.info("Initialized ResumeService")
    
    async def process_resume(
        self, file_content: bytes, filename: str, task_id: str
    ) -> Dict[str, Any]:
        """Process a resume file.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            task_id: Unique task identifier
            
        Returns:
            Dict[str, Any]: Processing result with metadata
            
        Raises:
            DocumentProcessingError: If processing fails
        """
        start_time = time.time()
        logger.info(f"Processing resume {filename} for task {task_id}")
        
        try:
            # Save original document
            file_path = await self.storage_service.save_document(
                file_content, task_id, filename
            )
            
            # Extract text
            extracted_text = await self.document_processor.extract_text_from_bytes(
                file_content, filename=filename
            )
            
            # Save extracted text
            text_path = await self.storage_service.save_extracted_text(
                extracted_text, task_id
            )
            
            # Update metadata with processing results
            metadata = {
                "status": "completed",
                "processing_time_ms": (time.time() - start_time) * 1000,
                "text_length": len(extracted_text)
            }
            await self.storage_service.save_metadata(task_id, metadata)
            
            logger.info(
                f"Resume processing completed for task {task_id}, "
                f"extracted {len(extracted_text)} characters"
            )
            
            result = {
                "task_id": task_id,
                "filename": filename,
                "text": extracted_text,
                "text_path": str(text_path),
                "original_path": str(file_path),
                "status": "completed"
            }
            
            return result
            
        except Exception as e:
            # Update metadata with error
            error_metadata = {
                "status": "failed",
                "error": str(e),
                "processing_time_ms": (time.time() - start_time) * 1000
            }
            await self.storage_service.save_metadata(task_id, error_metadata)
            
            logger.error(f"Resume processing failed for task {task_id}: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Resume processing failed: {str(e)}")
    
    async def resume_exists(self, task_id: str) -> bool:
        """Check if a resume exists.
        
        Args:
            task_id: Task identifier
            
        Returns:
            bool: True if the resume exists, False otherwise
        """
        logger.debug(f"Checking if resume {task_id} exists")
        
        metadata = await self.storage_service.get_metadata(task_id)
        document_path = await self.storage_service.get_original_document_path(task_id)
        
        return bool(metadata and document_path)
    
    async def get_resume_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get resume data by task ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Resume data if available
        """
        logger.debug(f"Getting resume data for task {task_id}")
        
        if not await self.resume_exists(task_id):
            logger.warning(f"Resume {task_id} does not exist")
            return None
        
        try:
            # Get metadata and extracted text
            metadata = await self.storage_service.get_metadata(task_id)
            extracted_text = await self.storage_service.get_extracted_text(task_id)
            
            if not extracted_text:
                logger.warning(f"No extracted text found for resume {task_id}")
            
            return {
                "task_id": task_id,
                "metadata": metadata,
                "text": extracted_text,
                "status": metadata.get("status", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Error getting resume data for task {task_id}: {str(e)}", exc_info=True)
            return None
    
    async def customize_resume(
        self, resume_id: str, job_description: str, task_id: str
    ) -> str:
        """Customize a resume based on a job description.
        
        Args:
            resume_id: Resume task identifier
            job_description: Job description text
            task_id: New task identifier for customization
            
        Returns:
            str: Task ID for the customization task
            
        Raises:
            ResumeNotFoundError: If the resume doesn't exist
        """
        # This will be fully implemented in Phase 2
        logger.info(f"Starting resume customization for resume {resume_id}")
        
        if not await self.resume_exists(resume_id):
            raise ResumeNotFoundError(resume_id)
        
        # Update metadata for the new task
        await self.storage_service.save_metadata(task_id, {
            "status": "processing",
            "resume_id": resume_id,
            "customization_type": "job_description",
            "started_at": time.time()
        })
        
        return task_id


# Factory function is now in dependencies.py
