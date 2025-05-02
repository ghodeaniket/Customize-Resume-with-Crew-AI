"""Base repository interface for data access."""
from abc import ABC, abstractmethod
from typing import Dict, List, Generic, TypeVar, Optional, Any
from uuid import UUID

# Define a type variable for the entity ID
ID = TypeVar('ID', str, UUID, int)

# Define a type variable for the entity
T = TypeVar('T')


class BaseRepository(Generic[T, ID], ABC):
    """Base interface for repository implementations.
    
    All repository implementations must implement this interface
    to ensure consistent data access patterns across the application.
    
    Type Parameters:
        T: The entity type managed by the repository
        ID: The ID type for the entity (str, UUID, int, etc.)
    """
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """Save an entity to the repository.
        
        Args:
            entity: The entity to save
            
        Returns:
            T: The saved entity
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, id: ID) -> Optional[T]:
        """Find an entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            Optional[T]: The entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_all(self) -> List[T]:
        """Find all entities.
        
        Returns:
            List[T]: List of all entities
        """
        pass
    
    @abstractmethod
    async def update(self, id: ID, data: Dict[str, Any]) -> Optional[T]:
        """Update an entity by ID.
        
        Args:
            id: Entity ID
            data: Data to update
            
        Returns:
            Optional[T]: The updated entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, id: ID) -> bool:
        """Delete an entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def exists(self, id: ID) -> bool:
        """Check if an entity exists by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            bool: True if exists, False otherwise
        """
        pass
