"""Repository implementations for data access."""
from app.repositories.base import BaseRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.file_system_repository import FileSystemDocumentRepository, FileSystemTaskRepository

__all__ = [
    "BaseRepository",
    "DocumentRepository",
    "TaskRepository",
    "FileSystemDocumentRepository",
    "FileSystemTaskRepository",
]
