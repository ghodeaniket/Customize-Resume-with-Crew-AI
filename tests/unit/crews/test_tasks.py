"""Unit tests for CrewAI tasks."""
import pytest
from unittest.mock import Mock, patch

from app.crews.tasks.base import BaseResumeTask
from app.crews.tasks.base.base_task import TaskConfig
from app.crews.tasks.analysis_task import JobAnalysisTask
from app.crews.tasks.optimization_task import ResumeOptimizationTask


class TestBaseResumeTask:
    """Test the base task functionality."""
    
    def test_init(self):
        """Test task initialization."""
        config = TaskConfig(
            name="Test Task",
            description="Test description",
            expected_output="Test output"
        )
        
        task = BaseResumeTask(config)
        
        assert task.config == config
        assert task._task is None
    
    def test_create_task(self):
        """Test task creation."""
        config = TaskConfig(
            name="Test Task",
            description="Test description",
            expected_output="Test output"
        )
        
        with patch('app.crews.tasks.base.base_task.Task') as mock_task_class:
            mock_task_instance = Mock()
            mock_task_class.return_value = mock_task_instance
            
            task = BaseResumeTask(config)
            agent = Mock()
            
            crew_task = task.create_task(agent)
            
            mock_task_class.assert_called_once()
            assert crew_task == mock_task_instance
            assert task._task == mock_task_instance
    
    def test_reset_task(self):
        """Test task reset."""
        config = TaskConfig(
            name="Test Task",
            description="Test description",
            expected_output="Test output"
        )
        
        task = BaseResumeTask(config)
        task._task = Mock()
        
        task.reset_task()
        
        assert task._task is None


class TestJobAnalysisTask:
    """Test the job analysis task."""
    
    def test_init(self):
        """Test job analysis task initialization."""
        job_description = "Test job description"
        task = JobAnalysisTask(job_description)
        
        assert task.config.name == "Job Analysis"
        assert job_description in task.config.description
        assert task.job_description == job_description
    
    def test_validate_result_str(self):
        """Test result validation for string results."""
        task = JobAnalysisTask("Test job description")
        
        # Valid result
        valid_result = "This result includes skills and experience requirements"
        assert task.validate_result(valid_result) is True
        
        # Invalid result
        invalid_result = "This result has no relevant content"
        assert task.validate_result(invalid_result) is False
        
        # None result
        assert task.validate_result(None) is False
    
    def test_validate_result_dict(self):
        """Test result validation for dictionary results."""
        task = JobAnalysisTask("Test job description")
        
        # Valid result
        valid_result = {
            "skills": ["Python", "Docker"],
            "experience": "5 years"
        }
        assert task.validate_result(valid_result) is True
        
        # Invalid result
        invalid_result = {
            "unrelated": "content"
        }
        assert task.validate_result(invalid_result) is False
    
    def test_factory_function(self):
        """Test the factory function for backward compatibility."""
        from app.crews.tasks.analysis_task import create_job_analysis_task
        
        with patch('app.crews.tasks.base.base_task.Task') as mock_task_class:
            mock_task_instance = Mock()
            mock_task_class.return_value = mock_task_instance
            
            agent = Mock()
            job_description = "Test job description"
            
            task = create_job_analysis_task(agent, job_description)
            
            assert task == mock_task_instance


class TestResumeOptimizationTask:
    """Test the resume optimization task."""
    
    def test_init(self):
        """Test resume optimization task initialization."""
        resume_text = "Test resume"
        job_analysis_result = "Test analysis"
        customize_level = "standard"
        
        task = ResumeOptimizationTask(
            resume_text=resume_text,
            job_analysis_result=job_analysis_result,
            customize_level=customize_level
        )
        
        assert task.config.name == "Resume Optimization"
        assert resume_text in task.config.description
        assert job_analysis_result in task.config.description
        assert task.resume_text == resume_text
        assert task.job_analysis_result == job_analysis_result
        assert task.customize_level == customize_level
    
    def test_get_customization_guidance(self):
        """Test getting customization guidance."""
        task = ResumeOptimizationTask(
            resume_text="Test",
            job_analysis_result="Test",
            customize_level="minimal"
        )
        
        minimal_guidance = task._get_customization_guidance("minimal")
        assert "90%" in minimal_guidance
        
        standard_guidance = task._get_customization_guidance("standard")
        assert "75%" in standard_guidance
        
        comprehensive_guidance = task._get_customization_guidance("comprehensive")
        assert "90% of the job requirements" in comprehensive_guidance
    
    def test_validate_result(self):
        """Test result validation."""
        task = ResumeOptimizationTask(
            resume_text="Test",
            job_analysis_result="Test",
            customize_level="standard"
        )
        
        # Valid result
        valid_result = "This is a resume with experience, skills, and education sections."
        assert task.validate_result(valid_result) is True
        
        # Too short result
        short_result = "Too short"
        assert task.validate_result(short_result) is False
        
        # None result
        assert task.validate_result(None) is False
