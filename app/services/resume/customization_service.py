"""Service for resume customization operations."""
import time
import os
from typing import Dict, Optional, Any, List
from pathlib import Path

from crewai import Crew, Process, LLM, Task, Agent, CrewAIException
from pydantic import BaseModel, ConfigDict, Field

from app.core.logging import logger
from app.core.config import settings
from app.core.exceptions import DocumentProcessingError, ResumeNotFoundError, CustomizationError
from app.services.resume.base import BaseService
from app.services.resume.storage_service import ResumeStorageService
from app.repositories.task_repository import TaskRepository
from app.services.resume.extraction_service import ResumeExtractionService


class JobAnalysisState(BaseModel):
    """State for job analysis phase of resume customization."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    job_description: str = ""
    analysis_result: str = ""
    required_skills: List[str] = Field(default_factory=list)
    required_experience: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    completed: bool = False
    error: Optional[str] = None


class ResumeOptimizationState(BaseModel):
    """State for resume optimization phase of customization."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    resume_text: str = ""
    optimized_resume: str = ""
    completed: bool = False
    error: Optional[str] = None


class CustomizationState(BaseModel):
    """Complete state for resume customization process."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    task_id: str
    resume_id: str
    customize_level: str = "standard"
    job_analysis: JobAnalysisState = Field(default_factory=JobAnalysisState)
    resume_optimization: ResumeOptimizationState = Field(default_factory=ResumeOptimizationState)
    status: str = "processing"
    progress: float = 0.0
    error_message: Optional[str] = None
    started_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None


class ResumeCustomizationService(BaseService[Dict[str, Any], str]):
    """Service for customizing resumes based on job descriptions.
    
    This service is responsible for coordinating the AI-powered customization
    of resumes to match job descriptions. It manages the entire customization
    workflow, from job analysis to resume optimization.
    """
    
    def __init__(
        self, 
        extraction_service: ResumeExtractionService,
        storage_service: ResumeStorageService,
        task_repository: TaskRepository
    ):
        """Initialize the resume customization service.
        
        Args:
            extraction_service: Extraction service for resume text
            storage_service: Storage service for persistence
            task_repository: Repository for task data access
        """
        self.extraction_service = extraction_service
        self.storage_service = storage_service
        self.task_repository = task_repository
        logger.info("Initialized ResumeCustomizationService")
    
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get customization task by ID.
        
        Args:
            id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Customization task data if found
        """
        try:
            # Get task metadata
            task = await self.task_repository.get_task(id)
            
            if not task:
                logger.debug(f"No task found for ID {id}")
                return None
            
            # For completed tasks, include the result
            if task.get("status") == "completed":
                result_content = await self.storage_service.get_result(id)
                
                return {
                    "task_id": id,
                    "status": "completed",
                    "result": result_content,
                    "metadata": task
                }
            
            # For other task statuses
            return {
                "task_id": id,
                "status": task.get("status", "unknown"),
                "progress": task.get("progress", 0.0),
                "message": task.get("message", ""),
                "metadata": task
            }
            
        except Exception as e:
            logger.error(f"Error getting customization task {id}: {str(e)}", exc_info=True)
            return None
    
    async def exists(self, id: str) -> bool:
        """Check if a customization task exists.
        
        Args:
            id: Task identifier
            
        Returns:
            bool: True if the task exists, False otherwise
        """
        try:
            task = await self.task_repository.get_task(id)
            return task is not None
        except Exception as e:
            logger.error(f"Error checking if task {id} exists: {str(e)}", exc_info=True)
            return False
    
    def _setup_llm_environment(self) -> None:
        """Set up environment variables for LLM API keys.
        
        This method ensures that API keys are properly set in the environment
        for CrewAI components to access them.
        """
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
    
    def _create_llm(self) -> LLM:
        """Create an LLM instance for CrewAI.
        
        Returns:
            LLM: LLM instance
            
        Raises:
            CustomizationError: If no API key is configured
        """
        # Get API key from settings
        api_key = settings.LLM_API_KEY or settings.OPENAI_API_KEY
        if not api_key:
            raise CustomizationError("No LLM API key configured")
        
        # Get model name from settings
        model_name = settings.AGENT_LLM
        if not model_name:
            model_name = "gpt-4o"  # Default to a reasonable model if not specified
            logger.warning(f"No LLM model specified, using default: {model_name}")
        
        # Initialize LLM with explicit parameters
        llm = LLM(api_key=api_key, model=model_name)
        logger.info(f"Initialized LLM with model: {model_name}")
        
        return llm
    
    def _extract_crew_result(self, crew_output: Any) -> str:
        """Extract the result string from different CrewAI output formats.
        
        Args:
            crew_output: The output from crew.kickoff()
            
        Returns:
            str: Extracted result text or empty string if extraction fails
        """
        # Try different methods to extract the result
        extraction_methods = [
            # Method 1: Access as tasks[0].output.raw
            lambda x: x.tasks[0].output.raw if hasattr(x, 'tasks') and x.tasks and hasattr(x.tasks[0], 'output') and hasattr(x.tasks[0].output, 'raw') else None,
            
            # Method 2: Access as task_output
            lambda x: x.task_output if hasattr(x, 'task_output') else None,
            
            # Method 3: Access as raw
            lambda x: x.raw if hasattr(x, 'raw') else None,
            
            # Method 4: Access as output
            lambda x: x.output if hasattr(x, 'output') else None,
            
            # Method 5: Access as result
            lambda x: x.result if hasattr(x, 'result') else None,
            
            # Method 6: Convert to dict and stringify
            lambda x: str(x.to_dict()) if hasattr(x, 'to_dict') else None,
            
            # Method 7: Check for getattr with specific attributes
            lambda x: getattr(x, 'content', None),
            
            # Method 8: Access first element if it's a list
            lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None,
            
            # Method 9: Try __str__ method
            lambda x: str(x)
        ]
        
        # Try each method and return the first successful result
        for i, method in enumerate(extraction_methods):
            try:
                result = method(crew_output)
                if result:
                    logger.info(f"Successfully extracted result using method {i+1}")
                    return result
            except (AttributeError, IndexError, TypeError) as e:
                logger.debug(f"Extraction method {i+1} failed: {str(e)}")
                continue
        
        # If all methods fail, return an empty string
        logger.warning("All extraction methods failed")
        return ""
    
    async def _create_job_analysis_task(
        self, agent: Agent, job_description: str
    ) -> Task:
        """Create a task for analyzing a job description.
        
        Args:
            agent: The CrewAI agent to assign the task to
            job_description: The job description text
            
        Returns:
            Task: The job analysis task
        """
        from app.crews.tasks.analyze_job import create_job_analysis_task
        
        return create_job_analysis_task(
            agent=agent,
            job_description=job_description
        )
    
    async def _create_resume_optimization_task(
        self,
        agent: Agent,
        resume_text: str,
        job_analysis_result: str,
        customize_level: str
    ) -> Task:
        """Create a task for optimizing a resume.
        
        Args:
            agent: The CrewAI agent to assign the task to
            resume_text: The original resume text
            job_analysis_result: The job analysis result
            customize_level: The level of customization
            
        Returns:
            Task: The resume optimization task
        """
        from app.crews.tasks.optimize_resume import create_resume_optimization_task
        
        return create_resume_optimization_task(
            agent=agent,
            resume_text=resume_text,
            job_analysis_result=job_analysis_result,
            customize_level=customize_level
        )
    
    async def _create_fallback_optimization_task(
        self,
        agent: Agent,
        resume_text: str,
        job_description_text: str,
        customize_level: str
    ) -> Task:
        """Create a fallback task for optimizing a resume.
        
        This method is used when the standard approach fails, typically due to
        formatting issues with the job analysis result.
        
        Args:
            agent: The CrewAI agent to assign the task to
            resume_text: The original resume text
            job_description_text: The original job description text
            customize_level: The level of customization
            
        Returns:
            Task: The fallback resume optimization task
        """
        from app.crews.tasks.optimize_resume_fallback import create_resume_optimization_fallback_task
        
        return create_resume_optimization_fallback_task(
            agent=agent,
            resume_text=resume_text,
            job_description_text=job_description_text,
            customize_level=customize_level
        )
    
    async def _create_tools(self) -> List[Any]:
        """Create tools for CrewAI agents.
        
        Returns:
            List[Any]: List of tools
        """
        # Try with class-based tools first (more compatible with some CrewAI versions)
        try:
            from app.crews.tools.resume_processor import ResumeProcessorTool, JobMatcherTool
            
            # Create class-based tool instances
            resume_processor_tool = ResumeProcessorTool(resume_service=self)
            job_matcher_tool = JobMatcherTool() 
            
            logger.info("Created class-based tools for CrewAI integration")
            return [resume_processor_tool, job_matcher_tool]
            
        except Exception as tool_error:
            # Fallback to function-based tools if class-based tools fail
            logger.warning(f"Class-based tools failed: {str(tool_error)}, falling back to function-based tools")
            
            from app.crews.tools.resume_processor import create_resume_processor_tool, create_job_matcher_tool
            
            # Create function-based tool instances
            resume_processor = create_resume_processor_tool(self)
            job_matcher = create_job_matcher_tool()
            
            logger.info(f"Created function-based tools: {type(resume_processor)}, {type(job_matcher)}")
            return [resume_processor, job_matcher]
    
    async def _create_agents(self, llm: LLM, tools: List[Any]) -> Dict[str, Agent]:
        """Create agents for CrewAI.
        
        Args:
            llm: LLM instance
            tools: List of tools
            
        Returns:
            Dict[str, Agent]: Dictionary of agent name to agent
        """
        from app.crews.agents import create_resume_analyzer_agent, create_resume_optimizer_agent
        
        # Create analyzer agent
        analyzer_agent = create_resume_analyzer_agent(tools=tools)
        analyzer_agent.llm = llm  # Explicitly set the LLM
        
        # Create optimizer agent
        optimizer_agent = create_resume_optimizer_agent(tools=tools)
        optimizer_agent.llm = llm  # Explicitly set the LLM
        
        return {
            "analyzer": analyzer_agent,
            "optimizer": optimizer_agent
        }
    
    async def _run_job_analysis(
        self, crew: Crew, state: CustomizationState
    ) -> str:
        """Run job analysis task with the crew.
        
        Args:
            crew: The CrewAI crew instance
            state: The customization state
            
        Returns:
            str: Job analysis result
            
        Raises:
            CustomizationError: If the job analysis fails
        """
        logger.info("Running job analysis with CrewAI")
        try:
            # Run first task (job analysis)
            logger.info("Kicking off job analysis crew")
            crew_output = crew.kickoff()
            logger.info(f"Received crew output type: {type(crew_output)}")
            
            # Extract the result
            result = self._extract_crew_result(crew_output)
            
            if result:
                logger.info("Job analysis completed successfully")
                # Update state
                state.job_analysis.analysis_result = result
                state.job_analysis.completed = True
                state.progress = 60.0
                
                return result
            else:
                # If we couldn't extract a result, return the string representation
                logger.warning("Could not extract structured output, returning string representation")
                fallback_result = str(crew_output)
                
                # Update state
                state.job_analysis.analysis_result = fallback_result
                state.job_analysis.completed = True
                state.progress = 60.0
                
                return fallback_result
            
        except Exception as e:
            logger.error(f"Error during job analysis: {str(e)}", exc_info=True)
            
            # Update state
            state.job_analysis.error = str(e)
            state.error_message = f"Job analysis failed: {str(e)}"
            
            raise CustomizationError(f"Job analysis failed: {str(e)}")
    
    async def _run_resume_optimization(
        self,
        crew: Crew,
        optimizer_agent: Agent,
        resume_text: str,
        job_analysis_result: str,
        customize_level: str,
        state: CustomizationState
    ) -> str:
        """Run resume optimization task with the crew.
        
        Args:
            crew: The CrewAI crew instance
            optimizer_agent: The resume optimizer agent
            resume_text: The original resume text
            job_analysis_result: The result of job analysis
            customize_level: The level of customization
            state: The customization state
            
        Returns:
            str: Optimized resume text
            
        Raises:
            CustomizationError: If the optimization fails
        """
        logger.info(f"Running resume optimization with customize level: {customize_level}")
        try:
            # Create and add the optimization task
            optimization_task = await self._create_resume_optimization_task(
                agent=optimizer_agent,
                resume_text=resume_text,
                job_analysis_result=job_analysis_result,
                customize_level=customize_level
            )
            
            # Replace crew tasks with the optimization task
            crew.tasks = [optimization_task]
            
            # Run the optimization task
            logger.info("Kicking off resume optimization crew")
            crew_output = crew.kickoff()
            logger.info(f"Received optimization crew output type: {type(crew_output)}")
            
            # Extract the result
            result = self._extract_crew_result(crew_output)
            
            if result:
                logger.info("Resume optimization completed successfully")
                # Update state
                state.resume_optimization.optimized_resume = result
                state.resume_optimization.completed = True
                state.progress = 100.0
                
                return result
            else:
                # If we couldn't extract a result, return the string representation
                logger.warning("Could not extract structured output from optimization, returning string representation")
                fallback_result = str(crew_output)
                
                # Update state
                state.resume_optimization.optimized_resume = fallback_result
                state.resume_optimization.completed = True
                state.progress = 100.0
                
                return fallback_result
            
        except Exception as e:
            logger.error(f"Error during resume optimization: {str(e)}", exc_info=True)
            
            # Update state
            state.resume_optimization.error = str(e)
            state.error_message = f"Resume optimization failed: {str(e)}"
            
            raise CustomizationError(f"Resume optimization failed: {str(e)}")
    
    async def _run_resume_optimization_fallback(
        self,
        crew: Crew,
        optimizer_agent: Agent,
        resume_text: str,
        job_description_text: str,
        customize_level: str,
        state: CustomizationState
    ) -> str:
        """Run resume optimization with a fallback approach.
        
        Args:
            crew: The CrewAI crew instance
            optimizer_agent: The resume optimizer agent
            resume_text: The original resume text
            job_description_text: The original job description text
            customize_level: The level of customization
            state: The customization state
            
        Returns:
            str: Optimized resume text
            
        Raises:
            CustomizationError: If the optimization fails
        """
        logger.info(f"Running FALLBACK resume optimization with customize level: {customize_level}")
        try:
            # Create the fallback task
            fallback_task = await self._create_fallback_optimization_task(
                agent=optimizer_agent,
                resume_text=resume_text,
                job_description_text=job_description_text,
                customize_level=customize_level
            )
            
            # Replace crew tasks with the fallback task
            crew.tasks = [fallback_task]
            
            # Run the optimization task
            logger.info("Kicking off fallback resume optimization crew")
            crew_output = crew.kickoff()
            logger.info(f"Received fallback optimization crew output type: {type(crew_output)}")
            
            # Extract the result
            result = self._extract_crew_result(crew_output)
            
            if result:
                logger.info("Fallback resume optimization completed successfully")
                # Update state
                state.resume_optimization.optimized_resume = result
                state.resume_optimization.completed = True
                state.progress = 100.0
                
                return result
            else:
                # If we couldn't extract a result, return the string representation
                logger.warning("Could not extract structured output from fallback optimization, returning string representation")
                fallback_result = str(crew_output)
                
                # Update state
                state.resume_optimization.optimized_resume = fallback_result
                state.resume_optimization.completed = True
                state.progress = 100.0
                
                return fallback_result
            
        except Exception as e:
            logger.error(f"Error during fallback resume optimization: {str(e)}", exc_info=True)
            
            # Update state
            state.resume_optimization.error = str(e)
            state.error_message = f"Fallback resume optimization failed: {str(e)}"
            
            raise CustomizationError(f"Fallback resume optimization failed: {str(e)}")
    
    async def customize_resume(
        self, 
        resume_id: str, 
        job_description: str, 
        task_id: str,
        customize_level: str = "standard"
    ) -> str:
        """Customize a resume based on a job description using CrewAI.
        
        Args:
            resume_id: Resume task identifier
            job_description: Job description text
            task_id: New task identifier for customization
            customize_level: Level of customization (minimal, standard, comprehensive)
            
        Returns:
            str: Task ID for the customization task
            
        Raises:
            ResumeNotFoundError: If the resume doesn't exist
            CustomizationError: If the customization process fails
        """
        start_time = time.time()
        logger.info(f"Starting resume customization for resume {resume_id}")
        
        # Create state object
        state = CustomizationState(
            task_id=task_id,
            resume_id=resume_id,
            customize_level=customize_level,
            started_at=start_time,
            progress=0.0
        )
        
        # Check if resume exists
        if not await self.extraction_service.exists(resume_id):
            logger.error(f"Resume {resume_id} not found for customization")
            
            # Update state
            state.status = "failed"
            state.error_message = f"Resume {resume_id} not found"
            
            raise ResumeNotFoundError(resume_id)
        
        # Initialize task status
        await self.task_repository.update_task(
            task_id=task_id,
            status="processing",
            progress=0.0,
            resume_id=resume_id,
            customization_type="job_description",
            customize_level=customize_level,
            started_at=time.time()
        )
        
        try:
            # Get resume text
            resume_data = await self.extraction_service.get_by_id(resume_id)
            if not resume_data or "text" not in resume_data:
                # Update state
                state.status = "failed"
                state.error_message = "Resume text not available"
                
                # Update task
                await self.task_repository.update_task(
                    task_id=task_id,
                    status="failed",
                    progress=100.0,
                    error="Resume text not available",
                    processing_time_ms=(time.time() - start_time) * 1000
                )
                
                raise CustomizationError("Resume text not available")
            
            resume_text = resume_data["text"]
            logger.info(f"Retrieved resume text for customization, length: {len(resume_text)}")
            
            # Update state
            state.resume_optimization.resume_text = resume_text
            state.progress = 10.0
            
            # Update task
            await self.task_repository.update_task(
                task_id=task_id, 
                status="processing", 
                progress=10.0,
                message="Retrieved resume text"
            )
            
            # Set up environment
            self._setup_llm_environment()
            
            # Create LLM
            llm = self._create_llm()
            
            # Create tools
            tools = await self._create_tools()
            
            # Create agents
            agents = await self._create_agents(llm, tools)
            
            # Update state
            state.progress = 20.0
            
            # Update task
            await self.task_repository.update_task(
                task_id=task_id, 
                status="processing", 
                progress=20.0,
                message="Created AI agents"
            )
            
            # Create job analysis task
            job_analysis_task = await self._create_job_analysis_task(
                agent=agents["analyzer"],
                job_description=job_description
            )
            
            # Update state
            state.job_analysis.job_description = job_description
            state.progress = 30.0
            
            # Update task
            await self.task_repository.update_task(
                task_id=task_id, 
                status="processing", 
                progress=30.0,
                message="Analyzing job description"
            )
            
            # Create crew
            crew = Crew(
                agents=[agents["analyzer"], agents["optimizer"]],
                tasks=[job_analysis_task],
                verbose=settings.CREW_VERBOSE,
                process=Process.sequential
            )
            
            try:
                # Execute job analysis
                job_analysis_result = await self._run_job_analysis(crew, state)
                
                # Log the job analysis result for debugging (truncated)
                result_preview = str(job_analysis_result)[:200] + "..." if len(str(job_analysis_result)) > 200 else str(job_analysis_result)
                logger.info(f"Job analysis result: {result_preview}")
                
                # Update task
                await self.task_repository.update_task(
                    task_id=task_id, 
                    status="processing", 
                    progress=60.0,
                    message="Job analysis completed, optimizing resume"
                )
                
                # Create and execute resume optimization task
                optimized_resume = await self._run_resume_optimization(
                    crew=crew,
                    optimizer_agent=agents["optimizer"],
                    resume_text=resume_text,
                    job_analysis_result=job_analysis_result,
                    customize_level=customize_level,
                    state=state
                )
                
            except AttributeError as e:
                if "'str' object has no attribute 'get'" in str(e):
                    # Special handling for this specific error with a workaround
                    logger.warning("Handling AttributeError with job analysis result")
                    
                    # Update task
                    await self.task_repository.update_task(
                        task_id=task_id, 
                        status="processing", 
                        progress=60.0,
                        message="Job analysis completed with formatting issues, optimizing resume"
                    )
                    
                    # Create a simplified optimization task without the problematic context
                    optimized_resume = await self._run_resume_optimization_fallback(
                        crew=crew,
                        optimizer_agent=agents["optimizer"],
                        resume_text=resume_text,
                        job_description_text=job_description,
                        customize_level=customize_level,
                        state=state
                    )
                else:
                    # Re-raise if it's not the specific error we're handling
                    raise
            
            # Store the result
            await self.storage_service.save_result(task_id, optimized_resume)
            
            # Update state
            state.status = "completed"
            state.progress = 100.0
            state.completed_at = time.time()
            
            # Update task status to completed
            completion_time = time.time() - start_time
            await self.task_repository.update_task(
                task_id=task_id,
                status="completed",
                progress=100.0,
                message="Resume customization completed",
                processing_time_ms=completion_time * 1000,
                completion_time=time.time()
            )
            
            logger.info(
                f"Resume customization completed for task {task_id}, "
                f"took {completion_time:.2f} seconds"
            )
            
            return task_id
            
        except Exception as e:
            # Handle specific error types
            if "api_key" in str(e).lower() or "authentication" in str(e).lower():
                error_message = f"LLM API authentication failed: {str(e)}"
                logger.error(error_message, exc_info=True)
                
                # Update state
                state.status = "failed"
                state.error_message = "API key authentication failed. Please check your API key configuration."
                
                # Update task
                await self.task_repository.update_task(
                    task_id=task_id,
                    status="failed",
                    progress=100.0,
                    error="API key authentication failed. Please check your API key configuration.",
                    processing_time_ms=(time.time() - start_time) * 1000
                )
                
                raise CustomizationError("API key authentication failed. Please check your API key configuration.")
            else:
                # Handle general errors
                error_message = f"Resume customization failed: {str(e)}"
                logger.error(error_message, exc_info=True)
                
                # Update state
                state.status = "failed"
                state.error_message = str(e)
                state.completed_at = time.time()
                
                # Update task status to failed
                await self.task_repository.update_task(
                    task_id=task_id,
                    status="failed",
                    progress=100.0,
                    error=str(e),
                    processing_time_ms=(time.time() - start_time) * 1000
                )
                
                raise CustomizationError(error_message)


# Factory function for dependency injection
def get_resume_customization_service(
    extraction_service: ResumeExtractionService,
    storage_service: ResumeStorageService,
    task_repository: TaskRepository
) -> ResumeCustomizationService:
    """Get resume customization service instance.
    
    Args:
        extraction_service: Extraction service
        storage_service: Storage service
        task_repository: Task repository
        
    Returns:
        ResumeCustomizationService: Resume customization service instance
    """
    return ResumeCustomizationService(
        extraction_service=extraction_service,
        storage_service=storage_service,
        task_repository=task_repository
    )
