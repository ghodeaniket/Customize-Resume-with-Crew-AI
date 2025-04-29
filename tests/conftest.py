"""Test fixtures for the Resume Customizer application."""
import pytest
import asyncio
import uuid
import os
import io
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from fastapi import UploadFile, File, BackgroundTasks

from app.main import app
from app.infrastructure.document_processor import DocumentProcessor
from app.services.document_storage_service import DocumentStorageService
from app.services.resume_service import ResumeService
from app.core.config import settings


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
def temp_uploads_dir(tmp_path):
    """Create a temporary uploads directory for testing."""
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    
    # Patch the config to use our temporary directory
    original_uploads_dir = settings.UPLOADS_DIR
    settings.UPLOADS_DIR = str(uploads_dir)
    
    yield uploads_dir
    
    # Restore original setting
    settings.UPLOADS_DIR = original_uploads_dir


@pytest.fixture
def storage_service(temp_uploads_dir):
    """Create a document storage service instance for testing."""
    return DocumentStorageService(base_path=str(temp_uploads_dir))


@pytest.fixture
def resume_service(document_processor, storage_service):
    """Create a resume service instance for testing."""
    return ResumeService(document_processor=document_processor, storage_service=storage_service)


@pytest.fixture
def background_tasks():
    """Create a background tasks instance for testing."""
    return BackgroundTasks()


@pytest.fixture
def mock_task_id():
    """Create a mock task ID for testing."""
    return str(uuid.uuid4())


@pytest.fixture
def test_pdf_path():
    """Path to test PDF file."""
    return Path(__file__).parent / "data" / "test_resume.pdf"


@pytest.fixture
def test_docx_path():
    """Path to test DOCX file."""
    return Path(__file__).parent / "data" / "test_resume.docx"


@pytest.fixture
def test_txt_path():
    """Path to test TXT file."""
    return Path(__file__).parent / "data" / "test_resume.txt"


@pytest.fixture
def create_test_data_dir():
    """Create test data directory if it doesn't exist."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture
def sample_pdf_content(create_test_data_dir, test_pdf_path):
    """Sample PDF content for testing."""
    # Create a simple PDF if it doesn't exist yet
    if not test_pdf_path.exists():
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            c = canvas.Canvas(str(test_pdf_path), pagesize=letter)
            c.drawString(100, 750, "Test Resume")
            c.drawString(100, 730, "Software Engineer")
            c.drawString(100, 710, "Skills:")
            c.drawString(120, 690, "Python, FastAPI, CrewAI")
            c.drawString(100, 670, "Experience:")
            c.drawString(120, 650, "Software Engineer, ABC Corp, 2018-Present")
            c.drawString(120, 630, "- Developed backend services using Python")
            c.drawString(120, 610, "- Implemented AI-powered document processing")
            c.save()
        except ImportError:
            # If reportlab is not available, create a simple text file
            with open(test_pdf_path, "wb") as f:
                f.write(b"%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Resources<<>>/Contents 4 0 R/Parent 2 0 R>>\nendobj\n4 0 obj\n<</Length 51>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test Resume - Software Engineer) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000212 00000 n\ntrailer\n<</Size 5/Root 1 0 R>>\nstartxref\n312\n%%EOF")
    
    # Read the PDF content
    with open(test_pdf_path, "rb") as f:
        return f.read()


@pytest.fixture
def sample_docx_content(create_test_data_dir, test_docx_path):
    """Sample DOCX content for testing."""
    # Create a simple DOCX if it doesn't exist yet
    if not test_docx_path.exists():
        try:
            from docx import Document
            
            doc = Document()
            doc.add_heading("Test Resume", 0)
            doc.add_paragraph("Software Engineer")
            doc.add_heading("Skills", 1)
            doc.add_paragraph("Python, FastAPI, CrewAI")
            doc.add_heading("Experience", 1)
            doc.add_paragraph("Software Engineer, ABC Corp, 2018-Present")
            doc.add_paragraph("- Developed backend services using Python")
            doc.add_paragraph("- Implemented AI-powered document processing")
            doc.save(test_docx_path)
        except ImportError:
            # If python-docx is not available, create a simple binary file
            with open(test_docx_path, "wb") as f:
                f.write(b"PK\x03\x04\x14\x00\x00\x00\x00\x00\x00\x00!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00Test Resume\nSoftware Engineer\nSkills:\nPython, FastAPI, CrewAI\nExperience:\nSoftware Engineer, ABC Corp, 2018-Present\n- Developed backend services using Python\n- Implemented AI-powered document processing")
    
    # Read the DOCX content
    with open(test_docx_path, "rb") as f:
        return f.read()


@pytest.fixture
def sample_txt_content(create_test_data_dir, test_txt_path):
    """Sample TXT content for testing."""
    # Create a simple TXT if it doesn't exist yet
    if not test_txt_path.exists():
        with open(test_txt_path, "w") as f:
            f.write("Test Resume\nSoftware Engineer\n\nSkills:\nPython, FastAPI, CrewAI\n\nExperience:\nSoftware Engineer, ABC Corp, 2018-Present\n- Developed backend services using Python\n- Implemented AI-powered document processing")
    
    # Read the TXT content
    with open(test_txt_path, "rb") as f:
        return f.read()


@pytest.fixture
def mock_pdf_file(sample_pdf_content):
    """Create a mock PDF file for testing."""
    return UploadFile(
        filename="test_resume.pdf",
        file=io.BytesIO(sample_pdf_content)
    )


@pytest.fixture
def mock_docx_file(sample_docx_content):
    """Create a mock DOCX file for testing."""
    return UploadFile(
        filename="test_resume.docx",
        file=io.BytesIO(sample_docx_content)
    )


@pytest.fixture
def mock_txt_file(sample_txt_content):
    """Create a mock TXT file for testing."""
    return UploadFile(
        filename="test_resume.txt",
        file=io.BytesIO(sample_txt_content)
    )


@pytest.fixture
def mock_invalid_file():
    """Create a mock invalid file for testing."""
    return UploadFile(
        filename="invalid.xyz",
        file=io.BytesIO(b"This is not a valid document")
    )


@pytest.fixture
def mock_process_resume():
    """Mock the process_resume method of ResumeService."""
    async def _mock_process_resume(*args, **kwargs):
        return {
            "task_id": kwargs.get("task_id", str(uuid.uuid4())),
            "filename": kwargs.get("filename", "test_resume.pdf"),
            "text": "Test resume content extracted by mock",
            "text_path": "/tmp/extracted.txt",
            "original_path": "/tmp/original.pdf",
            "status": "completed"
        }
    
    with patch.object(
        ResumeService, 'process_resume', side_effect=_mock_process_resume
    ) as mock:
        yield mock
