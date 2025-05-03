"""CrewAI integration module for Resume Customizer."""
from app.crews.agents import (
    create_resume_analyzer_agent,
    create_resume_optimizer_agent,
    ResumeAnalyzerAgent,
    ResumeOptimizerAgent,
    BaseResumAgent,
    create_resume_analyzer_agent_v2,
    create_resume_optimizer_agent_v2
)

from app.crews.tasks import (
    create_job_analysis_task,
    create_resume_optimization_task,
    JobAnalysisTask,
    ResumeOptimizationTask,
    BaseResumeTask,
    create_job_analysis_task_v2,
    create_resume_optimization_task_v2
)

from app.crews.tools import (
    ResumeProcessorTool,
    JobMatcherTool,
    ResumeTools,
    create_resume_tools,
    create_resume_processor_tool,  
    create_job_matcher_tool,
    BaseResumeTool,
    ToolRegistry
)

from app.crews.flows import (
    ResumeCustomizationFlow,
    ResumeCustomizationFlowV2,
    BaseResumeFlow
)

__all__ = [
    # Legacy Agents
    "create_resume_analyzer_agent",
    "create_resume_optimizer_agent",
    
    # Legacy Tasks
    "create_job_analysis_task",
    "create_resume_optimization_task",
    
    # Legacy Tools
    "ResumeProcessorTool",
    "JobMatcherTool",
    
    # New Agents
    "ResumeAnalyzerAgent",
    "ResumeOptimizerAgent",
    "BaseResumAgent",
    "create_resume_analyzer_agent_v2",
    "create_resume_optimizer_agent_v2",
    
    # New Tasks
    "JobAnalysisTask",
    "ResumeOptimizationTask",
    "BaseResumeTask",
    "create_job_analysis_task_v2",
    "create_resume_optimization_task_v2",
    
    # New Tools
    "ResumeTools",
    "create_resume_tools",
    "create_resume_processor_tool",  
    "create_job_matcher_tool",
    "BaseResumeTool",
    "ToolRegistry",
    
    # Flows
    "ResumeCustomizationFlow",
    "ResumeCustomizationFlowV2",
    "BaseResumeFlow"
]
