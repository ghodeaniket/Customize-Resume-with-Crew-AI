"""Common test fixtures for all test modules."""
import os
import sys
import tempfile
import shutil
import uuid
from pathlib import Path

import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def test_uploads_dir():
    """Create a temporary directory for uploads during tests."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after the test
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_pdf_path():
    """Get path to test PDF file.
    
    This fixture assumes there's a test.pdf file in the test_data directory.
    If not, it will create an empty file for testing.
    """
    test_data_dir = Path(__file__).parent.parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    pdf_path = test_data_dir / "test.pdf"
    
    # Create an empty file if it doesn't exist
    if not pdf_path.exists():
        pdf_path.touch()
    
    return pdf_path


@pytest.fixture
def test_docx_path():
    """Get path to test DOCX file.
    
    This fixture assumes there's a test.docx file in the test_data directory.
    If not, it will create an empty file for testing.
    """
    test_data_dir = Path(__file__).parent.parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    docx_path = test_data_dir / "test.docx"
    
    # Create an empty file if it doesn't exist
    if not docx_path.exists():
        docx_path.touch()
    
    return docx_path


@pytest.fixture
def test_task_id():
    """Generate a random task ID for testing."""
    return str(uuid.uuid4())
