"""Batch operations endpoints for efficient multi-task handling."""
from typing import Annotated, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_task_service
from app.models.schemas import requests
from app.services.task_service import TaskService
from app.core.logging import logger

router = APIRouter(prefix="/api/batch", tags=["batch"])


@router.post("/tasks/status", response_model=Dict[str, Any])
async def get_batch_task_status(
    request: requests.BatchStatusRequest,
    task_service: Annotated[TaskService, Depends(get_task_service)]
):
    """Get status for multiple tasks in a single request.
    
    This endpoint reduces the number of API calls needed when tracking multiple tasks,
    improving performance for clients monitoring multiple operations.
    
    Args:
        request: Batch status request with task IDs
        task_service: Task service dependency
        
    Returns:
        Dict containing status information for all requested tasks
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        # Fetch all task statuses
        results = {}
        not_found_tasks = []
        
        for task_id in request.task_ids:
            task_data = await task_service.get_task(task_id)
            
            if task_data:
                # Basic status info
                status_info = {
                    "status": task_data.get("status", "unknown"),
                    "progress": task_data.get("progress", 0.0),
                    "task_type": task_data.get("task_type", "unknown"),
                    "created_at": task_data.get("created_at", ""),
                    "updated_at": task_data.get("updated_at", "")
                }
                
                # Add metadata if requested
                if request.include_metadata:
                    status_info["metadata"] = task_data.get("metadata", {})
                    status_info["result_url"] = None
                    
                    if task_data.get("status") == "completed":
                        # Construct result URL based on task type
                        task_type = task_data.get("task_type", "")
                        if task_type == "resume_processing":
                            status_info["result_url"] = f"/api/resumes/{task_id}/text"
                        elif task_type == "resume_customization":
                            status_info["result_url"] = f"/api/resumes/customization/{task_id}/result"
                
                results[task_id] = status_info
            else:
                not_found_tasks.append(task_id)
        
        response = {
            "tasks": results,
            "summary": {
                "total_requested": len(request.task_ids),
                "found": len(results),
                "not_found": len(not_found_tasks)
            }
        }
        
        # Include not found tasks if any
        if not_found_tasks:
            response["not_found_task_ids"] = not_found_tasks
        
        logger.info(
            f"Batch status check completed for {len(request.task_ids)} tasks",
            extra={
                "found_tasks": len(results),
                "not_found_tasks": len(not_found_tasks)
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Batch status check failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve batch task status: {str(e)}"
        )


@router.get("/tasks", response_model=Dict[str, Any])
async def list_tasks(
    request: requests.TaskListRequest = Depends(),
    task_service: Annotated[TaskService, Depends(get_task_service)] = None
):
    """List tasks with pagination and filtering.
    
    This endpoint provides a paginated list of tasks with filtering capabilities,
    making it easy to browse and manage large numbers of tasks.
    
    Args:
        request: Task list request with filters and pagination
        task_service: Task service dependency
        
    Returns:
        Dict containing paginated task list and metadata
    """
    try:
        # Build filter criteria
        filters = {}
        
        if request.task_type:
            filters["task_type"] = request.task_type
        
        if request.filters:
            if request.filters.status:
                filters["status"] = {"$in": request.filters.status}
            
            if request.filters.created_after:
                filters["created_at"] = {"$gte": request.filters.created_after.isoformat()}
            
            if request.filters.created_before:
                filters.setdefault("created_at", {})["$lte"] = request.filters.created_before.isoformat()
        
        # Get total count (simplified - actual implementation would query storage)
        total_items = 100  # Placeholder - actual implementation would count filtered items
        
        # Pagination calculations
        page = request.pagination.page
        page_size = request.pagination.page_size
        offset = (page - 1) * page_size
        
        total_pages = (total_items + page_size - 1) // page_size
        
        # Get paginated results (simplified - actual implementation would query storage)
        tasks = []  # Placeholder - actual implementation would fetch tasks
        
        # Create response
        response = {
            "tasks": tasks,
            "pagination": {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "items_per_page": page_size,
                "has_next": page < total_pages,
                "has_previous": page > 1
            },
            "filters_applied": filters
        }
        
        logger.info(
            f"Task list retrieved: page {page}, size {page_size}",
            extra={
                "total_items": total_items,
                "filters": filters
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Task list retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task list: {str(e)}"
        )
