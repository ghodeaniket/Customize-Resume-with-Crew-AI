"""Base service interface for resume services."""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, Generic, TypeVar, Protocol

# Define type variables for generic services
T = TypeVar('T')
ID = TypeVar('ID')

class BaseService(Generic[T, ID], ABC):
    """Base interface for service operations.
    
    This abstract base class defines the common interface for service operations.
    Services provide business logic for specific domains and coordinate between
    repositories, external systems, and domain models.
    
    Type Parameters:
        T: Type of the entity or data managed by the service
        ID: Type of the identifier for the entity
    """
    
    @abstractmethod
    async def get_by_id(self, id: ID) -> Optional[T]:
        """Get an entity by its identifier.
        
        Args:
            id: Entity identifier
            
        Returns:
            Optional[T]: Entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def exists(self, id: ID) -> bool:
        """Check if an entity exists.
        
        Args:
            id: Entity identifier
            
        Returns:
            bool: True if the entity exists, False otherwise
        """
        pass
