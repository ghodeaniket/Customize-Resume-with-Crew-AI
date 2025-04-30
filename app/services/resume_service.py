"""Service for resume processing and customization."""
import time
from typing import Dict, Optional, Any, BinaryIO, List
from pathlib import Path

from crewai import Crew, Process, LLM
from fastapi import UploadFile, BackgroundTasks

from app.core.logging import logger
from app.core.config import settings
from app.core.exceptions import DocumentProcessingError, ResumeNotFoundError, CustomizationError
from app.infrastructure.document_processor import DocumentProcessor
from app.services.document_storage_service import DocumentStorageService
from app.services.task_service import TaskService

# Import CrewAI components
from app.crews.agents import create_resume_analyzer_agent, create_resume_optimizer_agent
from app.crews.tasks import create_job_analysis_task, create_resume_optimization_task
from app.crews.tools import ResumeProcessorTool, JobMatcherTool


class ResumeService:
    """Service for processing and customizing resumes."""
    
    def __init__(
        self, 
        document_processor: DocumentProcessor,
        storage_service: DocumentStorageService,
        task_service: TaskService
    ):
        """Initialize the resume service.
        
        Args:
            document_processor: Document processor for text extraction
            storage_service: Storage service for document persistence
            task_service: Task service for tracking progress
        """
        self.document_processor = document_processor
        self.storage_service = storage_service
        self.task_service = task_service
        logger.info("Initialized ResumeService")
    
    async def process_resume(
        self, file_content: bytes, filename: str, task_id: str
    ) -> Dict[str, Any]:
        """Process a resume file.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            task_id: Unique task identifier
            
        Returns:
            Dict[str, Any]: Processing result with metadata
            
        Raises:
            DocumentProcessingError: If processing fails
        """
        start_time = time.time()
        logger.info(f"Processing resume {filename} for task {task_id}")
        
        try:
            # Save original document
            file_path = await self.storage_service.save_document(
                file_content, task_id, filename
            )
            
            # Extract text
            extracted_text = await self.document_processor.extract_text_from_bytes(
                file_content, filename=filename
            )
            
            # Save extracted text
            text_path = await self.storage_service.save_extracted_text(
                extracted_text, task_id
            )
            
            # Update metadata with processing results
            metadata = {
                "status": "completed",
                "processing_time_ms": (time.time() - start_time) * 1000,
                "text_length": len(extracted_text)
            }
            await self.storage_service.save_metadata(task_id, metadata)
            
            logger.info(
                f"Resume processing completed for task {task_id}, "
                f"extracted {len(extracted_text)} characters"
            )
            
            result = {
                "task_id": task_id,
                "filename": filename,
                "text": extracted_text,
                "text_path": str(text_path),
                "original_path": str(file_path),
                "status": "completed"
            }
            
            return result
            
        except Exception as e:
            # Update metadata with error
            error_metadata = {
                "status": "failed",
                "error": str(e),
                "processing_time_ms": (time.time() - start_time) * 1000
            }
            await self.storage_service.save_metadata(task_id, error_metadata)
            
            logger.error(f"Resume processing failed for task {task_id}: {str(e)}", exc_info=True)
            raise DocumentProcessingError(detail=f"Resume processing failed: {str(e)}")
    
    async def resume_exists(self, task_id: str) -> bool:
        """Check if a resume exists.
        
        Args:
            task_id: Task identifier
            
        Returns:
            bool: True if the resume exists, False otherwise
        """
        logger.debug(f"Checking if resume {task_id} exists")
        
        metadata = await self.storage_service.get_metadata(task_id)
        document_path = await self.storage_service.get_original_document_path(task_id)
        
        return bool(metadata and document_path)
    
    async def get_resume_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get resume data by task ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Resume data if available
        """
        logger.debug(f"Getting resume data for task {task_id}")
        
        if not await self.resume_exists(task_id):
            logger.warning(f"Resume {task_id} does not exist")
            return None
        
        try:
            # Get metadata and extracted text
            metadata = await self.storage_service.get_metadata(task_id)
            extracted_text = await self.storage_service.get_extracted_text(task_id)
            
            if not extracted_text:
                logger.warning(f"No extracted text found for resume {task_id}")
            
            return {
                "task_id": task_id,
                "metadata": metadata,
                "text": extracted_text,
                "status": metadata.get("status", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Error getting resume data for task {task_id}: {str(e)}", exc_info=True)
            return None
    
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
        
        # Check if resume exists
        if not await self.resume_exists(resume_id):
            logger.error(f"Resume {resume_id} not found for customization")
            raise ResumeNotFoundError(resume_id)
        
        # Initialize task status
        await self.task_service.update_task(
            task_id=task_id,
            status="processing",
            progress=0.0,
            resume_id=resume_id,
            customization_type="job_description",
            customize_level=customize_level,
            started_at=start_time
        )
        
        try:
            # Get resume text
            resume_data = await self.get_resume_data(resume_id)
            if not resume_data or "text" not in resume_data:
                raise CustomizationError("Resume text not available")
            
            resume_text = resume_data["text"]
            logger.info(f"Retrieved resume text for customization, length: {len(resume_text)}")
            
            # Update progress
            await self.task_service.update_task(
                task_id=task_id, 
                status="processing", 
                progress=10.0,
                message="Retrieved resume text"
            )
            
            # Set environment variables for LLM API keys
            self._setup_llm_environment()
            
            # Create LLM instance with API key and model
            api_key = settings.LLM_API_KEY or settings.OPENAI_API_KEY
            if not api_key:
                raise CustomizationError("No LLM API key configured")
            
            model_name = settings.AGENT_LLM
            if not model_name:
                model_name = "gpt-4o" # Default to a reasonable model if not specified
                logger.warning(f"No LLM model specified, using default: {model_name}")
            
            # Initialize LLM with explicit parameters
            llm = LLM(api_key=api_key, model=model_name)
            logger.info(f"Initialized LLM with model: {model_name}")
            
            # Try with class-based tools first (more compatible with some CrewAI versions)
            try:
                from app.crews.tools.resume_processor import ResumeProcessorTool, JobMatcherTool
                
                # Create class-based tool instances
                resume_processor_tool = ResumeProcessorTool(resume_service=self)
                job_matcher_tool = JobMatcherTool() 
                
                logger.info("Created class-based tools for CrewAI integration")
                tools_to_use = [resume_processor_tool, job_matcher_tool]
                
            except Exception as tool_error:
                # Fallback to function-based tools if class-based tools fail
                logger.warning(f"Class-based tools failed: {str(tool_error)}, falling back to function-based tools")
                
                from app.crews.tools.resume_processor import create_resume_processor_tool, create_job_matcher_tool
                
                # Create function-based tool instances
                resume_processor = create_resume_processor_tool(self)
                job_matcher = create_job_matcher_tool()
                
                logger.info(f"Created function-based tools: {type(resume_processor)}, {type(job_matcher)}")
                tools_to_use = [resume_processor, job_matcher]
            
            # Create agents with explicit LLM and tools
            analyzer_agent = create_resume_analyzer_agent(
                tools=tools_to_use
            )
            analyzer_agent.llm = llm  # Explicitly set the LLM
            
            optimizer_agent = create_resume_optimizer_agent(
                tools=tools_to_use
            )
            optimizer_agent.llm = llm  # Explicitly set the LLM
            
            # Update progress
            await self.task_service.update_task(
                task_id=task_id, 
                status="processing", 
                progress=20.0,
                message="Created AI agents"
            )
            
            # Create tasks
            job_analysis_task = create_job_analysis_task(
                agent=analyzer_agent,
                job_description=job_description
            )
            
            # Update progress
            await self.task_service.update_task(
                task_id=task_id, 
                status="processing", 
                progress=30.0,
                message="Analyzing job description"
            )
            
            # Create crew with explicit verbose setting and process
            crew = Crew(
                agents=[analyzer_agent, optimizer_agent],
                tasks=[job_analysis_task],
                verbose=settings.CREW_VERBOSE,
                process=Process.sequential
            )
            
            try:
                # Execute job analysis
                job_analysis_result = await self._run_job_analysis(crew)
                
                # Log the job analysis result for debugging (truncated)
                result_preview = str(job_analysis_result)[:200] + "..." if len(str(job_analysis_result)) > 200 else str(job_analysis_result)
                logger.info(f"Job analysis result type: {type(job_analysis_result)}, preview: {result_preview}")
                
                # Update progress
                await self.task_service.update_task(
                    task_id=task_id, 
                    status="processing", 
                    progress=60.0,
                    message="Job analysis completed, optimizing resume"
                )
                
                # Create and execute resume optimization task
                optimized_resume = await self._run_resume_optimization(
                    crew=crew,
                    optimizer_agent=optimizer_agent,
                    resume_text=resume_text,
                    job_analysis_result=job_analysis_result,
                    customize_level=customize_level
                )
            except AttributeError as e:
                if "'str' object has no attribute 'get'" in str(e):
                    # Special handling for this specific error with a workaround
                    logger.warning("Handling AttributeError with job analysis result")
                    
                    # Update progress despite the error
                    await self.task_service.update_task(
                        task_id=task_id, 
                        status="processing", 
                        progress=60.0,
                        message="Job analysis completed with formatting issues, optimizing resume"
                    )
                    
                    # Create a simplified optimization task without the problematic context
                    optimized_resume = await self._run_resume_optimization_fallback(
                        crew=crew,
                        optimizer_agent=optimizer_agent,
                        resume_text=resume_text,
                        job_description_text=job_description,  # Use original job description
                        customize_level=customize_level
                    )
                else:
                    # Re-raise if it's not the specific error we're handling
                    raise
            
            # Store the result
            await self.storage_service.save_result(task_id, optimized_resume)
            
            # Update task status to completed
            completion_time = time.time() - start_time
            await self.task_service.update_task(
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
                await self.task_service.update_task(
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
                
                # Update task status to failed
                await self.task_service.update_task(
                    task_id=task_id,
                    status="failed",
                    progress=100.0,
                    error=str(e),
                    processing_time_ms=(time.time() - start_time) * 1000
                )
                
                raise CustomizationError(error_message)
    
    def _setup_llm_environment(self) -> None:
        """Set up environment variables for LLM API keys.
        
        This method ensures that API keys are properly set in the environment
        for CrewAI components to access them.
        """
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
    
    async def _run_job_analysis(self, crew: Crew) -> str:
        """Run job analysis task with the crew.
        
        Args:
            crew: The CrewAI crew instance
            
        Returns:
            str: Job analysis result
        """
        logger.info("Running job analysis with CrewAI")
        try:
            # Run first task (job analysis)
            logger.info("Kicking off job analysis crew")
            crew_output = crew.kickoff()
            logger.info(f"Received crew output type: {type(crew_output)}")
            
            # Extract the result using different approaches
            result = self._extract_crew_result(crew_output)
            
            if result:
                logger.info("Job analysis completed successfully")
                return result
            else:
                # If we couldn't extract a result, return the string representation
                logger.warning("Could not extract structured output, returning string representation")
                return str(crew_output)
            
        except Exception as e:
            logger.error(f"Error during job analysis: {str(e)}", exc_info=True)
            raise CustomizationError(f"Job analysis failed: {str(e)}")
    
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
    
    async def _run_resume_optimization(
        self,
        crew: Crew,
        optimizer_agent: Any,
        resume_text: str,
        job_analysis_result: str,
        customize_level: str
    ) -> str:
        """Run resume optimization task with the crew.
        
        Args:
            crew: The CrewAI crew instance
            optimizer_agent: The resume optimizer agent
            resume_text: The original resume text
            job_analysis_result: The result of job analysis
            customize_level: The level of customization
            
        Returns:
            str: Optimized resume text
        """
        logger.info(f"Running resume optimization with customize level: {customize_level}")
        try:
            # Import the task creation function
            from app.crews.tasks.optimize_resume import create_resume_optimization_task
            
            # Create and add the optimization task
            optimization_task = create_resume_optimization_task(
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
            
            # Extract the result using our helper method
            result = self._extract_crew_result(crew_output)
            
            if result:
                logger.info("Resume optimization completed successfully")
                return result
            else:
                # If we couldn't extract a result, return the string representation
                logger.warning("Could not extract structured output from optimization, returning string representation")
                return str(crew_output)
            
        except Exception as e:
            logger.error(f"Error during resume optimization: {str(e)}", exc_info=True)
            raise CustomizationError(f"Resume optimization failed: {str(e)}")
    
    async def _run_resume_optimization_fallback(
        self,
        crew: Crew,
        optimizer_agent: Any,
        resume_text: str,
        job_description_text: str,
        customize_level: str
    ) -> str:
        """Run resume optimization with a fallback approach that doesn't rely on job analysis.
        
        This method is used when the standard approach fails, typically due to
        formatting issues with the job analysis result.
        
        Args:
            crew: The CrewAI crew instance
            optimizer_agent: The resume optimizer agent
            resume_text: The original resume text
            job_description_text: The original job description text
            customize_level: The level of customization
            
        Returns:
            str: Optimized resume text
        """
        logger.info(f"Running FALLBACK resume optimization with customize level: {customize_level}")
        try:
            # Import the fallback task creation function
            from app.crews.tasks.optimize_resume_fallback import create_resume_optimization_fallback_task
            
            # Create the fallback optimization task
            fallback_task = create_resume_optimization_fallback_task(
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
                return result
            else:
                # If we couldn't extract a result, return the string representation
                logger.warning("Could not extract structured output from fallback optimization, returning string representation")
                return str(crew_output)
            
        except Exception as e:
            logger.error(f"Error during fallback resume optimization: {str(e)}", exc_info=True)
            raise CustomizationError(f"Fallback resume optimization failed: {str(e)}")
    
    async def get_customization_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get customization result by task ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Customization result if available
        """
        logger.debug(f"Getting customization result for task {task_id}")
        
        # Get task metadata
        task = await self.task_service.get_task(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found")
            return None
        
        # Check if task is completed
        if task.get("status") != "completed":
            logger.warning(
                f"Cannot get result for incomplete task {task_id}, "
                f"status: {task.get('status')}"
            )
            return {
                "task_id": task_id,
                "status": task.get("status"),
                "progress": task.get("progress", 0.0),
                "message": task.get("message", "Task not completed")
            }
        
        # Get result content
        result_content = await self.storage_service.get_result(task_id)
        if not result_content:
            logger.warning(f"Result content not found for completed task {task_id}")
            return {
                "task_id": task_id,
                "status": "error",
                "message": "Result content not found"
            }
        
        # Return result with metadata
        return {
            "task_id": task_id,
            "status": "completed",
            "result": result_content,
            "metadata": task
        }


# Factory function is now in dependencies.py
