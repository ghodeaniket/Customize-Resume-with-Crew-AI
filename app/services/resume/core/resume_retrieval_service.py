"""Service for retrieving and validating resume data."""
from typing import Dict, Any, Optional

from app.core.logging import logger
from app.core.exceptions import ResumeNotFoundError
from app.services.document_storage_service import DocumentStorageService


class ResumeRetrievalService:
    """Service for retrieving and validating resume data."""
    
    def __init__(self, storage_service: DocumentStorageService):
        """Initialize the resume retrieval service.
        
        Args:
            storage_service: Storage service for document retrieval
        """
        self.storage_service = storage_service
        logger.info("Initialized ResumeRetrievalService")
    
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
    
    async def get_resume_text(self, task_id: str) -> str:
        """Get resume text content.
        
        Args:
            task_id: Task identifier
            
        Returns:
            str: Resume text content
            
        Raises:
            ResumeNotFoundError: If resume doesn't exist
        """
        if not await self.resume_exists(task_id):
            logger.error(f"Resume {task_id} not found")
            raise ResumeNotFoundError(task_id)
        
        extracted_text = await self.storage_service.get_extracted_text(task_id)
        if not extracted_text:
            logger.error(f"No extracted text found for resume {task_id}")
            raise ResumeNotFoundError(task_id, "No extracted text available")
        
        return extracted_text
    
    async def get_resume_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get complete resume data by task ID.
        
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
    
    async def get_resume_metadata(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get resume metadata.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Resume metadata if available
        """
        if not await self.resume_exists(task_id):
            return None
        
        return await self.storage_service.get_metadata(task_id)
