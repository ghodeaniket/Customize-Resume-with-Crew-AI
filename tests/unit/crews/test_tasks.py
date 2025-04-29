"""Unit tests for CrewAI tasks."""
import pytest
from unittest.mock import patch, MagicMock

from app.crews.tasks import create_job_analysis_task, create_resume_optimization_task


@pytest.fixture
def mock_agent():
    """Mock agent for testing."""
    return MagicMock()


def test_create_job_analysis_task(mock_agent):
    """Test creating a job analysis task."""
    with patch("app.crews.tasks.analyze_job.Task") as mock_task:
        # Setup mock
        mock_task_instance = MagicMock()
        mock_task.return_value = mock_task_instance
        
        # Sample job description
        job_description = "Software Developer position with Python and FastAPI experience"
        
        # Call the function
        task = create_job_analysis_task(agent=mock_agent, job_description=job_description)
        
        # Verify task was created with correct parameters
        mock_task.assert_called_once()
        
        # Get the call arguments
        call_args = mock_task.call_args[1]
        
        # Check key parameters
        assert job_description in call_args["description"]
        assert "analysis" in call_args["expected_output"]
        assert call_args["agent"] == mock_agent
        
        # Verify the returned task
        assert task == mock_task_instance


def test_create_resume_optimization_task(mock_agent):
    """Test creating a resume optimization task."""
    with patch("app.crews.tasks.optimize_resume.Task") as mock_task:
        # Setup mock
        mock_task_instance = MagicMock()
        mock_task.return_value = mock_task_instance
        
        # Sample data
        resume_text = "Python developer with 5 years of experience"
        job_analysis = "Looking for Python developer with FastAPI experience"
        customize_level = "comprehensive"
        
        # Call the function
        task = create_resume_optimization_task(
            agent=mock_agent, 
            resume_text=resume_text, 
            job_analysis_result=job_analysis,
            customize_level=customize_level
        )
        
        # Verify task was created with correct parameters
        mock_task.assert_called_once()
        
        # Get the call arguments
        call_args = mock_task.call_args[1]
        
        # Check key parameters
        assert resume_text in call_args["description"]
        assert job_analysis in call_args["description"]
        assert customize_level in call_args["description"]
        assert "optimized resume" in call_args["expected_output"]
        assert call_args["agent"] == mock_agent
        assert job_analysis in call_args["context"]
        
        # Verify the returned task
        assert task == mock_task_instance
