"""Service for resume processing and customization using repository pattern."""
import time
from typing import Dict, Optional, Any, BinaryIO, List
from pathlib import Path

from fastapi import UploadFile, BackgroundTasks

from app.core.logging import logger
from app.core.config import settings
from app.core.exceptions import DocumentProcessingError, ResumeNotFoundError, CustomizationError
from app.infrastructure.document_processor import DocumentProcessor
from app.repositories.document_repository import DocumentRepository
from app.repositories.task_repository import TaskRepository
from app.crews.flows import ResumeCustomizationFlow
from app.models.domain.states import ResumeCustomizationState, CustomizationLevel


class ResumeServiceRepository:
    """Service for processing and customizing resumes using repository pattern.
    
    This service implements the same functionality as the original ResumeService
    but uses the repository pattern for data access, providing better separation
    of concerns and testability.
    """
    
    def __init__(
        self, 
        document_processor: DocumentProcessor,
        document_repository: DocumentRepository,
        task_repository: TaskRepository
    ):
        """Initialize the resume service.
        
        Args:
            document_processor: Document processor for text extraction
            document_repository: Repository for document data access
            task_repository: Repository for task data access
        """
        self.document_processor = document_processor
        self.document_repository = document_repository
        self.task_repository = task_repository
        logger.info("Initialized ResumeServiceRepository with repositories")
    
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
            file_path = await self.document_repository.save_document(
                file_content, task_id, filename
            )
            
            # Extract text
            extracted_text = await self.document_processor.extract_text_from_bytes(
                file_content, filename=filename
            )
            
            # Save extracted text
            text_path = await self.document_repository.save_extracted_text(
                extracted_text, task_id
            )
            
            # Update metadata with processing results
            metadata = {
                "status": "completed",
                "processing_time_ms": (time.time() - start_time) * 1000,
                "text_length": len(extracted_text)
            }
            await self.document_repository.save_metadata(task_id, metadata)
            
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
            await self.document_repository.save_metadata(task_id, error_metadata)
            
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
        return await self.document_repository.exists(task_id)
    
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
            # Get metadata
            metadata = await self.document_repository.get_metadata(task_id)
            
            # Get extracted text
            extracted_text = await self.document_repository.get_extracted_text(task_id)
            
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
        """Customize a resume based on a job description using CrewAI Flow.
        
        This method uses the new ResumeCustomizationFlow implementation
        instead of the original CrewAI approach, leveraging the structured
        state management and flow control provided by CrewAI Flows.
        
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
            resume_data = await self.get_resume_data(resume_id)
            if not resume_data or "text" not in resume_data:
                raise CustomizationError("Resume text not available")
            
            resume_text = resume_data["text"]
            logger.info(f"Retrieved resume text for customization, length: {len(resume_text)}")
            
            # Update progress
            await self.task_repository.update_task(
                task_id=task_id, 
                status="processing", 
                progress=10.0,
                message="Retrieved resume text"
            )
            
            # Create customization flow with dependencies
            customization_flow = ResumeCustomizationFlow(
                task_id=task_id,
                resume_service=self,
                storage_service=self.document_repository,  # Pass document repository as storage service
                task_service=self.task_repository  # Pass task repository as task service
            )
            
            # Set resume and job description
            customization_flow.set_resume(
                resume_text=resume_text, 
                filename=resume_data.get("metadata", {}).get("original_filename")
            )
            customization_flow.set_job_description(
                job_description_text=job_description,
                filename="job_description.txt"
            )
            
            # Set customization level
            customization_flow.set_customization_level(customize_level)
            
            # Execute the flow
            logger.info(f"Kicking off customization flow for task {task_id}")
            result = customization_flow.kickoff()
            logger.info(f"Customization flow completed for task {task_id}")
            
            # Get the final state
            flow_state = customization_flow.state
            
            # Check for errors
            if flow_state.status.value == "failed":
                raise CustomizationError(flow_state.error_message or "Customization failed")
            
            # Get the optimized resume text
            optimized_resume = flow_state.resume_optimization.optimized_resume
            if not optimized_resume:
                raise CustomizationError("No optimized resume produced")
            
            # Store the result
            await self.document_repository.save_result(task_id, optimized_resume)
            
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
                
                # Update task status to failed
                await self.task_repository.update_task(
                    task_id=task_id,
                    status="failed",
                    progress=100.0,
                    error=str(e),
                    processing_time_ms=(time.time() - start_time) * 1000
                )
                
                raise CustomizationError(error_message)
    
    async def get_customization_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get customization result by task ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Customization result if available
        """
        logger.debug(f"Getting customization result for task {task_id}")
        
        # Get task metadata
        task = await self.task_repository.get_task(task_id)
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
        result_content = await self.document_repository.get_result(task_id)
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


# Factory function for dependency injection
def get_resume_service_repository(
    document_processor: DocumentProcessor,
    document_repository: DocumentRepository,
    task_repository: TaskRepository
) -> ResumeServiceRepository:
    """Get resume service instance.
    
    Args:
        document_processor: Document processor
        document_repository: Document repository for data access
        task_repository: Task repository for data access
        
    Returns:
        ResumeServiceRepository: Resume service instance
    """
    return ResumeServiceRepository(
        document_processor=document_processor,
        document_repository=document_repository,
        task_repository=task_repository
    )
