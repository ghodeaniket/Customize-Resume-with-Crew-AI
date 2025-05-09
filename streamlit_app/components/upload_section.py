"""Resume upload section component."""
import streamlit as st
import os
from utils.file_validation import validate_file_type, validate_file_size
from services.api_service import upload_resume
from utils.resume_models import ResumeUploadError

def render_upload_section():
    """Render the resume upload section of the application."""
    
    st.markdown("### Step 1: Upload Your Resume")
    
    # File upload widget
    uploaded_file = st.file_uploader(
        "Upload your resume (PDF, DOCX, or TXT)",
        type=["pdf", "docx", "txt"],
        help="Maximum file size: 10MB"
    )
    
    # Show tips
    with st.expander("Tips for best results"):
        st.markdown(
            """
            - Ensure your resume is a PDF, DOCX, or TXT file
            - Make sure the file is not password-protected
            - Include your skills, work experience, and education
            - For best results, use a clean, standard format
            """
        )
    
    # If file was uploaded, validate and process it
    if uploaded_file is not None:
        file_name = uploaded_file.name
        file_size = uploaded_file.size
        file_content = uploaded_file.getvalue()
        
        st.session_state.upload_state["current_file"] = file_name
        
        # Validate file type
        is_valid_type, type_message = validate_file_type(file_name)
        if not is_valid_type:
            st.error(f"Invalid file type: {type_message}")
            return
            
        # Validate file size
        is_valid_size, size_message = validate_file_size(file_size)
        if not is_valid_size:
            st.error(f"Invalid file size: {size_message}")
            return
        
        # Show file details
        st.markdown(
            f"""
            <div class="info-box">
            📄 <b>File:</b> {file_name}<br>
            📏 <b>Size:</b> {format_size(file_size)}
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Only show process button if not already processing
        if not st.session_state.upload_state["is_processing"]:
            if st.button("Process Resume", type="primary", key="process_resume_button"):
                # Set processing state
                st.session_state.upload_state["is_processing"] = True
                
                with st.spinner("Uploading resume..."):
                    try:
                        # Upload the resume to the backend
                        response = upload_resume(uploaded_file)
                        
                        # Save the task ID for status tracking
                        st.session_state.upload_state["task_id"] = response.get("task_id")
                        st.session_state.upload_state["filename"] = response.get("filename")
                        st.session_state.upload_state["status"] = response.get("status")
                        
                        # Show success message
                        st.success(f"Resume uploaded successfully: {file_name}")
                        
                    except ResumeUploadError as e:
                        # Show error message
                        st.error(f"Error uploading resume: {str(e)}")
                        st.session_state.upload_state["error"] = str(e)
                    finally:
                        # Clear processing state
                        st.session_state.upload_state["is_processing"] = False
                
                # Force a rerun to update the UI
                st.rerun()
        
        # Show processing spinner if still processing
        if st.session_state.upload_state["is_processing"]:
            st.spinner("Processing resume...")


def format_size(size_bytes):
    """Format file size in bytes to a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
