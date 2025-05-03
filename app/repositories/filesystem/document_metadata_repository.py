"""Document metadata repository for file system operations."""
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any

import aiofiles

from app.core.logging import logger
from app.repositories.filesystem.base_repository import FileSystemBaseRepository
from app.repositories.filesystem.document_storage_repository import DocumentStorageRepository


class DocumentMetadataRepository(FileSystemBaseRepository):
    """Repository for managing document metadata operations."""
    
    def __init__(self, base_path: str):
        """Initialize the document metadata repository.
        
        Args:
            base_path: Base directory for storing documents
        """
        super().__init__(base_path)
        self.storage_repository = DocumentStorageRepository(base_path)
    
    async def save(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Save a document entity.
        
        Args:
            entity: Document entity to save
            
        Returns:
            Dict[str, Any]: Saved document entity
        """
        task_id = entity.get("task_id")
        if not task_id:
            task_id = str(uuid.uuid4())
            entity["task_id"] = task_id
        
        # Save metadata
        await self.save_metadata(task_id, entity)
        
        return entity
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Find a document by ID.
        
        Args:
            id: Document ID
            
        Returns:
            Optional[Dict[str, Any]]: Document if found, None otherwise
        """
        metadata = await self.get_metadata(id)
        if not metadata:
            return None
        
        # Add extracted text if available
        extracted_text = await self.storage_repository.get_extracted_text(id)
        if extracted_text:
            metadata["text"] = extracted_text
        
        return metadata
    
    async def find_all(self) -> List[Dict[str, Any]]:
        """Find all documents.
        
        Returns:
            List[Dict[str, Any]]: List of all documents
        """
        return await self.list_documents()
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a document by ID.
        
        Args:
            id: Document ID
            data: Data to update
            
        Returns:
            Optional[Dict[str, Any]]: Updated document if found, None otherwise
        """
        metadata = await self.get_metadata(id)
        if not metadata:
            return None
        
        # Update metadata
        metadata.update(data)
        await self.save_metadata(id, metadata)
        
        return metadata
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents with their metadata.
        
        Returns:
            List[Dict]: List of documents with metadata
        """
        documents = []
        
        for task_dir in self.base_path.iterdir():
            if not task_dir.is_dir():
                continue
            
            metadata_path = task_dir / "metadata.json"
            if metadata_path.exists():
                try:
                    async with aiofiles.open(metadata_path, "r", encoding="utf-8") as f:
                        content = await f.read()
                        metadata = json.loads(content)
                        documents.append({
                            "task_id": task_dir.name,
                            **metadata
                        })
                except Exception as e:
                    logger.warning(f"Error reading metadata for task {task_dir.name}: {str(e)}")
        
        return documents
