"""Integration tests for the Resume API endpoints."""
import pytest
from fastapi.testclient import TestClient


def test_health_check(test_client):
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_resume_endpoint(test_client):
    """Test the resume upload endpoint."""
    # This will be implemented in Phase 1
    pass
