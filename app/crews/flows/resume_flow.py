"""Resume customization flow implementation using refactored architecture.

This module implements the structured flow for the resume customization process,
using CrewAI's Flow feature with typed state management and improved separation of concerns.
"""
import time
from typing import Dict, Any, Optional
from datetime import datetime

from crewai.flow.flow import listen, start, router

from app.crews.flows.base import BaseResumeFlow
from app.crews.agents.analyzer_agent import ResumeAnalyzerAgent
from app.crews.agents.optimizer_agent import ResumeOptimizerAgent
from app.crews.tasks.analysis_task import JobAnalysisTask
from app.crews.tasks.optimization_task import ResumeOptimizationTask
from app.crews.tools.resume_tools import create_resume_tools
from app.core.logging import logger
from app.models.domain.states import (
    ResumeCustomizationState, 
    JobAnalysisStatus, 
    ResumeOptimizationStatus,
    TaskStatus,
    DocumentInfo
)


class ResumeCustomizationFlow(BaseResumeFlow[ResumeCustomizationState]):
    """Flow for the resume customization process.
    
    This flow orchestrates the entire resume customization process, from
    job description analysis to resume optimization, using the refactored
    agent and task architecture.
    """
    
    def __init__(
        self, 
        task_id: str, 
        resume_service = None, 
        storage_service = None, 
        task_service = None
    ):
        """Initialize the resume customization flow.
        
        Args:
            task_id: Unique identifier for the task
            resume_service: Resume service instance (optional, for dependency injection)
            storage_service: Storage service instance (optional, for dependency injection)
            task_service: Task service instance (optional, for dependency injection)
        """
        # Create initial state
        initial_state = ResumeCustomizationState(task_id=task_id)
        
        # Package services
        services = {
            "resume_service": resume_service,
            "storage_service": storage_service,
            "task_service": task_service
        }
        
        super().__init__(
            task_id=task_id,
            initial_state=initial_state,
            services=services
        )
        
        # Initialize agents and tools
        self.analyzer_agent = None
        self.optimizer_agent = None
        self.tools = None
        
        logger.info(f"Initialized ResumeCustomizationFlow for task {task_id}")
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """Initialize tools for the flow.
        
        Returns:
            Dict[str, Any]: Dictionary of initialized tools
        """
        if self.tools:
            return self.tools
        
        logger.info("Initializing tools for resume customization flow")
        
        # Get resume service
        resume_service = self.get_service("resume_service")
        
        # Create tools
        self.tools = create_resume_tools(resume_service=resume_service)
        
        logger.info(f"Initialized {len(self.tools)} tools")
        return self.tools
    
    def _create_analyzer_agent(self) -> ResumeAnalyzerAgent:
        """Create the resume analyzer agent with tools.
        
        Returns:
            ResumeAnalyzerAgent: Configured analyzer agent
        """
        if self.analyzer_agent:
            return self.analyzer_agent
        
        logger.info("Creating resume analyzer agent")
        
        # Initialize tools
        tools = self._initialize_tools()
        
        # Select appropriate tools for analyzer
        analyzer_tools = [
            tools["keyword_extractor"],
            tools["job_matcher"]
        ]
        
        # Create agent
        self.analyzer_agent = ResumeAnalyzerAgent(tools=analyzer_tools)
        
        return self.analyzer_agent
    
    def _create_optimizer_agent(self) -> ResumeOptimizerAgent:
        """Create the resume optimizer agent with tools.
        
        Returns:
            ResumeOptimizerAgent: Configured optimizer agent
        """
        if self.optimizer_agent:
            return self.optimizer_agent
        
        logger.info("Creating resume optimizer agent")
        
        # Initialize tools
        tools = self._initialize_tools()
        
        # Select appropriate tools for optimizer
        optimizer_tools = [
            tools["resume_processor"],
            tools["ats_optimizer"],
            tools["keyword_extractor"]
        ]
        
        # Create agent
        self.optimizer_agent = ResumeOptimizerAgent(tools=optimizer_tools)
        
        return self.optimizer_agent
    
    @start()
    def initialize_flow(self):
        """Initialize the flow and set up initial state.
        
        This is the entry point for the flow.
        
        Returns:
            str: Status message
        """
        logger.info(f"Starting resume customization flow for task {self.state.task_id}")
        
        # Start flow timing
        self.start_flow()
        
        # Update state to processing
        self.state.status = TaskStatus.PROCESSING
        self.state.started_at = datetime.now()
        self.state.progress = 5.0
        
        # Set up LLM environment
        self._setup_llm_environment()
        
        # Proceed to check resources
        return "Flow initialized successfully"
    
    @listen(initialize_flow)
    def check_resources(self, previous_result):
        """Check if required resources exist.
        
        Args:
            previous_result: Result from the previous step
            
        Returns:
            str: Route for next step
        """
        logger.info(f"Checking resources for task {self.state.task_id}")
        
        # Update progress
        self.state.progress = 10.0
        
        # Check resources and determine next step
        job_ready = self.state.job_analysis.is_ready_for_analysis()
        job_complete = self.state.job_analysis.is_analysis_complete()
        
        resume_ready = self.state.resume_optimization.is_ready_for_optimization(job_complete)
        resume_complete = self.state.resume_optimization.is_optimization_complete()
        
        if not job_ready and not job_complete:
            return "missing_job_description"
        elif job_ready and not job_complete:
            return "analyze_job"
        elif not resume_ready and not resume_complete:
            return "missing_resume"
        elif resume_ready and not resume_complete:
            return "optimize_resume"
        else:
            return "complete"
    
    @router(check_resources)
    def resource_router(self, route):
        """Route to appropriate next step based on resource check.
        
        Args:
            route: Route string from check_resources
            
        Returns:
            str: Next step to execute
        """
        logger.info(f"Routing to {route} for task {self.state.task_id}")
        return route
    
    @listen("missing_job_description")
    def handle_missing_job_description(self):
        """Handle case where job description is missing."""
        logger.warning(f"Job description missing for task {self.state.task_id}")
        self.handle_error(
            ValueError("Job description not found"),
            context="resource_check"
        )
        self.state.progress = 100.0
        return "Job description not found or not accessible"
    
    @listen("missing_resume")
    def handle_missing_resume(self):
        """Handle case where resume is missing."""
        logger.warning(f"Resume missing for task {self.state.task_id}")
        self.handle_error(
            ValueError("Resume not found"),
            context="resource_check"
        )
        self.state.progress = 100.0
        return "Resume not found or not accessible"
    
    @listen("analyze_job")
    def analyze_job_description(self):
        """Analyze the job description using the analyzer agent.
        
        Returns:
            str: Result of job analysis
        """
        logger.info(f"Analyzing job description for task {self.state.task_id}")
        start_time = time.time()
        
        try:
            # Update job analysis state
            self.state.job_analysis.status = JobAnalysisStatus.IN_PROGRESS
            self.state.progress = 20.0
            
            # Get job description text
            job_description = self.state.job_analysis.job_description.content
            
            if not job_description:
                raise ValueError("Job description content not available")
            
            # Create analyzer agent
            analyzer_agent = self._create_analyzer_agent()
            
            # Create job analysis task
            task_creator = JobAnalysisTask(job_description=job_description)
            job_analysis_task = task_creator.get_task(analyzer_agent.get_agent())
            
            # Execute the task
            logger.info("Executing job analysis task")
            self.state.progress = 30.0
            
            # Execute task
            analysis_result = analyzer_agent.get_agent().execute_task(job_analysis_task)
            
            # Update state with result
            self.state.job_analysis.status = JobAnalysisStatus.COMPLETED
            self.state.job_analysis.analysis_result = analysis_result
            
            # Update progress
            self.state.progress = 50.0
            logger.info(f"Job analysis completed for task {self.state.task_id}")
            
            return analysis_result
            
        except Exception as e:
            self.handle_error(e, context="job_analysis")
            self.state.job_analysis.status = JobAnalysisStatus.FAILED
            self.state.job_analysis.error_message = str(e)
            return f"Error: {str(e)}"
        finally:
            # Calculate processing time
            processing_time = time.time() - start_time
            self.state.processing_time_ms = (processing_time * 1000 
                if self.state.processing_time_ms is None 
                else self.state.processing_time_ms + (processing_time * 1000))
    
    @listen("optimize_resume")
    def optimize_resume(self):
        """Optimize the resume based on job analysis.
        
        Returns:
            str: Optimized resume content
        """
        logger.info(f"Optimizing resume for task {self.state.task_id}")
        start_time = time.time()
        
        try:
            # Check if job analysis is complete
            if not self.state.job_analysis.is_analysis_complete():
                raise ValueError("Job analysis must be completed before resume optimization")
            
            # Update resume optimization state
            self.state.resume_optimization.status = ResumeOptimizationStatus.IN_PROGRESS
            self.state.progress = 60.0
            
            # Get resume text
            resume_text = self.state.resume_optimization.resume.content
            
            if not resume_text:
                raise ValueError("Resume content not available")
            
            # Get job analysis result
            job_analysis_result = self.state.job_analysis.analysis_result
            
            # Get customization level
            customize_level = self.state.resume_optimization.customization_level.value
            
            # Create optimizer agent
            optimizer_agent = self._create_optimizer_agent()
            
            # Create resume optimization task
            task_creator = ResumeOptimizationTask(
                resume_text=resume_text,
                job_analysis_result=job_analysis_result,
                customize_level=customize_level
            )
            optimization_task = task_creator.get_task(optimizer_agent.get_agent())
            
            # Execute the task
            logger.info("Executing resume optimization task")
            self.state.progress = 70.0
            
            # Execute task
            optimized_resume = optimizer_agent.get_agent().execute_task(optimization_task)
            
            # Update state with result
            self.state.resume_optimization.status = ResumeOptimizationStatus.COMPLETED
            self.state.resume_optimization.optimized_resume = optimized_resume
            
            # Update progress
            self.state.progress = 90.0
            
            # Update task status
            self.state.status = TaskStatus.COMPLETED
            self.state.completed_at = datetime.now()
            self.state.progress = 100.0
            
            logger.info(f"Resume optimization completed for task {self.state.task_id}")
            
            return optimized_resume
            
        except Exception as e:
            self.handle_error(e, context="resume_optimization")
            self.state.resume_optimization.status = ResumeOptimizationStatus.FAILED
            self.state.resume_optimization.error_message = str(e)
            return f"Error: {str(e)}"
        finally:
            # Calculate processing time
            processing_time = time.time() - start_time
            self.state.processing_time_ms = (processing_time * 1000 
                if self.state.processing_time_ms is None 
                else self.state.processing_time_ms + (processing_time * 1000))
    
    @listen("complete")
    def finalize_flow(self):
        """Finalize the flow and return results.
        
        Returns:
            dict: Final result with optimized resume and metadata
        """
        logger.info(f"Finalizing flow for task {self.state.task_id}")
        
        # End flow timing
        self.end_flow()
        
        # Ensure completion status
        self.state.status = TaskStatus.COMPLETED
        self.state.progress = 100.0
        
        if not self.state.completed_at:
            self.state.completed_at = datetime.now()
        
        # Create result object
        result = {
            "task_id": self.state.task_id,
            "status": self.state.status.value,
            "optimized_resume": self.state.resume_optimization.optimized_resume,
            "metadata": {
                "processing_time_ms": self.state.processing_time_ms,
                "customize_level": self.state.resume_optimization.customization_level.value,
                "started_at": self.state.started_at.isoformat() if self.state.started_at else None,
                "completed_at": self.state.completed_at.isoformat() if self.state.completed_at else None,
                "execution_time_seconds": self.get_execution_time()
            },
            "metrics": self.get_flow_metrics()
        }
        
        return result
    
    def set_job_description(self, job_description_text: str, filename: Optional[str] = None) -> None:
        """Set the job description for analysis.
        
        Args:
            job_description_text: Job description text content
            filename: Optional filename for reference
        """
        document_info = DocumentInfo(
            document_id=f"{self.state.task_id}_job",
            filename=filename,
            content=job_description_text,
            size_bytes=len(job_description_text.encode("utf-8")) if job_description_text else None,
            extracted_at=datetime.now()
        )
        
        self.state.job_analysis.job_description = document_info
        logger.info(f"Set job description for task {self.state.task_id}")
    
    def set_resume(self, resume_text: str, filename: Optional[str] = None) -> None:
        """Set the resume for optimization.
        
        Args:
            resume_text: Resume text content
            filename: Optional filename for reference
        """
        document_info = DocumentInfo(
            document_id=f"{self.state.task_id}_resume",
            filename=filename,
            content=resume_text,
            size_bytes=len(resume_text.encode("utf-8")) if resume_text else None,
            extracted_at=datetime.now()
        )
        
        self.state.resume_optimization.resume = document_info
        logger.info(f"Set resume for task {self.state.task_id}")
    
    def set_customization_level(self, level: str) -> None:
        """Set the customization level for resume optimization.
        
        Args:
            level: Customization level (minimal, standard, comprehensive)
        """
        self.state.resume_optimization.customization_level = level
        logger.info(f"Set customization level to {level} for task {self.state.task_id}")
    
    def get_result(self) -> Dict[str, Any]:
        """Get the result of the resume customization.
        
        Returns:
            Dict[str, Any]: Result with optimized resume and metadata
        """
        return {
            "task_id": self.state.task_id,
            "status": self.state.status.value,
            "progress": self.state.progress,
            "optimized_resume": self.state.resume_optimization.optimized_resume,
            "error_message": self.state.error_message,
            "metadata": {
                "processing_time_ms": self.state.processing_time_ms,
                "customize_level": self.state.resume_optimization.customization_level.value,
                "started_at": self.state.started_at.isoformat() if self.state.started_at else None,
                "completed_at": self.state.completed_at.isoformat() if self.state.completed_at else None,
                "execution_time_seconds": self.get_execution_time()
            }
        }
