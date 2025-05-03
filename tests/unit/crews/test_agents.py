"""Unit tests for CrewAI agents."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.crews.agents.base import BaseResumAgent
from app.crews.agents.base.base_agent import AgentConfig
from app.crews.agents.analyzer_agent import ResumeAnalyzerAgent
from app.crews.agents.optimizer_agent import ResumeOptimizerAgent


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('app.crews.agents.base.base_agent.settings') as mock_settings:
        mock_settings.AGENT_LLM = "gpt-4"
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.LLM_API_KEY = "test-key"
        mock_settings.AGENT_VERBOSE = True
        yield mock_settings


@pytest.fixture
def mock_llm():
    """Mock LLM instance."""
    with patch('app.crews.agents.base.base_agent.LLM') as mock_llm_class:
        mock_instance = Mock()
        mock_llm_class.return_value = mock_instance
        yield mock_llm_class


class TestBaseResumAgent:
    """Test the base agent functionality."""
    
    def test_init(self, mock_settings):
        """Test agent initialization."""
        config = AgentConfig(
            role="Test Agent",
            goal="Test goal",
            backstory="Test backstory"
        )
        
        agent = BaseResumAgent(config)
        
        assert agent.config == config
        assert agent.tools == []
        assert agent._llm is None
        assert agent._agent is None
    
    def test_setup_llm(self, mock_settings, mock_llm):
        """Test LLM setup."""
        config = AgentConfig(
            role="Test Agent",
            goal="Test goal",
            backstory="Test backstory"
        )
        
        agent = BaseResumAgent(config)
        llm = agent._setup_llm()
        
        mock_llm.assert_called_once_with(api_key="test-key", model="gpt-4")
        assert llm == mock_llm.return_value
    
    def test_create_agent(self, mock_settings, mock_llm):
        """Test agent creation."""
        config = AgentConfig(
            role="Test Agent",
            goal="Test goal",
            backstory="Test backstory"
        )
        
        with patch('app.crews.agents.base.base_agent.Agent') as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_class.return_value = mock_agent_instance
            
            agent = BaseResumAgent(config)
            crew_agent = agent.create_agent()
            
            mock_agent_class.assert_called_once()
            assert crew_agent == mock_agent_instance
            assert agent._agent == mock_agent_instance
    
    def test_add_tool(self):
        """Test adding tools to agent."""
        config = AgentConfig(
            role="Test Agent",
            goal="Test goal",
            backstory="Test backstory"
        )
        
        agent = BaseResumAgent(config)
        tool = Mock(name="test_tool")
        
        agent.add_tool(tool)
        
        assert tool in agent.tools
    
    def test_remove_tool(self):
        """Test removing tools from agent."""
        config = AgentConfig(
            role="Test Agent",
            goal="Test goal",
            backstory="Test backstory"
        )
        
        agent = BaseResumAgent(config)
        tool = Mock(name="test_tool")
        tool.name = "test_tool"
        
        agent.add_tool(tool)
        agent.remove_tool("test_tool")
        
        assert tool not in agent.tools


class TestResumeAnalyzerAgent:
    """Test the resume analyzer agent."""
    
    def test_init(self, mock_settings):
        """Test analyzer agent initialization."""
        analyzer = ResumeAnalyzerAgent()
        
        assert analyzer.config.role == "Resume Analyzer"
        assert analyzer.config.allow_delegation is False
        assert analyzer.config.memory is True
    
    def test_factory_function(self, mock_settings, mock_llm):
        """Test the factory function for backward compatibility."""
        from app.crews.agents.analyzer_agent import create_resume_analyzer_agent
        
        with patch('app.crews.agents.base.base_agent.Agent') as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_class.return_value = mock_agent_instance
            
            tools = [Mock()]
            agent = create_resume_analyzer_agent(tools=tools)
            
            assert agent == mock_agent_instance


class TestResumeOptimizerAgent:
    """Test the resume optimizer agent."""
    
    def test_init(self, mock_settings):
        """Test optimizer agent initialization."""
        optimizer = ResumeOptimizerAgent()
        
        assert optimizer.config.role == "Resume Optimizer"
        assert optimizer.config.allow_delegation is False
        assert optimizer.config.memory is True
        assert optimizer.config.memory_config is not None
    
    def test_get_customization_strategy(self):
        """Test getting customization strategy."""
        optimizer = ResumeOptimizerAgent()
        
        minimal_strategy = optimizer.get_customization_strategy("minimal")
        assert minimal_strategy["content_preservation"] == 0.90
        
        standard_strategy = optimizer.get_customization_strategy("standard")
        assert standard_strategy["content_preservation"] == 0.75
        
        comprehensive_strategy = optimizer.get_customization_strategy("comprehensive")
        assert comprehensive_strategy["content_preservation"] == 0.50
        
        # Test default
        default_strategy = optimizer.get_customization_strategy("invalid")
        assert default_strategy == standard_strategy
