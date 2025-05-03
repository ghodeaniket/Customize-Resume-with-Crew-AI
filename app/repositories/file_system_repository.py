"""File system repository implementations for document and task access.

This module serves as a compatibility layer after refactoring.
The original large repository has been split into smaller, focused repositories.
"""
from .filesystem import FileSystemDocumentRepository, FileSystemTaskRepository

__all__ = [
    "FileSystemDocumentRepository",
    "FileSystemTaskRepository",
]
