"""API service for job description customization."""
import httpx
import streamlit as st
import json
import time
from typing import Dict, Any, Optional

from utils.job_models import (
    CustomizationRequest,
    CustomizationResponse,
    CustomizationStatusResponse,
    CustomizationResultResponse,
    CustomizationRequestError,
    CustomizationStatusError,
    CustomizationResultError
)

# Import the helper function from api_service
from services.api_service import get_api_url, with_retry

# Default timeout for API requests
DEFAULT_TIMEOUT = 30.0  # seconds


def submit_customization(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Submit a customization request to the API.
    
    Args:
        request: The customization request data as a dictionary
        
    Returns:
        dict: The API response data
        
    Raises:
        CustomizationRequestError: If the request fails
    """
    url = get_api_url("resumes/customize")
    
    try:
        # Use the request data directly
        request_data = request
        
        # For debugging - add info about the request payload
        with st.expander("Debug Information", expanded=False):
            st.write("Request URL:", url)
            st.write("Request Payload:", request_data)
        
        # Make the request with httpx
        timeout = st.session_state.api_config.get("timeout", DEFAULT_TIMEOUT)
        
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                url, 
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
        
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
                
            raise CustomizationRequestError(f"Customization request failed: {error_detail}")
            
    except httpx.TimeoutException:
        raise CustomizationRequestError("Request timed out. The server took too long to respond.")
    
    except httpx.RequestError as e:
        raise CustomizationRequestError(f"Network error: {str(e)}")
    
    except Exception as e:
        raise CustomizationRequestError(f"Unexpected error: {str(e)}")


def get_customization_status(task_id: str) -> Dict[str, Any]:
    """
    Get the status of a customization task.
    
    Args:
        task_id: The ID of the customization task
        
    Returns:
        dict: The task status response
        
    Raises:
        CustomizationStatusError: If the status check fails
    """
    url = get_api_url(f"resumes/customization/{task_id}")
    
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
                
            raise CustomizationStatusError(f"Status check failed: {error_detail}")
            
    except httpx.TimeoutException:
        raise CustomizationStatusError("Request timed out. The server took too long to respond.")
    
    except httpx.RequestError as e:
        raise CustomizationStatusError(f"Network error: {str(e)}")
    
    except Exception as e:
        raise CustomizationStatusError(f"Unexpected error: {str(e)}")


def get_customization_result(task_id: str) -> Dict[str, Any]:
    """
    Get the result of a completed customization task.
    
    Args:
        task_id: The ID of the customization task
        
    Returns:
        dict: The customization result response
        
    Raises:
        CustomizationResultError: If retrieving the result fails
    """
    url = get_api_url(f"resumes/customization/{task_id}/result")
    
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
                
            raise CustomizationResultError(f"Result retrieval failed: {error_detail}")
            
    except httpx.TimeoutException:
        raise CustomizationResultError("Request timed out. The server took too long to respond.")
    
    except httpx.RequestError as e:
        raise CustomizationResultError(f"Network error: {str(e)}")
    
    except Exception as e:
        raise CustomizationResultError(f"Unexpected error: {str(e)}")
