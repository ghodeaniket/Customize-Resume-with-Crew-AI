"""Service for resume processing and customization."""
import time
from typing import Dict, Optional, Any, BinaryIO, List
from pathlib import Path

from crewai import Crew, Process
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
            
            # Create CrewAI tools
            resume_processor_tool = ResumeProcessorTool(resume_service=self)
            job_matcher_tool = JobMatcherTool()
            
            # Create agents
            analyzer_agent = create_resume_analyzer_agent(
                tools=[resume_processor_tool, job_matcher_tool]
            )
            optimizer_agent = create_resume_optimizer_agent(
                tools=[resume_processor_tool, job_matcher_tool]
            )
            
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
            
            # Create crew
            crew = Crew(
                agents=[analyzer_agent, optimizer_agent],
                tasks=[job_analysis_task],
                verbose=settings.CREW_VERBOSE,
                process=Process.sequential
            )
            
            # Execute job analysis
            job_analysis_result = await self._run_job_analysis(crew)
            
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
            # Handle errors
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
            job_analysis_result = crew.kickoff()[0]
            logger.info("Job analysis completed successfully")
            return job_analysis_result
        except Exception as e:
            logger.error(f"Error during job analysis: {str(e)}", exc_info=True)
            raise CustomizationError(f"Job analysis failed: {str(e)}")
    
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
            optimized_resume = crew.kickoff()[0]
            logger.info("Resume optimization completed successfully")
            return optimized_resume
        except Exception as e:
            logger.error(f"Error during resume optimization: {str(e)}", exc_info=True)
            raise CustomizationError(f"Resume optimization failed: {str(e)}")
    
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
