"""
Resume Customizer - Streamlit Application
Phase 1: Resume Upload & Processing

This application provides a frontend for the Resume Customizer backend service,
allowing users to upload resumes and track their processing status.
"""
import streamlit as st
from components.header import render_header
from components.upload_section import render_upload_section
from components.status_section import render_status_section
from utils.session_state import initialize_session_state

# Configure page settings
st.set_page_config(
    page_title="Resume Customizer",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state variables
initialize_session_state()

# Render application components
def main():
    """Render the main application components."""
    
    # Render the header
    render_header()
    
    # Step indicator
    st.markdown(
        """
        <div class="step-indicator">
            <div class="step active">1. Upload Resume</div>
            <div class="step">2. Job Description</div>
            <div class="step">3. Results</div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Render the resume upload section
    render_upload_section()
    
    # Show status section if resume has been uploaded
    if st.session_state.upload_state["task_id"]:
        render_status_section()

# Apply custom styling with CSS
st.markdown(
    """
    <style>
    .upload-header {
        font-size: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    .step-indicator {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    
    .step {
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        color: #6c757d;
    }
    
    .step.active {
        background-color: #4263eb;
        color: white;
        font-weight: bold;
    }
    
    .status-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-top: 1.5rem;
        border-left: 4px solid #4263eb;
    }
    
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #f5c6cb;
    }
    
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #c3e6cb;
    }
    
    .info-box {
        background-color: #e7f5ff;
        color: #0c326f;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #74c0fc;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

if __name__ == "__main__":
    main()
