"""
Customization Status Section component implementation (Phase 4).

This component provides a UI for tracking the status of resume customization,
showing progress indicators, estimated time remaining, and handling different status states.
"""

import streamlit as st
import time
from datetime import datetime, timedelta
import math
import json
from typing import Dict, Any, Optional, Tuple

from services.job_description_service import get_customization_status, get_customization_result


def render_customization_status_section():
    """Render the customization status tracking section."""
    
    st.markdown("### Customization Status")
    
    # Get the task ID from session state
    task_id = st.session_state.job_description_state.get("customization_task_id")
    
    if not task_id:
        st.error("No customization task has been submitted.")
        return
    
    # Create a status container
    status_container = st.container(border=True)
    
    with status_container:
        st.subheader("Resume Customization Progress")
        
        # Status indicator
        status = st.session_state.job_description_state.get("customization_status", "processing")
        
        if status == "processing":
            # Progress bar and percentage
            progress = st.session_state.job_description_state.get("customization_progress", 0)
            st.progress(progress / 100)
            st.markdown(f"**Progress:** {progress:.0f}%")
            
            # Display estimated time remaining
            est_time = display_estimated_time_remaining()
            
            # Processing stages - show more detailed information about the current stage
            display_processing_stage(progress)
            
        elif status == "completed":
            # Show completed status with success message
            st.success("✅ Customization completed successfully!")
            st.progress(1.0)
            
            # Show processing time if available
            if "customization_processing_time" in st.session_state.job_description_state:
                processing_time = st.session_state.job_description_state["customization_processing_time"]
                st.info(f"Processing completed in {processing_time:.1f} seconds")
            
            # Create a button to view results
            if st.button("View Customized Resume", type="primary"):
                st.session_state.job_description_state["customization_view_results"] = True
                retrieve_customization_results(task_id)
                
        elif status == "failed":
            # Show error message and details
            error_message = st.session_state.job_description_state.get("customization_error", "Unknown error")
            st.error(f"❌ Customization failed: {error_message}")
            
            # Show troubleshooting section
            with st.expander("Troubleshooting"):
                st.markdown("""
                **Common issues:**
                - Backend service might be unavailable
                - The resume or job description might have formatting issues
                - Network connectivity problems
                
                **What to try:**
                - Submit the request again
                - Try with a different job description
                - Ensure your internet connection is stable
                """)
            
            # Retry button
            if st.button("Retry Customization"):
                # Reset the status and go back to job description step
                st.session_state.job_description_state["step"] = "input"
                st.session_state.nav_state["current_step"] = 2
                st.rerun()
        else:
            # Unknown status
            st.warning(f"Unknown status: {status}")
    
    # Check status on page load and update every 3 seconds
    auto_refresh = st.empty()
    if auto_refresh.checkbox("Auto-refresh status", value=True):
        st.session_state.job_description_state["auto_refresh"] = True
    else:
        st.session_state.job_description_state["auto_refresh"] = False
        
    # Manual refresh button
    if st.button("Refresh Status"):
        refresh_status(status_container, task_id)
    
    # Auto-refresh if enabled
    if st.session_state.job_description_state.get("auto_refresh", True):
        refresh_status(status_container, task_id)


def refresh_status(status_container, task_id):
    """
    Refresh the status display with latest information from API.
    
    Args:
        status_container: Streamlit container for status display
        task_id: The customization task ID
    """
    try:
        # Check if we should throttle requests (don't check more than once every 2 seconds)
        last_check = st.session_state.job_description_state.get("last_status_check")
        now = datetime.now()
        
        if last_check:
            last_check_time = datetime.fromisoformat(last_check)
            if (now - last_check_time).total_seconds() < 2:
                # Too soon - wait a bit
                time.sleep(2 - (now - last_check_time).total_seconds())
        
        # Make API call to get current status
        response = get_customization_status(task_id)
        
        # Update last check time
        st.session_state.job_description_state["last_status_check"] = now.isoformat()
        
        # Extract status data - use response directly as it doesn't have a 'data' wrapper
        # Update session state with response data
        st.session_state.job_description_state["customization_status"] = response.get("status")
        st.session_state.job_description_state["customization_progress"] = response.get("progress", 0)
        st.session_state.job_description_state["customization_message"] = response.get("message")
        
        # If processing is complete, update state accordingly
        if response.get("status") == "completed":
            st.session_state.job_description_state["customization_processing_time"] = response.get("processing_time_ms", 0) / 1000 if response.get("processing_time_ms") else 0
            
            # When completed, automatically retrieve results
            retrieve_customization_results(task_id)
        
        # If processing failed, capture the error
        if response.get("status") == "failed":
            st.session_state.job_description_state["customization_error"] = response.get("message", "Unknown error")
                
    except Exception as e:
        # Handle API errors
        with status_container:
            st.error(f"Error checking status: {str(e)}")
            st.session_state.job_description_state["customization_error"] = str(e)
            
    # Sleep briefly to avoid overwhelming the API and rerun if auto-refresh is enabled
    if st.session_state.job_description_state.get("auto_refresh", True) and st.session_state.job_description_state.get("customization_status") == "processing":
        time.sleep(2)
        st.rerun()


