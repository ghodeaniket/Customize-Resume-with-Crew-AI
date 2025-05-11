"""Dependency injection for customization repository."""
from fastapi import Depends

from app.repositories.filesystem.customization_repository import CustomizationRepository


def get_customization_repository() -> CustomizationRepository:
    """Get customization repository instance.
    
    Returns:
        CustomizationRepository: Customization repository instance
    """
    return CustomizationRepository()
