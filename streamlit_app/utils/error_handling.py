"""Error handling utilities for the Resume Customizer app."""

import streamlit as st
import time
from typing import Dict, Any, List, Optional, Callable
import traceback
import json
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("resume_customizer")

# Error types and user-friendly messages
ERROR_MESSAGES = {
    # API Connection Errors
    "RequestError": "Could not connect to the server. Please check your internet connection and try again.",
    "TimeoutError": "The request timed out. The server might be busy, please try again later.",
    "ConnectionError": "Connection to the server failed. Please check your internet connection and try again.",
    
    # Customization Errors
    "CustomizationRequestError": "There was an error submitting your customization request. Please try again.",
    "CustomizationStatusError": "Could not check the status of your customization request.",
    "CustomizationResultError": "Could not retrieve the customization results. Please try again.",
    
    # Resume Processing Errors
    "ResumeUploadError": "There was an error uploading your resume. Please try again.",
    "ResumeStatusError": "Could not check the status of your resume processing.",
    "ResumeTextError": "Could not retrieve the text from your resume. Please try again.",
    
    # Job Description Errors
    "JobDescriptionValidationError": "The job description could not be validated. Please check the content and try again.",
    
    # Generic Errors
    "FileTypeError": "The file type is not supported. Please upload a PDF, DOCX, or TXT file.",
    "FileSizeError": "The file is too large. Please upload a file smaller than 10MB.",
    "ValidationError": "The submitted data is invalid. Please check your inputs and try again.",
    "UnknownError": "An unexpected error occurred. Please try again or contact support if the issue persists."
}

def get_error_message(error: Exception) -> str:
    """
    Get a user-friendly error message based on the exception type.
    
    Args:
        error: The exception that was raised
        
    Returns:
        str: A user-friendly error message
    """
    # Get the error type name
    error_type = type(error).__name__
    
    # Check if there's a specific message for this error type
    if error_type in ERROR_MESSAGES:
        message = ERROR_MESSAGES[error_type]
    else:
        # Try to find a partial match
        for key in ERROR_MESSAGES:
            if key in error_type:
                message = ERROR_MESSAGES[key]
                break
        else:
            # Use generic message if no match found
            message = ERROR_MESSAGES["UnknownError"]
    
    # Append specific error message if available and not too technical
    if str(error) and not str(error).startswith("Exception"):
        specific_message = str(error)
        
        # Don't include URL, stack traces or other technical details
        if not any(x in specific_message for x in ["http://", "https://", "Traceback", "File \"", "line ", "<", ">"]):
            message += f" Details: {specific_message}"
    
    return message


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Log an error with context and return an error ID.
    
    Args:
        error: The exception that was raised
        context: Additional context information (optional)
        
    Returns:
        str: A unique error ID for reference
    """
    # Generate a unique error ID
    error_id = f"err_{int(time.time())}"
    
    # Get the stack trace
    stack_trace = traceback.format_exc()
    
    # Create a log entry
    log_entry = {
        "error_id": error_id,
        "timestamp": datetime.now().isoformat(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "stack_trace": stack_trace
    }
    
    # Add context if available
    if context:
        log_entry["context"] = context
    
    # Log the error
    logger.error(f"Error {error_id}: {type(error).__name__} - {str(error)}")
    logger.debug(f"Error details: {json.dumps(log_entry, indent=2)}")
    
    return error_id


def handle_api_error(func: Callable) -> Callable:
    """
    Decorator for handling API errors in a standardized way.
    
    Args:
        func: The function to decorate
        
    Returns:
        Callable: The decorated function
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log the error
            error_id = log_error(e, {
                "function": func.__name__,
                "args": str(args),
                "kwargs": str(kwargs)
            })
            
            # Get a user-friendly message
            message = get_error_message(e)
            
            # Add error ID for reference
            message += f" (Reference: {error_id})"
            
            # Re-raise with the user-friendly message
            raise type(e)(message)
    
    return wrapper


def show_error_message(error: Exception, help_text: Optional[str] = None):
    """
    Display a standardized error message to the user.
    
    Args:
        error: The exception that was raised
        help_text: Additional help text to display (optional)
    """
    # Get a user-friendly message
    message = get_error_message(error)
    
    # Display the error message
    st.error(f"Error: {message}")
    
    # Add troubleshooting help if available
    if help_text:
        with st.expander("Troubleshooting"):
            st.markdown(help_text)
    else:
        # Default troubleshooting help
        with st.expander("Troubleshooting"):
            st.markdown("""
            **Try the following:**
            
            - Check your internet connection
            - Refresh the page and try again
            - If you're uploading a file, make sure it's in a supported format (PDF, DOCX, TXT)
            - If the issue persists, try again later or contact support
            """)


def show_retry_options(retry_func: Optional[Callable] = None, back_func: Optional[Callable] = None):
    """
    Display standardized retry options.
    
    Args:
        retry_func: Function to call when retry is clicked (optional)
        back_func: Function to call when back is clicked (optional)
    """
    # Create columns for the buttons
    col1, col2 = st.columns(2)
    
    # Retry button
    if retry_func:
        with col1:
            if st.button("Try Again", key="retry_button", use_container_width=True):
                retry_func()
    
    # Back button
    if back_func:
        with col2:
            if st.button("Go Back", key="back_button", use_container_width=True):
                back_func()
