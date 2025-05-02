"""Unit tests for resume customization flow."""
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.models.domain.states import (
    ResumeCustomizationState, 
    JobAnalysisStatus, 
    ResumeOptimizationStatus,
    TaskStatus,
    DocumentInfo,
    CustomizationLevel
)
from app.crews.flows.resume_customization_flow import ResumeCustomizationFlow


@pytest.fixture
def test_task_id():
    """Generate a random task ID for testing."""
    return str(uuid.uuid4())


@pytest.fixture
def test_resume_text():
    """Sample resume text for testing."""
    return """
    John Doe
    Software Engineer

    EXPERIENCE
    Senior Developer, ABC Company (2020-Present)
    - Developed web applications using Python and FastAPI
    - Led team of 5 developers on project X

    SKILLS
    Python, FastAPI, SQL, Git, AWS
    """


@pytest.fixture
def test_job_description():
    """Sample job description for testing."""
    return """
    Senior Software Engineer

    Requirements:
    - 5+ years of experience in Python development
    - Experience with FastAPI, Flask, or Django
    - Knowledge of SQL and database design
    - Experience with Git and CI/CD pipelines
    """


@pytest.mark.asyncio
async def test_resume_customization_state_validation():
    """Test validation for the ResumeCustomizationState model."""
    # Valid state creation
    state = ResumeCustomizationState(task_id="test-123")
    assert state.task_id == "test-123"
    assert state.status == TaskStatus.CREATED
    assert state.progress == 0.0
    
    # Test progress validation
    with pytest.raises(ValidationError):
        ResumeCustomizationState(task_id="test-123", progress=101.0)
    
    with pytest.raises(ValidationError):
        ResumeCustomizationState(task_id="test-123", progress=-1.0)
    
    # Test rounding of progress value
    state = ResumeCustomizationState(task_id="test-123", progress=10.123)
    assert state.progress == 10.1


@pytest.mark.asyncio
async def test_resume_customization_flow_initialization(test_task_id):
    """Test initialization of the ResumeCustomizationFlow."""
    # Act
    flow = ResumeCustomizationFlow(task_id=test_task_id)
    
    # Assert
    assert flow.state.task_id == test_task_id
    assert flow.state.status == TaskStatus.CREATED
    assert flow.state.progress == 0.0
    assert flow.state.job_analysis.status == JobAnalysisStatus.PENDING
    assert flow.state.resume_optimization.status == ResumeOptimizationStatus.PENDING


@pytest.mark.asyncio
async def test_set_job_description(test_task_id, test_job_description):
    """Test setting job description in the flow."""
    # Arrange
    flow = ResumeCustomizationFlow(task_id=test_task_id)
    
    # Act
    flow.set_job_description(test_job_description, "job.txt")
    
    # Assert
    assert flow.state.job_analysis.job_description.content == test_job_description
    assert flow.state.job_analysis.job_description.filename == "job.txt"


@pytest.mark.asyncio
async def test_set_resume(test_task_id, test_resume_text):
    """Test setting resume in the flow."""
    # Arrange
    flow = ResumeCustomizationFlow(task_id=test_task_id)
    
    # Act
    flow.set_resume(test_resume_text, "resume.txt")
    
    # Assert
    assert flow.state.resume_optimization.resume.content == test_resume_text
    assert flow.state.resume_optimization.resume.filename == "resume.txt"


@pytest.mark.asyncio
async def test_set_customization_level(test_task_id):
    """Test setting customization level in the flow."""
    # Arrange
    flow = ResumeCustomizationFlow(task_id=test_task_id)
    
    # Act
    flow.set_customization_level(CustomizationLevel.COMPREHENSIVE.value)
    
    # Assert
    assert flow.state.resume_optimization.customization_level == CustomizationLevel.COMPREHENSIVE
    
    # Test invalid customization level
    with pytest.raises(ValueError):
        flow.set_customization_level("invalid_level")


@pytest.mark.asyncio
@patch("app.crews.flows.resume_customization_flow.Agent")
async def test_initialize_flow(mock_agent, test_task_id):
    """Test the initialize_flow method."""
    # Arrange
    flow = ResumeCustomizationFlow(task_id=test_task_id)
    
    # Act
    result = flow.initialize_flow()
    
    # Assert
    assert result == "Flow initialized successfully"
    assert flow.state.status == TaskStatus.PROCESSING
    assert flow.state.progress == 5.0
    assert flow.state.started_at is not None


@pytest.mark.asyncio
async def test_check_resources_missing_job(test_task_id):
    """Test check_resources with missing job description."""
    # Arrange
    flow = ResumeCustomizationFlow(task_id=test_task_id)
    
    # Act
    result = flow.check_resources("previous_result")
    
    # Assert
    assert result == "missing_job_description"


@pytest.mark.asyncio
async def test_check_resources_analyze_job(test_task_id, test_job_description):
    """Test check_resources with job description ready for analysis."""
    # Arrange
    flow = ResumeCustomizationFlow(task_id=test_task_id)
    flow.set_job_description(test_job_description)
    
    # Act
    result = flow.check_resources("previous_result")
    
    # Assert
    assert result == "analyze_job"


@pytest.mark.asyncio
async def test_check_resources_missing_resume(test_task_id, test_job_description):
    """Test check_resources with job analyzed but missing resume."""
    # Arrange
    flow = ResumeCustomizationFlow(task_id=test_task_id)
    flow.set_job_description(test_job_description)
    
    # Set job analysis as completed
    flow.state.job_analysis.status = JobAnalysisStatus.COMPLETED
    flow.state.job_analysis.analysis_result = "Analysis result"
    
    # Act
    result = flow.check_resources("previous_result")
    
    # Assert
    assert result == "missing_resume"


