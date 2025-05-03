"""Service for orchestrating resume processing and customization operations."""
import time
from typing import Dict, Any, Optional

from app.core.logging import logger
from app.core.exceptions import ResumeNotFoundError, CustomizationError
from app.services.document_storage_service import DocumentStorageService
from app.services.resume.core.resume_extractor_service import ResumeExtractorService
from app.services.resume.core.resume_retrieval_service import ResumeRetrievalService
from app.services.resume.core.task_status_service import TaskStatusService


class ResumeOrchestratorService:
    """Orchestrator service that coordinates resume operations."""
    
    def __init__(
        self,
        extractor_service: ResumeExtractorService,
        retrieval_service: ResumeRetrievalService,
        task_status_service: TaskStatusService,
        storage_service: DocumentStorageService
    ):
        """Initialize the orchestrator service.
        
        Args:
            extractor_service: Service for extracting text from resumes
            retrieval_service: Service for retrieving resume data
            task_status_service: Service for managing task status
            storage_service: Document storage service
        """
        self.extractor_service = extractor_service
        self.retrieval_service = retrieval_service
        self.task_status_service = task_status_service
        self.storage_service = storage_service
        logger.info("Initialized ResumeOrchestratorService")
    
    async def process_resume(
        self, file_content: bytes, filename: str, task_id: str
    ) -> Dict[str, Any]:
        """Process a resume file and coordinate all operations.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            task_id: Unique task identifier
            
        Returns:
            Dict[str, Any]: Processing result with metadata
        """
        start_time = time.time()
        
        try:
            # Start task tracking
            await self.task_status_service.mark_task_started(
                task_id, 
                task_type="resume_processing",
                additional_metadata={"filename": filename}
            )
            
            # Extract text and save documents
            extraction_result = await self.extractor_service.extract_resume_text(
                file_content, filename, task_id
            )
            
            # Mark task completed
            await self.task_status_service.mark_task_completed(
                task_id=task_id,
                start_time=start_time,
                result={"text_length": len(extraction_result["text"])}
            )
            
            # Return result
            return {
                "task_id": task_id,
                "filename": filename,
                "text": extraction_result["text"],
                "text_path": extraction_result["text_path"],
                "original_path": extraction_result["original_path"],
                "status": "completed"
            }
            
        except Exception as e:
            # Mark task as failed
            await self.task_status_service.mark_task_failed(
                task_id=task_id,
                error=str(e),
                start_time=start_time,
                error_type="processing_error"
            )
            
            logger.error(f"Resume processing failed for task {task_id}: {str(e)}", exc_info=True)
            raise
    
    async def get_resume_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get resume data by task ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Resume data if available
        """
        return await self.retrieval_service.get_resume_data(task_id)
    
    async def resume_exists(self, task_id: str) -> bool:
        """Check if a resume exists.
        
        Args:
            task_id: Task identifier
            
        Returns:
            bool: True if the resume exists, False otherwise
        """
        return await self.retrieval_service.resume_exists(task_id)
    
    async def get_customization_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get customization result by task ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Customization result if available
        """
        # Get task metadata
        task = await self.task_status_service.get_task_status(task_id)
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
