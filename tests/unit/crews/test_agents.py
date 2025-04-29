"""Unit tests for CrewAI agents."""
import pytest
from unittest.mock import patch, MagicMock

from app.crews.agents import create_resume_analyzer_agent, create_resume_optimizer_agent


@pytest.fixture
def mock_tools():
    """Mock tools for testing."""
    return [MagicMock()]


def test_create_resume_analyzer_agent(mock_tools):
    """Test creating a resume analyzer agent."""
    with patch("app.crews.agents.analyzer.Agent") as mock_agent:
        # Setup mock
        mock_agent_instance = MagicMock()
        mock_agent.return_value = mock_agent_instance
        
        # Call the function
        agent = create_resume_analyzer_agent(tools=mock_tools)
        
        # Verify agent was created with correct parameters
        mock_agent.assert_called_once()
        
        # Get the call arguments
        call_args = mock_agent.call_args[1]
        
        # Check key parameters
        assert call_args["role"] == "Resume Analyzer"
        assert "skills" in call_args["goal"]
        assert "expert" in call_args["backstory"]
        assert call_args["tools"] == mock_tools
        
        # Verify the returned agent
        assert agent == mock_agent_instance


def test_create_resume_optimizer_agent(mock_tools):
    """Test creating a resume optimizer agent."""
    with patch("app.crews.agents.optimizer.Agent") as mock_agent:
        # Setup mock
        mock_agent_instance = MagicMock()
        mock_agent.return_value = mock_agent_instance
        
        # Call the function
        agent = create_resume_optimizer_agent(tools=mock_tools)
        
        # Verify agent was created with correct parameters
        mock_agent.assert_called_once()
        
        # Get the call arguments
        call_args = mock_agent.call_args[1]
        
        # Check key parameters
        assert call_args["role"] == "Resume Optimizer"
        assert "tailored" in call_args["goal"]
        assert "professional" in call_args["backstory"]
        assert call_args["tools"] == mock_tools
        assert call_args["memory"] == True
        
        # Verify the returned agent
        assert agent == mock_agent_instance
