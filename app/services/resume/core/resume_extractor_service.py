"""Service focused on resume document extraction and processing."""
import time
from typing import Dict, Any

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError
from app.infrastructure.document_processor import DocumentProcessor
from app.services.document_storage_service import DocumentStorageService


class ResumeExtractorService:
    """Service for extracting text from resume documents."""
    
    def __init__(
        self, 
        document_processor: DocumentProcessor,
        storage_service: DocumentStorageService
    ):
        """Initialize the resume extractor service.
        
        Args:
            document_processor: Document processor for text extraction
            storage_service: Storage service for document persistence
        """
        self.document_processor = document_processor
        self.storage_service = storage_service
        logger.info("Initialized ResumeExtractorService")
    
    async def extract_resume_text(
        self, file_content: bytes, filename: str, task_id: str
    ) -> Dict[str, Any]:
        """Extract text from a resume file.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            task_id: Unique task identifier
            
        Returns:
            Dict[str, Any]: Extraction result with metadata
            
        Raises:
            DocumentProcessingError: If extraction fails
        """
        start_time = time.time()
        logger.info(f"Extracting text from resume {filename} for task {task_id}")
        
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
            
            # Create extraction metadata
            metadata = {
                "status": "completed",
                "processing_time_ms": (time.time() - start_time) * 1000,
                "text_length": len(extracted_text),
                "filename": filename,
                "extraction_complete": True
            }
            
            await self.storage_service.save_metadata(task_id, metadata)
            
            logger.info(
                f"Resume extraction completed for task {task_id}, "
                f"extracted {len(extracted_text)} characters"
            )
            
            return {
                "task_id": task_id,
                "filename": filename,
                "text": extracted_text,
                "text_path": str(text_path),
                "original_path": str(file_path),
                "metadata": metadata
            }
            
        except Exception as e:
            # Update metadata with error
            error_metadata = {
                "status": "failed",
                "error": str(e),
                "processing_time_ms": (time.time() - start_time) * 1000,
                "extraction_complete": False
            }
            await self.storage_service.save_metadata(task_id, error_metadata)
            
            logger.error(f"Resume extraction failed for task {task_id}: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Resume extraction failed: {str(e)}")
            
    async def process_resume_document(
        self, file_content: bytes, filename: str, task_id: str
    ) -> str:
        """Process a resume document and return the extracted text.
        
        Simplified interface for extraction that only returns the text.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            task_id: Unique task identifier
            
        Returns:
            str: Extracted text content
            
        Raises:
            DocumentProcessingError: If processing fails
        """
        result = await self.extract_resume_text(file_content, filename, task_id)
        return result["text"]
