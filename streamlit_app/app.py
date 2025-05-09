"""
Resume Customizer - Streamlit Application
Phase 1, 2 & 3: Resume Upload, Processing, Job Description Parsing, and Customization Options

This application provides a frontend for the Resume Customizer backend service,
allowing users to upload resumes, track processing status, submit job descriptions,
and configure customization options for resume generation.
"""
import streamlit as st
from components.header import render_header
from components.upload_section import render_upload_section
from components.status_section import render_status_section
from components.job_description_section import render_job_description_section
from components.customization_options import render_customization_options
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
    
    # Get current step from navigation state
    current_step = st.session_state.nav_state["current_step"]
    
    # Step indicator
    st.markdown(
        f"""
        <div class="step-indicator">
            <div class="step {"active" if current_step == 1 else "completed" if 1 in st.session_state.nav_state["steps_completed"] else ""}">1. Upload Resume</div>
            <div class="step {"active" if current_step == 2 else "completed" if 2 in st.session_state.nav_state["steps_completed"] else ""}">2. Job Description</div>
            <div class="step {"active" if current_step == 3 else "completed" if 3 in st.session_state.nav_state["steps_completed"] else ""}">3. Results</div>
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
                if st.button("Continue to Job Description", type="primary"):
                    st.session_state.nav_state["current_step"] = 2
                    st.rerun()
    
    elif current_step == 2:
        # Render the job description section
        render_job_description_section()
        
        # Check if job description is processed and ready for customization
        if (st.session_state.job_description_state["processed_text"] and 
            st.session_state.job_description_state["is_valid"]):
            # Render the customization options section
            render_customization_options()
            
            # If customization task is submitted, mark step 2 as completed
            if st.session_state.job_description_state.get("customization_task_id"):
                if 2 not in st.session_state.nav_state["steps_completed"]:
                    st.session_state.nav_state["steps_completed"].append(2)
                st.session_state.nav_state["can_proceed"] = True
                
                # Auto-proceed to step 3 if a customization task exists
                if st.session_state.job_description_state["customization_status"] == "processing":
                    st.session_state.nav_state["current_step"] = 3
                    st.rerun()
        
        # Button to go back to resume upload if needed
        if st.button("← Back to Resume Upload"):
            st.session_state.nav_state["current_step"] = 1
            st.rerun()
    
    elif current_step == 3:
        # Placeholder for results section (Phase 4)
        st.markdown("## Step 3: Results")
        st.info("The results section will be implemented in the next phase.")
        
        # Display the customization task status if available
        if st.session_state.job_description_state.get("customization_task_id"):
            task_id = st.session_state.job_description_state["customization_task_id"]
            status = st.session_state.job_description_state["customization_status"]
            progress = st.session_state.job_description_state["customization_progress"]
            
            st.markdown(
                f"""
                <div class="status-card">
                    <h3>Customization Status</h3>
                    <p>Task ID: {task_id}</p>
                    <p>Status: {status.capitalize()}</p>
                    <p>Progress: {progress}%</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        # Button to go back to job description if needed
        if st.button("← Back to Job Description"):
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
    
    .step.completed {
        background-color: #a5b4fc;
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
    </style>
    """, 
    unsafe_allow_html=True
)

if __name__ == "__main__":
    main()
