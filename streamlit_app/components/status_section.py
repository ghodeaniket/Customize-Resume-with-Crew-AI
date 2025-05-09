"""Status tracking component for resume processing."""
import streamlit as st
import time
from services.api_service import get_resume_status, get_resume_text

def render_status_section():
    """Render the resume processing status section."""
    
    st.markdown("### Resume Processing Status")
    
    # Create a status card
    st.markdown(
        """
        <div class="status-card">
        <h4>Status: Processing your resume...</h4>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Get the task ID from session state
    task_id = st.session_state.upload_state["task_id"]
    filename = st.session_state.upload_state["filename"]
    
    if task_id:
        # Show task details
        status_container = st.container()
        
        # Check status on page load and update every 2 seconds
        auto_refresh = st.empty()
        if auto_refresh.checkbox("Auto-refresh status", value=True):
            st.session_state.upload_state["auto_refresh"] = True
        else:
            st.session_state.upload_state["auto_refresh"] = False
            
        # Manual refresh button
        if st.button("Refresh Status"):
            refresh_status(status_container, task_id)
        
        # Auto-refresh if enabled
        if st.session_state.upload_state["auto_refresh"]:
            refresh_status(status_container, task_id)
            
        # If status is "completed", show the extracted text button
        if st.session_state.upload_state["status"] == "completed":
            if st.button("View Extracted Text"):
                with st.spinner("Retrieving extracted text..."):
                    try:
                        # Get the extracted text
                        text_response = get_resume_text(task_id)
                        
                        # Store the text in session state
                        st.session_state.upload_state["extracted_text"] = text_response.get("text", "")
                        
                        # Show success message and the text
                        st.success("Text extracted successfully!")
                        
                    except Exception as e:
                        st.error(f"Error retrieving text: {str(e)}")
            
            # Display the extracted text if available
            if st.session_state.upload_state.get("extracted_text"):
                with st.expander("Extracted Text", expanded=True):
                    st.text_area(
                        "Resume Content", 
                        st.session_state.upload_state["extracted_text"],
                        height=300,
                        disabled=True
                    )
                    
                # Show continue button
                if st.button("Continue to Job Description", type="primary"):
                    # This will be implemented in Phase 2
                    st.info("Job Description input will be available in the next phase")
                    
                # Show reset button
                if st.button("Upload Another Resume"):
                    # Reset the session state
                    st.session_state.upload_state = {
                        "task_id": None,
                        "filename": None,
                        "status": None,
                        "progress": 0,
                        "is_processing": False,
                        "error": None,
                        "current_file": None,
                        "extracted_text": None,
                        "auto_refresh": True,
                    }
                    st.rerun()


def refresh_status(status_container, task_id):
    """Refresh the status display with latest information from API."""
    
    try:
        # Make API call to get current status
        response = get_resume_status(task_id)
        
        # Update session state with response data
        st.session_state.upload_state["status"] = response.get("status")
        st.session_state.upload_state["progress"] = response.get("progress", 0)
        
        # Display status info
        with status_container:
            status = st.session_state.upload_state["status"]
            progress = st.session_state.upload_state["progress"]
            
            # Show appropriate status message and progress
            if status == "processing":
                st.info(f"Processing: {progress:.0f}% complete")
                st.progress(progress / 100)
            elif status == "completed":
                st.success("Processing completed successfully!")
                st.progress(1.0)
            elif status == "failed":
                st.error(f"Processing failed: {response.get('message', 'Unknown error')}")
            else:
                st.warning(f"Unknown status: {status}")
                
    except Exception as e:
        # Handle API errors
        with status_container:
            st.error(f"Error checking status: {str(e)}")
            
    # Sleep briefly to avoid overwhelming the API
    if st.session_state.upload_state["auto_refresh"] and st.session_state.upload_state["status"] == "processing":
        time.sleep(2)
        st.rerun()
