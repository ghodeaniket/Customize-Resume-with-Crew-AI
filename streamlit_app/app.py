"""
Resume Customizer - Streamlit Application
Phase 1-4: Resume Upload, Processing, Job Description Parsing, Customization Options, and Status Tracking

This application provides a frontend for the Resume Customizer backend service,
allowing users to upload resumes, track processing status, submit job descriptions,
configure customization options, and view customized results.
"""
import streamlit as st
from components.header import render_header
from components.upload_section import render_upload_section
from components.status_section import render_status_section
from components.job_description_section import render_job_description_section
from components.customization_options import render_customization_options
from components.customization_request_section import render_customization_request_section
from components.customization_status_section import render_customization_status_section
from components.results_section import render_results_section
from utils.session_state import initialize_session_state
from utils.error_handling import show_error_message

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
    
    # Get current step from navigation state
    current_step = st.session_state.nav_state["current_step"]
    
    # Step indicator
    st.markdown(
        f"""
        <div class="step-indicator">
            <div class="step-item {"active" if current_step == 1 else "completed" if 1 in st.session_state.nav_state["steps_completed"] else ""}">
                <div class="step-number">1</div>
                <div class="step-text">Upload Resume</div>
            </div>
            <div class="step-connector {"completed" if 1 in st.session_state.nav_state["steps_completed"] else ""}"></div>
            <div class="step-item {"active" if current_step == 2 else "completed" if 2 in st.session_state.nav_state["steps_completed"] else ""}">
                <div class="step-number">2</div>
                <div class="step-text">Job Description</div>
            </div>
            <div class="step-connector {"completed" if 2 in st.session_state.nav_state["steps_completed"] else ""}"></div>
            <div class="step-item {"active" if current_step == 3 else "completed" if 3 in st.session_state.nav_state["steps_completed"] else ""}">
                <div class="step-number">3</div>
                <div class="step-text">Results</div>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Show appropriate section based on navigation state
    if current_step == 1:
        # Render the resume upload section
        render_upload_section()
        
        # Show status section if resume has been uploaded
        if st.session_state.upload_state["task_id"]:
            render_status_section()
            
            # Check if resume is processed and ready for next step
            if st.session_state.upload_state["status"] == "completed":
                st.session_state.nav_state["can_proceed"] = True
                if 1 not in st.session_state.nav_state["steps_completed"]:
                    st.session_state.nav_state["steps_completed"].append(1)
                
                # Button to proceed to job description step
                if st.button("Continue to Job Description", type="primary", key="proceed_to_job_description_btn"):
                    st.session_state.nav_state["current_step"] = 2
                    st.rerun()
    
    elif current_step == 2:
        # Render the job description section
        render_job_description_section()
        
        # Check if job description is processed and ready for customization
        if (st.session_state.job_description_state["processed_text"] and 
            st.session_state.job_description_state["is_valid"]):
            
            # Check if we're at the submission step or still configuring
            if st.session_state.job_description_state.get("step") == "complete":
                # If the customization has been submitted, proceed to step 3
                st.session_state.nav_state["current_step"] = 3
                st.rerun()
            else:
                # Render the customization options section
                render_customization_options()
                
                # If the "Customize My Resume" button is clicked in customization_options.py,
                # it will directly handle submission and update the step
        
        # Button to go back to resume upload if needed
        if st.button("← Back to Resume Upload", key="back_to_upload_btn"):
            st.session_state.nav_state["current_step"] = 1
            st.rerun()
    
    elif current_step == 3:
        # Phase 4: Results and Status Tracking
        
        # Check if customization is complete and results should be shown
        if (st.session_state.job_description_state.get("customization_status") == "completed" and 
            st.session_state.job_description_state.get("customization_view_results", False)):
            # Show the results section
            render_results_section()
        else:
            # Show the customization status section for tracking progress
            render_customization_status_section()
        
        # Button to go back to job description if needed (only if not viewing results)
        if not st.session_state.job_description_state.get("customization_view_results", False):
            if st.button("← Back to Job Description", key="back_to_job_desc_btn"):
                st.session_state.nav_state["current_step"] = 2
                st.rerun()

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
        justify-content: center;
        align-items: center;
        margin-bottom: 2rem;
        padding: 1rem;
        position: relative;
    }
    
    .step-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
        z-index: 1;
        width: 120px;
    }
    
    .step-number {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background-color: #e2e8f0;
        color: #6c757d;
        display: flex;
        justify-content: center;
        align-items: center;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .step-text {
        font-size: 0.875rem;
        color: #6c757d;
        text-align: center;
    }
    
    .step-connector {
        height: 3px;
        flex-grow: 1;
        background-color: #e2e8f0;
        margin: 0 0.5rem;
        width: 80px;
        margin-top: -45px;
    }
    
    .step-item.active .step-number {
        background-color: #4263eb;
        color: white;
    }
    
    .step-item.active .step-text {
        color: #4263eb;
        font-weight: bold;
    }
    
    .step-item.completed .step-number {
        background-color: #a5b4fc;
        color: white;
    }
    
    .step-item.completed .step-text {
        color: #4263eb;
    }
    
    .step-connector.completed {
        background-color: #a5b4fc;
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
    
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #ffeeba;
    }
    
    /* Customization options styling */
    .preset-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 3px solid #4263eb;
        transition: all 0.3s ease;
    }
    
    .preset-card:hover {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    .preference-toggle {
        margin: 0.5rem 0;
    }
    
    .summary-section {
        background-color: #f1f5f9;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
    
    .industry-tag {
        background-color: #e2e8f0;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        display: inline-block;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .keyword-tag {
        background-color: #dbeafe;
        color: #1e40af;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        display: inline-block;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* Phase 4 styling additions */
    .progress-container {
        position: relative;
        margin: 1.5rem 0;
    }
    
    .progress-label {
        position: absolute;
        top: -1.25rem;
        right: 0;
        font-size: 0.875rem;
        color: #4b5563;
    }
    
    .progress-info {
        display: flex;
        justify-content: space-between;
        margin-top: 0.5rem;
        font-size: 0.875rem;
        color: #4b5563;
    }
    
    .result-section {
        margin: 1.5rem 0;
    }
    
    .diff-container {
        background-color: #f8fafc;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        overflow-x: auto;
        font-family: monospace;
        font-size: 0.875rem;
        line-height: 1.5;
    }
    
    .diff-added {
        background-color: #d4edda;
    }
    
    .diff-removed {
        background-color: #f8d7da;
    }
    
    .diff-unchanged {
        color: #6c757d;
    }
    
    .result-action-button {
        margin-top: 1rem;
    }
    
    .result-section-title {
        margin: 1.5rem 0 1rem 0;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 0.5rem;
    }
    
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
    
    .pulsing-text {
        animation: pulse 1.5s infinite;
    }
    
    .comparison-view {
        display: flex;
        flex-direction: column;
    }
    
    @media (min-width: 768px) {
        .comparison-view {
            flex-direction: row;
        }
    }
    
    .download-options {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

if __name__ == "__main__":
    main()
