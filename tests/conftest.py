"""Test fixtures for the Resume Customizer application."""
import pytest
import asyncio
from pathlib import Path
import os

from fastapi.testclient import TestClient

from app.main import app
from app.infrastructure.document_processor import DocumentProcessor
from app.services.resume_service import ResumeService


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def document_processor():
    """Create a document processor instance for testing."""
    return DocumentProcessor(cache_enabled=False)


@pytest.fixture
def resume_service():
    """Create a resume service instance for testing."""
    return ResumeService()


@pytest.fixture
def temp_uploads_dir(tmp_path):
    """Create a temporary uploads directory for testing."""
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    return uploads_dir


# Add mock data fixtures for testing in Phase 1
