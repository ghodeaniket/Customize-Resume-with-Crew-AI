"""Document repository interface for document-related data access."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, BinaryIO
from pathlib import Path

from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Dict[str, Any], str], ABC):
    """Repository interface for document-related operations.
    
    This interface extends the base repository interface with
    document-specific operations such as saving document content,
    extracting text, and managing document metadata.
    """
    
    @abstractmethod
    async def save_document(
        self, content: bytes, task_id: str, original_filename: str
    ) -> Path:
        """Save document content to storage.
        
        Args:
            content: Document content bytes
            task_id: Unique task identifier
            original_filename: Original filename
            
        Returns:
            Path: Path to the saved document
        """
        pass
    
    @abstractmethod
    async def save_extracted_text(self, text: str, task_id: str) -> Path:
        """Save extracted text to storage.
        
        Args:
            text: Extracted text content
            task_id: Task identifier
            
        Returns:
            Path: Path to the saved text file
        """
        pass
    
    @abstractmethod
    async def save_metadata(self, task_id: str, metadata: Dict[str, Any]) -> Path:
        """Save metadata for a task.
        
        Args:
            task_id: Task identifier
            metadata: Metadata dictionary
            
        Returns:
            Path: Path to the metadata file
        """
        pass
    
    @abstractmethod
    async def get_metadata(self, task_id: str) -> Dict[str, Any]:
        """Get metadata for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Dict: Metadata dictionary
        """
        pass
    
    @abstractmethod
    async def get_extracted_text(self, task_id: str) -> Optional[str]:
        """Get extracted text for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[str]: Extracted text if available
        """
        pass
    
    @abstractmethod
    async def get_original_document_path(self, task_id: str) -> Optional[Path]:
        """Get the path to the original document.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Path]: Path to the original document if available
        """
        pass
    
    @abstractmethod
    async def save_result(self, task_id: str, result: str) -> Path:
        """Save task result to storage.
        
        Args:
            task_id: Task identifier
            result: Task result content
            
        Returns:
            Path: Path to the saved result file
        """
        pass
    
    @abstractmethod
    async def get_result(self, task_id: str) -> Optional[str]:
        """Get task result for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[str]: Task result if available
        """
        pass
    
    @abstractmethod
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents with their metadata.
        
        Returns:
            List[Dict]: List of documents with metadata
        """
        pass
