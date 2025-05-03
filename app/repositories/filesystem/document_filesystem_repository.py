"""Consolidated file system document repository."""
from pathlib import Path
from typing import Dict, List, Optional, Any

from app.core.config import settings
from app.repositories.document_repository import DocumentRepository
from app.repositories.filesystem.document_metadata_repository import DocumentMetadataRepository
from app.repositories.filesystem.document_storage_repository import DocumentStorageRepository


class FileSystemDocumentRepository(DocumentRepository):
    """File system implementation of the document repository.
    
    This implementation stores documents, extracted text, metadata,
    and results as files in the file system, using dedicated repositories.
    """
    
    def __init__(self, base_path: str = settings.UPLOADS_DIR):
        """Initialize file system document repository.
        
        Args:
            base_path: Base directory for storing documents
        """
        self.base_path = Path(base_path)
        self.metadata_repo = DocumentMetadataRepository(base_path)
        self.storage_repo = DocumentStorageRepository(base_path)
    
    async def save(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Save a document entity."""
        return await self.metadata_repo.save(entity)
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Find a document by ID."""
        return await self.metadata_repo.find_by_id(id)
    
    async def find_all(self) -> List[Dict[str, Any]]:
        """Find all documents."""
        return await self.metadata_repo.find_all()
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a document by ID."""
        return await self.metadata_repo.update(id, data)
    
    async def delete(self, id: str) -> bool:
        """Delete a document by ID."""
        return await self.metadata_repo.delete(id)
    
    async def exists(self, id: str) -> bool:
        """Check if a document exists by ID."""
        return await self.metadata_repo.exists(id)
    
    async def save_document(
        self, content: bytes, task_id: str, original_filename: str
    ) -> Path:
        """Save document content to disk with a unique ID."""
        return await self.storage_repo.save_document(content, task_id, original_filename)
    
    async def save_extracted_text(self, text: str, task_id: str) -> Path:
        """Save extracted text to disk."""
        return await self.storage_repo.save_extracted_text(text, task_id)
    
    async def save_metadata(self, task_id: str, metadata: Dict[str, Any]) -> Path:
        """Save metadata for a task."""
        return await self.metadata_repo.save_metadata(task_id, metadata)
    
    async def get_metadata(self, task_id: str) -> Dict[str, Any]:
        """Get metadata for a task."""
        return await self.metadata_repo.get_metadata(task_id)
    
    async def get_extracted_text(self, task_id: str) -> Optional[str]:
        """Get extracted text for a task."""
        return await self.storage_repo.get_extracted_text(task_id)
    
    async def get_original_document_path(self, task_id: str) -> Optional[Path]:
        """Get the path to the original document."""
        return await self.storage_repo.get_original_document_path(task_id)
    
    async def save_result(self, task_id: str, result: str) -> Path:
        """Save task result to disk."""
        return await self.storage_repo.save_result(task_id, result)
    
    async def get_result(self, task_id: str) -> Optional[str]:
        """Get task result for a task."""
        return await self.storage_repo.get_result(task_id)
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents with their metadata."""
        return await self.metadata_repo.list_documents()
