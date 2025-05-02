"""Resume customization flow implementation using CrewAI flows.

This module implements the structured flow for the resume customization process,
using CrewAI's Flow feature with typed state management.
"""
import os
import time
from typing import Dict, Any, Optional, Union
from datetime import datetime

from crewai import Agent, LLM
from crewai.flow.flow import Flow, listen, start, router

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError, ResumeNotFoundError, CustomizationError
from app.models.domain.states import (
    ResumeCustomizationState, 
    JobAnalysisStatus, 
    ResumeOptimizationStatus,
    TaskStatus,
    DocumentInfo
)
from app.crews.agents import create_resume_analyzer_agent, create_resume_optimizer_agent
from app.crews.tools import ResumeProcessorTool, JobMatcherTool



class ResumeCustomizationFlow(Flow[ResumeCustomizationState]):
    """Flow for the resume customization process.
    
    This flow orchestrates the entire resume customization process, from
    job description analysis to resume optimization. It manages the state
    transitions and ensures proper data flow between steps.
    
    The @persist decorator ensures that the flow state is persisted
    across process restarts, allowing for resumability of long-running tasks.
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
        super().__init__()
        # Store services for later use (dependency injection)
        self.resume_service = resume_service
        self.storage_service = storage_service
        self.task_service = task_service
        
        # Initialize state with task ID
        initial_state = ResumeCustomizationState(task_id=task_id)
        self.set_initial_state(initial_state)
        
        logger.info(f"Initialized ResumeCustomizationFlow for task {task_id}")
    
    @start()
    def initialize_flow(self):
        """Initialize the flow and set up initial state.
        
        This is the entry point for the flow, marked with @start() decorator.
        It sets up the environment and does basic validation.
        
        Returns:
            str: Status message
        """
        logger.info(f"Starting resume customization flow for task {self.state.task_id}")
        
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
        
        Validates that the required resume and job description exist and
        are accessible before proceeding with the customization process.
        
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
        """Handle case where job description is missing.
        
        Returns:
            str: Error message
        """
        logger.warning(f"Job description missing for task {self.state.task_id}")
        self.state.status = TaskStatus.FAILED
        self.state.error_message = "Job description not found or not accessible"
        self.state.progress = 100.0
        return "Job description not found or not accessible"
    
    @listen("missing_resume")
    def handle_missing_resume(self):
        """Handle case where resume is missing.
        
        Returns:
            str: Error message
        """
        logger.warning(f"Resume missing for task {self.state.task_id}")
        self.state.status = TaskStatus.FAILED
        self.state.error_message = "Resume not found or not accessible"
        self.state.progress = 100.0
        return "Resume not found or not accessible"
    
    @listen("analyze_job")
    def analyze_job_description(self):
        """Analyze the job description using CrewAI agent.
        
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
                if self.storage_service and self.state.job_analysis.job_description.content_path:
                    # Try to load content from storage
                    logger.info("Loading job description content from storage")
                    # Logic to load content would go here using storage_service
                    # This would be implemented when we create the repository pattern later
                
                if not job_description:
                    raise ValueError("Job description content not available")
            
            # Create analyzer agent with LLM
            analyzer_agent = self._create_analyzer_agent()
            
            # Create job analysis task
            from app.crews.tasks.analyze_job import create_job_analysis_task
            job_analysis_task = create_job_analysis_task(
                agent=analyzer_agent,
                job_description=job_description
            )
            
            # Execute the task directly (not using Crew to avoid complexity)
            logger.info("Executing job analysis task")
            
            # Update progress
            self.state.progress = 30.0
            
            # Execute task
            analysis_result = analyzer_agent.execute_task(job_analysis_task)
            
            # Update state with result
            self.state.job_analysis.status = JobAnalysisStatus.COMPLETED
            self.state.job_analysis.analysis_result = analysis_result
            
            # Extract key information from analysis (simplified for now)
            # In a production system, we would parse the structured output properly
            
            # Update progress
            self.state.progress = 50.0
            logger.info(f"Job analysis completed for task {self.state.task_id}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing job: {str(e)}", exc_info=True)
            self.state.job_analysis.status = JobAnalysisStatus.FAILED
            self.state.job_analysis.error_message = str(e)
            self.state.status = TaskStatus.FAILED
            self.state.error_message = f"Job analysis failed: {str(e)}"
            self.state.update_progress()
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
                if self.storage_service and self.state.resume_optimization.resume.content_path:
                    # Try to load content from storage
                    logger.info("Loading resume content from storage")
                    # This would be implemented with the repository pattern later
                
                if not resume_text:
                    raise ValueError("Resume content not available")
            
            # Get job analysis result
            job_analysis_result = self.state.job_analysis.analysis_result
            
            # Get customization level
            customize_level = self.state.resume_optimization.customization_level.value
            
            # Create optimizer agent with LLM
            optimizer_agent = self._create_optimizer_agent()
            
            # Create resume optimization task
            from app.crews.tasks.optimize_resume import create_resume_optimization_task
            optimization_task = create_resume_optimization_task(
                agent=optimizer_agent,
                resume_text=resume_text,
                job_analysis_result=job_analysis_result,
                customize_level=customize_level
            )
            
            # Execute the task directly
            logger.info("Executing resume optimization task")
            
            # Update progress
            self.state.progress = 70.0
            
            # Execute task
            optimized_resume = optimizer_agent.execute_task(optimization_task)
            
            # Update state with result
            self.state.resume_optimization.status = ResumeOptimizationStatus.COMPLETED
            self.state.resume_optimization.optimized_resume = optimized_resume
            
            # Update progress
            self.state.progress = 90.0
            
            # If storage_service is available, save result
            if self.storage_service:
                # Logic to save result would go here
                pass
            
            # Update task status
            self.state.status = TaskStatus.COMPLETED
            self.state.completed_at = datetime.now()
            self.state.progress = 100.0
            
            logger.info(f"Resume optimization completed for task {self.state.task_id}")
            
            return optimized_resume
            
        except Exception as e:
            logger.error(f"Error optimizing resume: {str(e)}", exc_info=True)
            self.state.resume_optimization.status = ResumeOptimizationStatus.FAILED
            self.state.resume_optimization.error_message = str(e)
            self.state.status = TaskStatus.FAILED
            self.state.error_message = f"Resume optimization failed: {str(e)}"
            self.state.update_progress()
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
            }
        }
        
        return result
    
    def _setup_llm_environment(self) -> None:
        """Set up environment variables for LLM API keys.
        
        This method ensures that API keys are properly set in the environment
        for CrewAI components to access them.
        """
        # Same implementation as in ResumeService._setup_llm_environment
        import os
        
        # Explicitly set API keys in environment variables to ensure they're available to CrewAI
        # First, check if API keys are in settings
        llm_api_key = settings.LLM_API_KEY
        openai_api_key = settings.OPENAI_API_KEY
        
        # Log environment status without exposing keys
        logger.info(f"Setting up LLM environment. LLM_API_KEY exists: {bool(llm_api_key)}, OPENAI_API_KEY exists: {bool(openai_api_key)}")
        
        # Set environment variables if they exist in settings
        if llm_api_key:
            os.environ["LLM_API_KEY"] = llm_api_key
            logger.debug("Set LLM_API_KEY in environment")
        
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
            logger.debug("Set OPENAI_API_KEY in environment")
        
        # Validate that we have at least one API key
        if not (llm_api_key or openai_api_key):
            logger.error("No API keys found in settings or environment")
            raise CustomizationError("No LLM API keys configured. Please set LLM_API_KEY or OPENAI_API_KEY.")
        
        # Set LLM model in environment if specified
        if settings.AGENT_LLM:
            os.environ["AGENT_LLM"] = settings.AGENT_LLM
            logger.debug(f"Set AGENT_LLM in environment: {settings.AGENT_LLM}")
        
        # Set AGENT_VERBOSE if specified
        os.environ["AGENT_VERBOSE"] = str(settings.AGENT_VERBOSE).lower()
        os.environ["CREW_VERBOSE"] = str(settings.CREW_VERBOSE).lower()
        
        logger.info("LLM environment setup complete")
    
    def _create_analyzer_agent(self) -> Agent:
        """Create the resume analyzer agent with tools.
        
        Returns:
            Agent: Configured resume analyzer agent
        """
        # Get API key from environment or settings
        api_key = os.environ.get("OPENAI_API_KEY") or settings.OPENAI_API_KEY or settings.LLM_API_KEY
        
        # Get model name from settings or default
        model_name = settings.AGENT_LLM or "gpt-4o"
        
        # Create LLM instance with explicit parameters
        llm = LLM(api_key=api_key, model=model_name)
        
        # Create tools (minimalistic for now)
        # In a production system, we would implement proper tools integration
        tools = []
        
        # Create and return the agent
        analyzer_agent = create_resume_analyzer_agent(tools=tools)
        analyzer_agent.llm = llm  # Explicitly set the LLM
        
        return analyzer_agent
    
    def _create_optimizer_agent(self) -> Agent:
        """Create the resume optimizer agent with tools.
        
        Returns:
            Agent: Configured resume optimizer agent
        """
        # Get API key from environment or settings
        api_key = os.environ.get("OPENAI_API_KEY") or settings.OPENAI_API_KEY or settings.LLM_API_KEY
        
        # Get model name from settings or default
        model_name = settings.AGENT_LLM or "gpt-4o"
        
        # Create LLM instance with explicit parameters
        llm = LLM(api_key=api_key, model=model_name)
        
        # Create tools (minimalistic for now)
        # In a production system, we would implement proper tools integration
        tools = []
        
        # Create and return the agent
        optimizer_agent = create_resume_optimizer_agent(tools=tools)
        optimizer_agent.llm = llm  # Explicitly set the LLM
        
        return optimizer_agent
    
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
        if level not in [e.value for e in self.state.resume_optimization.customization_level.__class__]:
            raise ValueError(f"Invalid customization level: {level}")
        
        self.state.resume_optimization.customization_level = level
        logger.info(f"Set customization level to {level} for task {self.state.task_id}")
    
    def get_result(self) -> Dict[str, Any]:
        """Get the result of the resume customization.
        
        Returns:
            Dict[str, Any]: Result with optimized resume and metadata
        """
        result = {
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
            }
        }
        
        return result
