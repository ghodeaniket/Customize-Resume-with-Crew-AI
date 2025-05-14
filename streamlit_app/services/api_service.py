"""API service for interacting with the Resume Customizer backend."""
import httpx
import streamlit as st
import time
from typing import Dict, Any, Optional
import json

from utils.resume_models import (
    ResumeUploadResponse, 
    TaskStatusResponse, 
    ResumeTextResponse,
    ResumeUploadError,
    ResumeStatusError,
    ResumeTextError
)

# Default timeout for API requests
DEFAULT_TIMEOUT = 30.0  # seconds

# Default retry configuration
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_BACKOFF = 1.0  # seconds


def get_api_url(path: str) -> str:
    """Get the full API URL for a given path.
    
    Args:
        path: The API path (without leading slash)
        
    Returns:
        str: The full API URL
    """
    base_url = st.session_state.api_config["base_url"]
    # Updated to include the v1 version in the API path
    return f"{base_url}/api/v1/{path}"


def upload_resume(file) -> Dict[str, Any]:
    """Upload a resume file to the backend.
    
    Args:
        file: The uploaded file from st.file_uploader
        
    Returns:
        dict: The response from the API as a dictionary
        
    Raises:
        ResumeUploadError: If the upload fails
    """
    url = get_api_url("resumes/upload")
    
    # Create a MultipartEncoder instance
    files = {"resume": (file.name, file.getvalue(), file.type)}
    
    try:
        # Make the request with httpx
        timeout = st.session_state.api_config.get("timeout", DEFAULT_TIMEOUT)
        
        # For debugging - add a debug expander
        with st.expander("Debug Information", expanded=False):
            st.write(f"Attempting upload to: {url}")
        
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, files=files)
        
        # Check for successful response
        if response.status_code == 200:
            return response.json()
        else:
            # Try to get error details
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", "Unknown error")
            except:
                error_detail = response.text or f"HTTP Error: {response.status_code}"
                
            raise ResumeUploadError(f"Upload failed: {error_detail}")
            
    except httpx.TimeoutException:
        raise ResumeUploadError("Request timed out. The server took too long to respond.")
    
    except httpx.RequestError as e:
        raise ResumeUploadError(f"Network error: {str(e)}")
    
    except Exception as e:
        raise ResumeUploadError(f"Unexpected error: {str(e)}")


def get_resume_status(task_id: str) -> Dict[str, Any]:
    """Get the status of a resume processing task.
    
    Args:
        task_id: The ID of the task to check
        
    Returns:
        dict: The task status response
        
    Raises:
        ResumeStatusError: If the status check fails
    """
    url = get_api_url(f"resumes/{task_id}")
    
    try:
        # Make the request with httpx
        timeout = st.session_state.api_config.get("timeout", DEFAULT_TIMEOUT)
        
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url)
        
        # Check for successful response
        if response.status_code == 200:
            return response.json()
        else:
            # Try to get error details
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", "Unknown error")
            except:
                error_detail = response.text or f"HTTP Error: {response.status_code}"
                
            raise ResumeStatusError(f"Status check failed: {error_detail}")
            
    except httpx.TimeoutException:
        raise ResumeStatusError("Request timed out. The server took too long to respond.")
    
    except httpx.RequestError as e:
        raise ResumeStatusError(f"Network error: {str(e)}")
    
    except Exception as e:
        raise ResumeStatusError(f"Unexpected error: {str(e)}")


def get_resume_text(task_id: str) -> Dict[str, Any]:
    """Get the extracted text from a processed resume.
    
    Args:
        task_id: The ID of the task
        
    Returns:
        dict: The extracted text response
        
    Raises:
        ResumeTextError: If retrieving the text fails
    """
    url = get_api_url(f"resumes/{task_id}/text")
    
    try:
        # Make the request with httpx
        timeout = st.session_state.api_config.get("timeout", DEFAULT_TIMEOUT)
        
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url)
        
        # Check for successful response
        if response.status_code == 200:
            return response.json()
        else:
            # Try to get error details
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", "Unknown error")
            except:
                error_detail = response.text or f"HTTP Error: {response.status_code}"
                
            raise ResumeTextError(f"Text retrieval failed: {error_detail}")
            
    except httpx.TimeoutException:
        raise ResumeTextError("Request timed out. The server took too long to respond.")
    
    except httpx.RequestError as e:
        raise ResumeTextError(f"Network error: {str(e)}")
    
    except Exception as e:
        raise ResumeTextError(f"Unexpected error: {str(e)}")


def with_retry(func, *args, retry_count=None, backoff=None, **kwargs):
    """Execute a function with retry logic.
    
    Args:
        func: The function to execute
        *args: Positional arguments to pass to the function
        retry_count: Number of retry attempts (default: from session state or DEFAULT_RETRY_COUNT)
        backoff: Backoff factor for exponential backoff (default: DEFAULT_RETRY_BACKOFF)
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        The result of the function
        
    Raises:
        Exception: The last exception encountered after all retries
    """
    if retry_count is None:
        retry_count = st.session_state.api_config.get("retry_count", DEFAULT_RETRY_COUNT)
        
    if backoff is None:
        backoff = DEFAULT_RETRY_BACKOFF
    
    last_exception = None
    
    for attempt in range(retry_count + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if attempt < retry_count:
                # Wait before retrying with exponential backoff
                sleep_time = backoff * (2 ** attempt)
                time.sleep(sleep_time)
            else:
                # Reraise the last exception after all retries
                raise
