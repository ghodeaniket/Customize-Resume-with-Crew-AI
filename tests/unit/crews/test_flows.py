"""Unit tests for CrewAI flows."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.crews.flows.base import BaseResumeFlow
from app.crews.flows.resume_flow import ResumeCustomizationFlow
from app.models.domain.states import (
    ResumeCustomizationState,
    TaskStatus,
    JobAnalysisStatus,
    ResumeOptimizationStatus
)


class TestBaseResumeFlow:
    """Test the base flow functionality."""
    
    def test_init(self):
        """Test flow initialization."""
        task_id = "test_task_123"
        initial_state = Mock()
        services = {"service1": Mock()}
        
        flow = BaseResumeFlow(
            task_id=task_id,
            initial_state=initial_state,
            services=services
        )
        
        assert flow.task_id == task_id
        assert flow.services == services
        assert flow.start_time is None
        assert flow.end_time is None
    
    def test_setup_llm_environment(self, monkeypatch):
        """Test LLM environment setup."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.LLM_API_KEY = "test-llm-key"
        mock_settings.OPENAI_API_KEY = "test-openai-key"
        mock_settings.AGENT_LLM = "gpt-4"
        mock_settings.AGENT_VERBOSE = True
        mock_settings.CREW_VERBOSE = False
        
        monkeypatch.setattr('app.crews.flows.base.base_flow.settings', mock_settings)
        
        # Create flow
        flow = BaseResumeFlow("test", Mock())
        
        # Test environment setup
        flow._setup_llm_environment()
        
        # Check environment variables were set
        import os
        assert os.environ.get("LLM_API_KEY") == "test-llm-key"
        assert os.environ.get("OPENAI_API_KEY") == "test-openai-key"
        assert os.environ.get("AGENT_LLM") == "gpt-4"
        assert os.environ.get("AGENT_VERBOSE") == "true"
        assert os.environ.get("CREW_VERBOSE") == "false"
    
    def test_get_service(self):
        """Test service retrieval."""
        service1 = Mock()
        services = {"service1": service1}
        
        flow = BaseResumeFlow("test", Mock(), services=services)
        
        # Test existing service
        retrieved_service = flow.get_service("service1")
        assert retrieved_service == service1
        
        # Test non-existent service
        with pytest.raises(ValueError):
            flow.get_service("non_existent")
    
    def test_timing_functions(self):
        """Test flow timing functions."""
        flow = BaseResumeFlow("test", Mock())
        
        # Start flow
        flow.start_flow()
        assert flow.start_time is not None
        
        # End flow
        flow.end_flow()
        assert flow.end_time is not None
        
        # Check execution time
        execution_time = flow.get_execution_time()
        assert execution_time >= 0
    
    def test_handle_error(self):
        """Test error handling."""
        # Create mock state with error fields
        mock_state = Mock()
        mock_state.status = "processing"
        mock_state.error_message = None
        
        flow = BaseResumeFlow("test", mock_state)
        flow.state = mock_state  # Ensure state is set properly
        
        # Handle error
        error = ValueError("Test error")
        flow.handle_error(error, context="test_context")
        
        # Check state was updated
        assert mock_state.status == "failed"
        assert mock_state.error_message == "Test error"


