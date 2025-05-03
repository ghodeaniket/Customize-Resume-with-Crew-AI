"""Service for resume text extraction operations."""
import time
from typing import Dict, Optional, Any, BinaryIO
from pathlib import Path

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError
from app.services.resume.base import BaseService
from app.infrastructure.document_processor import DocumentProcessor
from app.services.resume.storage_service import ResumeStorageService


class ResumeExtractionService(BaseService[Dict[str, Any], str]):
    """Service for handling resume text extraction.
    
    This service is responsible for processing resume documents and extracting
    text content for further analysis and customization. It coordinates between
    the document processor and storage service.
    """
    
    def __init__(
        self, 
        document_processor: DocumentProcessor,
        storage_service: ResumeStorageService
    ):
        """Initialize the resume extraction service.
        
        Args:
            document_processor: Document processor for text extraction
            storage_service: Storage service for persistence
        """
        self.document_processor = document_processor
        self.storage_service = storage_service
        logger.info("Initialized ResumeExtractionService")
    
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get extracted resume data by ID.
        
        Args:
            id: Resume identifier
            
        Returns:
            Optional[Dict[str, Any]]: Resume data with extracted text if found
        """
        try:
            # Get base resume data from storage service
            resume_data = await self.storage_service.get_by_id(id)
            
            if not resume_data:
                logger.debug(f"No resume data found for ID {id}")
                return None
            
            # Get extracted text
            extracted_text = await self.storage_service.get_extracted_text(id)
            
            if not extracted_text:
                logger.warning(f"No extracted text found for resume {id}")
            
            # Combine data
            resume_data["text"] = extracted_text
            resume_data["status"] = resume_data.get("metadata", {}).get("status", "unknown")
            
            return resume_data
            
        except Exception as e:
            logger.error(f"Error getting extracted resume data for ID {id}: {str(e)}", exc_info=True)
            return None
    
    async def exists(self, id: str) -> bool:
        """Check if an extracted resume exists.
        
        Args:
            id: Resume identifier
            
        Returns:
            bool: True if the resume exists with extracted text, False otherwise
        """
        if not await self.storage_service.exists(id):
            return False
            
        # Check if extracted text exists
        extracted_text = await self.storage_service.get_extracted_text(id)
        return extracted_text is not None
    
    async def extract_from_bytes(
        self, file_content: bytes, filename: str, task_id: str
    ) -> Dict[str, Any]:
        """Extract text from document bytes.
        
        Args:
            file_content: Document content bytes
            filename: Original filename
            task_id: Task identifier
            
        Returns:
            Dict[str, Any]: Extraction result with metadata
            
        Raises:
            DocumentProcessingError: If extraction fails
        """
        start_time = time.time()
        logger.info(f"Extracting text from {filename} for task {task_id}")
        
        try:
            # Save original document
            file_path = await self.storage_service.save_document(
                content=file_content,
                task_id=task_id,
                filename=filename
            )
            
            # Extract text
            extracted_text = await self.document_processor.extract_text_from_bytes(
                file_content, filename=filename
            )
            
            # Save extracted text
            text_path = await self.storage_service.save_extracted_text(
                text=extracted_text,
                task_id=task_id
            )
            
            # Update metadata with extraction results
            processing_time_ms = (time.time() - start_time) * 1000
            metadata = {
                "status": "completed",
                "processing_time_ms": processing_time_ms,
                "text_length": len(extracted_text),
                "extraction_completed_at": time.time()
            }
            await self.storage_service.save_metadata(task_id, metadata)
            
            logger.info(
                f"Text extraction completed for task {task_id}, "
                f"extracted {len(extracted_text)} characters in {processing_time_ms:.2f}ms"
            )
            
            return {
                "task_id": task_id,
                "filename": filename,
                "text": extracted_text,
                "text_path": str(text_path),
                "original_path": str(file_path),
                "status": "completed",
                "processing_time_ms": processing_time_ms
            }
            
        except Exception as e:
            error_message = f"Text extraction failed: {str(e)}"
            logger.error(f"Error extracting text for task {task_id}: {str(e)}", exc_info=True)
            
            # Update metadata with error
            error_metadata = {
                "status": "failed",
                "error": error_message,
                "processing_time_ms": (time.time() - start_time) * 1000
            }
            await self.storage_service.save_metadata(task_id, error_metadata)
            
            raise DocumentProcessingError(detail=error_message)
    
    async def process_resume(
        self, file_content: bytes, filename: str, task_id: str
    ) -> Dict[str, Any]:
        """Process a resume file end-to-end.
        
        This is the main method for processing a resume file, which coordinates
        the entire extraction workflow including document saving, text extraction,
        and metadata management.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            task_id: Unique task identifier
            
        Returns:
            Dict[str, Any]: Processing result with metadata
            
        Raises:
            DocumentProcessingError: If processing fails
        """
        logger.info(f"Processing resume {filename} for task {task_id}")
        
        # Update initial metadata
        initial_metadata = {
            "status": "processing",
            "filename": filename,
            "file_size": len(file_content),
            "started_at": time.time()
        }
        await self.storage_service.save_metadata(task_id, initial_metadata)
        
        # Extract text
        return await self.extract_from_bytes(
            file_content=file_content,
            filename=filename,
            task_id=task_id
        )


# Factory function for dependency injection
def get_resume_extraction_service(
    document_processor: DocumentProcessor,
    storage_service: ResumeStorageService
) -> ResumeExtractionService:
    """Get resume extraction service instance.
    
    Args:
        document_processor: Document processor
        storage_service: Storage service
        
    Returns:
        ResumeExtractionService: Resume extraction service instance
    """
    return ResumeExtractionService(
        document_processor=document_processor,
        storage_service=storage_service
    )