@pytest.mark.asyncio
async def test_check_resources_optimize_resume(test_task_id, test_job_description, test_resume_text):
    """Test check_resources with job analyzed and resume ready for optimization."""
    # Arrange
    flow = ResumeCustomizationFlow(task_id=test_task_id)
    flow.set_job_description(test_job_description)
    flow.set_resume(test_resume_text)
    
    # Set job analysis as completed
    flow.state.job_analysis.status = JobAnalysisStatus.COMPLETED
    flow.state.job_analysis.analysis_result = "Analysis result"
    
    # Act
    result = flow.check_resources("previous_result")
    
    # Assert
    assert result == "optimize_resume"


@pytest.mark.asyncio
async def test_check_resources_complete(test_task_id, test_job_description, test_resume_text):
    """Test check_resources with all steps completed."""
    # Arrange
    flow = ResumeCustomizationFlow(task_id=test_task_id)
    flow.set_job_description(test_job_description)
    flow.set_resume(test_resume_text)
    
    # Set job analysis as completed
    flow.state.job_analysis.status = JobAnalysisStatus.COMPLETED
    flow.state.job_analysis.analysis_result = "Analysis result"
    
    # Set resume optimization as completed
    flow.state.resume_optimization.status = ResumeOptimizationStatus.COMPLETED
    flow.state.resume_optimization.optimized_resume = "Optimized resume"
    
    # Act
    result = flow.check_resources("previous_result")
    
    # Assert
    assert result == "complete"


@pytest.mark.asyncio
@patch("app.crews.flows.resume_customization_flow.Agent")
@patch("app.crews.agents.create_resume_analyzer_agent")
@patch("app.crews.tasks.analyze_job.create_job_analysis_task")
async def test_analyze_job_description(
    mock_create_task, mock_create_agent, mock_agent, 
    test_task_id, test_job_description
):
    """Test analyze_job_description method."""
    # Arrange
    flow = ResumeCustomizationFlow(task_id=test_task_id)
    flow.set_job_description(test_job_description)
    
    # Mock agent and execution
    mock_agent_instance = MagicMock()
    mock_agent_instance.execute_task.return_value = "Analysis result"
    mock_create_agent.return_value = mock_agent_instance
    
    mock_task = MagicMock()
    mock_create_task.return_value = mock_task
    
    # Act
    result = flow.analyze_job_description()
    
    # Assert
    assert result == "Analysis result"
    assert flow.state.job_analysis.status == JobAnalysisStatus.COMPLETED
    assert flow.state.job_analysis.analysis_result == "Analysis result"
    assert flow.state.progress > 20.0  # Progress should increase
    
    # Verify agent execution
    mock_agent_instance.execute_task.assert_called_once_with(mock_task)


@pytest.mark.asyncio
@patch("app.crews.flows.resume_customization_flow.Agent")
@patch("app.crews.agents.create_resume_optimizer_agent")
@patch("app.crews.tasks.optimize_resume.create_resume_optimization_task")
async def test_optimize_resume(
    mock_create_task, mock_create_agent, mock_agent, 
    test_task_id, test_job_description, test_resume_text
):
    """Test optimize_resume method."""
    # Arrange
    flow = ResumeCustomizationFlow(task_id=test_task_id)
    flow.set_job_description(test_job_description)
    flow.set_resume(test_resume_text)
    
    # Set job analysis as completed
    flow.state.job_analysis.status = JobAnalysisStatus.COMPLETED
    flow.state.job_analysis.analysis_result = "Analysis result"
    
    # Mock agent and execution
    mock_agent_instance = MagicMock()
    mock_agent_instance.execute_task.return_value = "Optimized resume"
    mock_create_agent.return_value = mock_agent_instance
    
    mock_task = MagicMock()
    mock_create_task.return_value = mock_task
    
    # Act
    result = flow.optimize_resume()
    
    # Assert
    assert result == "Optimized resume"
    assert flow.state.resume_optimization.status == ResumeOptimizationStatus.COMPLETED
    assert flow.state.resume_optimization.optimized_resume == "Optimized resume"
    assert flow.state.status == TaskStatus.COMPLETED
    assert flow.state.progress == 100.0
    assert flow.state.completed_at is not None
    
    # Verify agent execution
    mock_agent_instance.execute_task.assert_called_once_with(mock_task)


@pytest.mark.asyncio
async def test_finalize_flow(test_task_id):
    """Test finalize_flow method."""
    # Arrange
    flow = ResumeCustomizationFlow(task_id=test_task_id)
    flow.state.resume_optimization.optimized_resume = "Optimized resume"
    flow.state.resume_optimization.customization_level = CustomizationLevel.STANDARD
    
    # Act
    result = flow.finalize_flow()
    
    # Assert
    assert result["task_id"] == test_task_id
    assert result["status"] == "completed"
    assert result["optimized_resume"] == "Optimized resume"
    assert result["metadata"]["customize_level"] == "standard"
    assert flow.state.status == TaskStatus.COMPLETED
    assert flow.state.progress == 100.0
    assert flow.state.completed_at is not None


@pytest.mark.asyncio
@patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}, clear=True)
async def test_setup_llm_environment(test_task_id):
    """Test _setup_llm_environment method."""
    # Arrange
    flow = ResumeCustomizationFlow(task_id=test_task_id)
    
    # Act
    flow._setup_llm_environment()
    
    # Assert - Just ensure it doesn't raise an exception
    assert True