class TestResumeCustomizationFlow:
    """Test the resume customization flow."""
    
    @pytest.fixture
    def mock_services(self):
        """Mock services for testing."""
        return {
            "resume_service": Mock(),
            "storage_service": Mock(),
            "task_service": Mock()
        }
    
    @pytest.fixture
    def mock_settings(self, monkeypatch):
        """Mock settings for testing."""
        mock_settings = Mock()
        mock_settings.LLM_API_KEY = "test-key"
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.AGENT_LLM = "gpt-4"
        mock_settings.AGENT_VERBOSE = True
        mock_settings.CREW_VERBOSE = False
        
        monkeypatch.setattr('app.crews.flows.base.base_flow.settings', mock_settings)
        monkeypatch.setattr('app.crews.flows.resume_flow.settings', mock_settings)
        
        return mock_settings
    
    def test_init(self, mock_services):
        """Test flow initialization."""
        task_id = "test_task_123"
        
        flow = ResumeCustomizationFlow(
            task_id=task_id,
            **mock_services
        )
        
        assert flow.task_id == task_id
        assert flow.services["resume_service"] == mock_services["resume_service"]
        assert flow.analyzer_agent is None
        assert flow.optimizer_agent is None
        assert flow.tools is None
    
    def test_initialize_tools(self, mock_services):
        """Test tool initialization."""
        flow = ResumeCustomizationFlow("test", **mock_services)
        
        with patch('app.crews.flows.resume_flow.create_resume_tools') as mock_create_tools:
            mock_tools = {"tool1": Mock(), "tool2": Mock()}
            mock_create_tools.return_value = mock_tools
            
            tools = flow._initialize_tools()
            
            assert tools == mock_tools
            assert flow.tools == mock_tools
            mock_create_tools.assert_called_once_with(
                resume_service=mock_services["resume_service"]
            )
    
    def test_create_analyzer_agent(self, mock_services):
        """Test analyzer agent creation."""
        flow = ResumeCustomizationFlow("test", **mock_services)
        
        # Mock tools
        mock_tools = {
            "keyword_extractor": Mock(),
            "job_matcher": Mock(),
            "resume_processor": Mock(),
            "ats_optimizer": Mock()
        }
        flow.tools = mock_tools
        
        with patch('app.crews.flows.resume_flow.ResumeAnalyzerAgent') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer_class.return_value = mock_analyzer
            
            agent = flow._create_analyzer_agent()
            
            assert agent == mock_analyzer
            assert flow.analyzer_agent == mock_analyzer
            
            # Check correct tools were passed
            call_args = mock_analyzer_class.call_args
            tools_arg = call_args[1]["tools"]
            assert len(tools_arg) == 2
            assert mock_tools["keyword_extractor"] in tools_arg
            assert mock_tools["job_matcher"] in tools_arg
    
    def test_set_job_description(self, mock_services):
        """Test setting job description."""
        flow = ResumeCustomizationFlow("test", **mock_services)
        
        job_text = "Test job description"
        filename = "job.txt"
        
        flow.set_job_description(job_text, filename)
        
        assert flow.state.job_analysis.job_description is not None
        assert flow.state.job_analysis.job_description.content == job_text
        assert flow.state.job_analysis.job_description.filename == filename
    
    def test_set_resume(self, mock_services):
        """Test setting resume."""
        flow = ResumeCustomizationFlow("test", **mock_services)
        
        resume_text = "Test resume content"
        filename = "resume.pdf"
        
        flow.set_resume(resume_text, filename)
        
        assert flow.state.resume_optimization.resume is not None
        assert flow.state.resume_optimization.resume.content == resume_text
        assert flow.state.resume_optimization.resume.filename == filename
    
    def test_set_customization_level(self, mock_services):
        """Test setting customization level."""
        flow = ResumeCustomizationFlow("test", **mock_services)
        
        flow.set_customization_level("comprehensive")
        
        assert flow.state.resume_optimization.customization_level == "comprehensive"
    
    def test_get_result(self, mock_services):
        """Test getting flow result."""
        flow = ResumeCustomizationFlow("test", **mock_services)
        
        # Set up state
        flow.state.status = TaskStatus.COMPLETED
        flow.state.progress = 100.0
        flow.state.resume_optimization.optimized_resume = "Optimized resume content"
        flow.state.resume_optimization.customization_level = "standard"
        flow.state.processing_time_ms = 5000.0
        flow.state.started_at = datetime.now()
        flow.state.completed_at = datetime.now()
        
        result = flow.get_result()
        
        assert result["task_id"] == "test"
        assert result["status"] == "completed"
        assert result["progress"] == 100.0
        assert result["optimized_resume"] == "Optimized resume content"
        assert result["metadata"]["customize_level"] == "standard"
        assert result["metadata"]["processing_time_ms"] == 5000.0
