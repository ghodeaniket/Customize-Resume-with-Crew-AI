"""Service for resume storage operations."""
import time
from typing import Dict, Optional, Any, BinaryIO, List
from pathlib import Path

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError
from app.services.resume.base import BaseService
from app.repositories.document_repository import DocumentRepository


class ResumeStorageService(BaseService[Dict[str, Any], str]):
    """Service for handling resume storage operations.
    
    This service is responsible for managing the storage aspects of resumes,
    including saving documents, extracting text, and managing metadata.
    It delegates actual storage operations to the document repository.
    """
    
    def __init__(self, document_repository: DocumentRepository):
        """Initialize the resume storage service.
        
        Args:
            document_repository: Repository for document data access
        """
        self.document_repository = document_repository
        logger.info("Initialized ResumeStorageService")
    
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get resume data by ID.
        
        Args:
            id: Resume identifier
            
        Returns:
            Optional[Dict[str, Any]]: Resume data if found
        """
        try:
            # Get metadata
            metadata = await self.document_repository.get_metadata(id)
            
            if not metadata:
                logger.debug(f"No metadata found for resume {id}")
                return None
            
            return {
                "task_id": id,
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"Error getting resume by ID {id}: {str(e)}", exc_info=True)
            return None
    
    async def exists(self, id: str) -> bool:
        """Check if a resume exists.
        
        Args:
            id: Resume identifier
            
        Returns:
            bool: True if the resume exists, False otherwise
        """
        return await self.document_repository.exists(id)
    
    async def save_document(
        self, content: bytes, task_id: str, filename: str
    ) -> Path:
        """Save document content.
        
        Args:
            content: Document content bytes
            task_id: Unique task identifier
            filename: Original filename
            
        Returns:
            Path: Path to the saved document
            
        Raises:
            DocumentProcessingError: If saving fails
        """
        try:
            return await self.document_repository.save_document(
                content=content,
                task_id=task_id,
                original_filename=filename
            )
        except Exception as e:
            logger.error(f"Error saving document {filename} for task {task_id}: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Error saving document: {str(e)}")
    
    async def save_extracted_text(self, text: str, task_id: str) -> Path:
        """Save extracted text.
        
        Args:
            text: Extracted text content
            task_id: Task identifier
            
        Returns:
            Path: Path to the saved text file
            
        Raises:
            DocumentProcessingError: If saving fails
        """
        try:
            return await self.document_repository.save_extracted_text(
                text=text,
                task_id=task_id
            )
        except Exception as e:
            logger.error(f"Error saving extracted text for task {task_id}: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Error saving extracted text: {str(e)}")
    
    async def save_metadata(self, task_id: str, metadata: Dict[str, Any]) -> Path:
        """Save metadata for a task.
        
        Args:
            task_id: Task identifier
            metadata: Metadata dictionary
            
        Returns:
            Path: Path to the metadata file
            
        Raises:
            DocumentProcessingError: If saving fails
        """
        try:
            return await self.document_repository.save_metadata(
                task_id=task_id,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error saving metadata for task {task_id}: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Error saving metadata: {str(e)}")
    
    async def get_metadata(self, task_id: str) -> Dict[str, Any]:
        """Get metadata for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Dict: Metadata dictionary
            
        Raises:
            DocumentProcessingError: If reading fails
        """
        try:
            return await self.document_repository.get_metadata(task_id)
        except Exception as e:
            logger.error(f"Error getting metadata for task {task_id}: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Error reading metadata: {str(e)}")
    
    async def get_extracted_text(self, task_id: str) -> Optional[str]:
        """Get extracted text for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[str]: Extracted text if available
        """
        try:
            return await self.document_repository.get_extracted_text(task_id)
        except Exception as e:
            logger.error(f"Error getting extracted text for task {task_id}: {str(e)}", exc_info=True)
            return None
    
    async def get_original_document_path(self, task_id: str) -> Optional[Path]:
        """Get the path to the original document.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Path]: Path to the original document if available
        """
        try:
            return await self.document_repository.get_original_document_path(task_id)
        except Exception as e:
            logger.error(f"Error getting document path for task {task_id}: {str(e)}", exc_info=True)
            return None
    
    async def save_result(self, task_id: str, result: str) -> Path:
        """Save task result.
        
        Args:
            task_id: Task identifier
            result: Task result content
            
        Returns:
            Path: Path to the saved result file
            
        Raises:
            DocumentProcessingError: If saving fails
        """
        try:
            return await self.document_repository.save_result(
                task_id=task_id,
                result=result
            )
        except Exception as e:
            logger.error(f"Error saving result for task {task_id}: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Error saving result: {str(e)}")
    
    async def get_result(self, task_id: str) -> Optional[str]:
        """Get task result.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[str]: Task result if available
        """
        try:
            return await self.document_repository.get_result(task_id)
        except Exception as e:
            logger.error(f"Error getting result for task {task_id}: {str(e)}", exc_info=True)
            return None
    
    async def list_resumes(self) -> List[Dict[str, Any]]:
        """List all resumes with their metadata.
        
        Returns:
            List[Dict]: List of resumes with metadata
        """
        try:
            documents = await self.document_repository.list_documents()
            
            # Filter for resume documents only
            resumes = [
                doc for doc in documents
                if doc.get("metadata", {}).get("type") != "customization"
            ]
            
            return resumes
        except Exception as e:
            logger.error(f"Error listing resumes: {str(e)}", exc_info=True)
            return []


# Factory function for dependency injection
def get_resume_storage_service(
    document_repository: DocumentRepository
) -> ResumeStorageService:
    """Get resume storage service instance.
    
    Args:
        document_repository: Document repository
        
    Returns:
        ResumeStorageService: Resume storage service instance
    """
    return ResumeStorageService(document_repository=document_repository)
