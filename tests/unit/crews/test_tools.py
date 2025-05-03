"""Unit tests for CrewAI tools."""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.crews.tools.base import BaseResumeTool
from app.crews.tools.base.base_tool import ToolRegistry
from app.crews.tools.resume_tools import ResumeTools, create_resume_tools


class TestBaseResumeTool:
    """Test the base tool functionality."""
    
    def test_init(self):
        """Test tool initialization."""
        tool = BaseResumeTool(
            name="Test Tool",
            description="Test description",
            cache_enabled=True
        )
        
        assert tool.name == "Test Tool"
        assert tool.description == "Test description"
        assert tool.cache_enabled is True
        assert tool._cache == {}
    
    def test_cache_key(self):
        """Test cache key generation."""
        tool = BaseResumeTool("Test", "Test")
        
        key = tool._cache_key("arg1", "arg2", kwarg1="val1")
        assert key == "arg1|arg2|kwarg1=val1"
    
    def test_with_cache_decorator(self):
        """Test caching decorator."""
        tool = BaseResumeTool("Test", "Test", cache_enabled=True)
        
        call_count = 0
        
        @tool.with_cache
        def test_func(arg):
            nonlocal call_count
            call_count += 1
            return f"result_{arg}"
        
        # First call
        result1 = test_func("test")
        assert result1 == "result_test"
        assert call_count == 1
        
        # Second call (cached)
        result2 = test_func("test")
        assert result2 == "result_test"
        assert call_count == 1  # Should not increase
        
        # Different argument
        result3 = test_func("different")
        assert result3 == "result_different"
        assert call_count == 2
    
    def test_with_error_handling_decorator(self):
        """Test error handling decorator."""
        tool = BaseResumeTool("Test", "Test")
        
        @tool.with_error_handling
        def test_func():
            raise ValueError("Test error")
        
        result = test_func()
        assert "error" in result
        assert "Test error" in result["error"]


class TestToolRegistry:
    """Test the tool registry."""
    
    def test_singleton(self):
        """Test singleton pattern."""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()
        
        assert registry1 is registry2
    
    def test_register_and_get(self):
        """Test registering and getting tools."""
        registry = ToolRegistry()
        registry.clear()
        
        tool = Mock()
        registry.register("test_tool", tool)
        
        retrieved_tool = registry.get("test_tool")
        assert retrieved_tool == tool
        
        # Test non-existent tool
        assert registry.get("non_existent") is None
    
    def test_list_tools(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        registry.clear()
        
        tool1 = Mock()
        tool2 = Mock()
        
        registry.register("tool1", tool1)
        registry.register("tool2", tool2)
        
        tools = registry.list_tools()
        assert len(tools) == 2
        assert tools["tool1"] == tool1
        assert tools["tool2"] == tool2


class TestResumeTools:
    """Test the resume tools collection."""
    
    @pytest.fixture
    def mock_resume_service(self):
        """Mock resume service for testing."""
        service = Mock()
        service.get_resume_data = AsyncMock(return_value={
            "status": "completed",
            "text": "Test resume content",
            "metadata": {"filename": "test.pdf"}
        })
        return service
    
    def test_init(self, mock_resume_service):
        """Test tools initialization."""
        tools = ResumeTools(resume_service=mock_resume_service)
        
        assert tools.resume_service == mock_resume_service
        assert tools.name == "ResumeTools"
    
    def test_create_resume_processor_tool(self, mock_resume_service):
        """Test creating resume processor tool."""
        tools = ResumeTools(resume_service=mock_resume_service)
        
        processor_tool = tools.create_resume_processor_tool()
        assert processor_tool is not None
        
        # Test the created tool
        result = processor_tool("test_task_id")
        assert result["text"] == "Test resume content"
        assert result["metadata"]["filename"] == "test.pdf"
    
    def test_create_job_matcher_tool(self):
        """Test creating job matcher tool."""
        tools = ResumeTools()
        
        matcher_tool = tools.create_job_matcher_tool()
        assert matcher_tool is not None
        
        # Test the created tool
        result = matcher_tool("Resume with Python", "Job requiring Python")
        assert "match_score" in result
        assert "missing_skills" in result
        assert "matching_skills" in result
        assert "recommendations" in result
    
    def test_create_keyword_extractor_tool(self):
        """Test creating keyword extractor tool."""
        tools = ResumeTools()
        
        extractor_tool = tools.create_keyword_extractor_tool()
        assert extractor_tool is not None
        
        # Test the created tool
        result = extractor_tool("Python programming with Docker and Kubernetes")
        assert "keywords" in result
        assert "total_words" in result
        assert "unique_words" in result
    
    def test_create_ats_optimizer_tool(self):
        """Test creating ATS optimizer tool."""
        tools = ResumeTools()
        
        optimizer_tool = tools.create_ats_optimizer_tool()
        assert optimizer_tool is not None
        
        # Test the created tool
        result = optimizer_tool(
            "Resume with Python experience",
            ["Python", "Docker", "AWS"]
        )
        assert "ats_score" in result
        assert "keyword_matches" in result
        assert "missing_keywords" in result
        assert "suggestions" in result


def test_create_resume_tools(monkeypatch):
    """Test the main function to create all tools."""
    mock_resume_service = Mock()
    
    # Clear registry before test
    ToolRegistry.clear()
    
    tools = create_resume_tools(resume_service=mock_resume_service)
    
    assert len(tools) == 4
    assert "resume_processor" in tools
    assert "job_matcher" in tools
    assert "keyword_extractor" in tools
    assert "ats_optimizer" in tools
    
    # Check if tools are registered
    registry = ToolRegistry()
    registered_tools = registry.list_tools()
    assert len(registered_tools) == 4