def retrieve_customization_results(task_id):
    """
    Retrieve the customization results from the API.
    
    Args:
        task_id: The customization task ID
    """
    try:
        # Make API call to get customization results
        with st.spinner("Retrieving customization results..."):
            response = get_customization_result(task_id)
            
            # Update session state with response data - use response directly
            st.session_state.job_description_state["customization_result"] = response
            st.session_state.job_description_state["customization_view_results"] = True
            st.success("Retrieved customization results successfully!")
            
            # Navigation - mark step 3 as completed
            if 3 not in st.session_state.nav_state["steps_completed"]:
                st.session_state.nav_state["steps_completed"].append(3)
                
    except Exception as e:
        # Handle API errors
        st.error(f"Error retrieving customization results: {str(e)}")
        st.session_state.job_description_state["customization_error"] = str(e)


def display_estimated_time_remaining():
    """
    Display the estimated time remaining for the customization process.
    
    Returns:
        float: The estimated time remaining in seconds
    """
    # Get the progress and estimated completion time from session state
    progress = st.session_state.job_description_state.get("customization_progress", 0)
    est_completion = st.session_state.job_description_state.get("estimated_completion_time")
    
    if est_completion and progress > 0:
        # If we have an estimated completion time, calculate time remaining
        try:
            if isinstance(est_completion, str):
                est_completion = datetime.fromisoformat(est_completion)
            
            now = datetime.now()
            remaining_seconds = max(0, (est_completion - now).total_seconds())
            
            # Adjust based on current progress
            if progress < 10:
                # Initial stages - estimated time might need adjustment
                # If very early in the process, don't show time estimate yet
                if progress < 5:
                    st.info("Initializing customization process...")
                    return None
                
                # At early stages, calculate a rough estimate based on progress so far
                elapsed = (now - datetime.fromisoformat(st.session_state.job_description_state["last_status_check"])).total_seconds()
                if elapsed > 0:
                    total_estimated = (elapsed / progress) * 100
                    remaining_seconds = total_estimated * (1 - progress / 100)
            
            # Format the time remaining in a human-readable format
            if remaining_seconds < 60:
                time_str = f"{math.ceil(remaining_seconds)} seconds"
            elif remaining_seconds < 3600:
                time_str = f"{math.ceil(remaining_seconds / 60)} minutes"
            else:
                hours = math.floor(remaining_seconds / 3600)
                minutes = math.ceil((remaining_seconds % 3600) / 60)
                time_str = f"{hours} hour{'s' if hours > 1 else ''}, {minutes} minute{'s' if minutes > 1 else ''}"
            
            # Display the time remaining
            st.info(f"⏱️ Estimated time remaining: {time_str}")
            return remaining_seconds
        except Exception as e:
            # If error in calculation, show a generic message
            st.info("Customization in progress...")
            return None
    else:
        # If we don't have enough information, show a generic message
        st.info("Customization in progress...")
        return None


def display_processing_stage(progress):
    """
    Display the current processing stage based on progress percentage.
    
    Args:
        progress: Current progress percentage (0-100)
    """
    # Define processing stages
    stages = [
        (0, "Initializing customization process..."),
        (10, "Analyzing resume structure..."),
        (25, "Extracting key skills and experience..."),
        (40, "Analyzing job description requirements..."),
        (55, "Matching resume to job requirements..."),
        (70, "Optimizing content and structure..."),
        (85, "Finalizing customized resume..."),
        (95, "Preparing output...")
    ]
    
    # Find the current stage
    current_stage = None
    for threshold, stage_text in stages:
        if progress >= threshold:
            current_stage = stage_text
    
    if current_stage:
        # Create a container with stage information
        stage_container = st.container(border=False)
        stage_container.markdown(f"**Current stage:** {current_stage}")
        
        # Add a pulsing animation CSS for the current stage
        st.markdown(
            """
            <style>
            @keyframes pulse {
                0% { opacity: 0.6; }
                50% { opacity: 1; }
                100% { opacity: 0.6; }
            }
            .pulsing-text {
                animation: pulse 1.5s infinite;
            }
            </style>
            <div class="pulsing-text" style="margin-top: 0.5rem; font-size: 0.9rem; color: #4263eb;">
                Processing...
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Add a small activity indicator to show ongoing processing
        activity_container = st.empty()
        activity_indicator = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
        activity_container.markdown(
            f"<div style='font-size: 1.5rem;'>{activity_indicator[int(time.time()) % len(activity_indicator)]}</div>", 
            unsafe_allow_html=True
        )
