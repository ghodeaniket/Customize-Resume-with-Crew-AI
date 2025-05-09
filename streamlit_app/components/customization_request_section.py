"""
Customization Request Section component implementation (Phase 4).

This component provides a UI for submitting customization requests,
showing a summary of selected options, and handling form validation.
"""

import streamlit as st
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from services.job_description_service import submit_customization

def render_customization_request_section():
    """Render the customization request submission form and validation."""
    
    st.markdown("### Customization Request Summary")
    
    # Get the necessary state variables
    cust_state = st.session_state.customization_state
    job_state = st.session_state.job_description_state
    upload_state = st.session_state.upload_state
    
    # Validate we have everything we need
    if not upload_state["task_id"]:
        st.error("No resume has been uploaded. Please upload a resume first.")
        return False
    
    if not job_state["processed_text"]:
        st.error("No job description has been processed. Please enter and process a job description.")
        return False
    
    # Create a container for the summary with border
    summary_container = st.container(border=True)
    
    with summary_container:
        # Show active preset if any
        if cust_state["active_preset"]:
            st.success(f"Using preset: {cust_state['active_preset']}")
        
        # Create two columns for the summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Basic Settings")
            st.markdown(f"**Customization Level:** {cust_state['customization_level'].capitalize()}")
            
            industry_text = cust_state["industry"] or "Not specified"
            st.markdown(f"**Industry:** {industry_text}")
            
            if cust_state["subindustry"]:
                st.markdown(f"**Specialty:** {cust_state['subindustry']}")
            
            if cust_state["keywords_to_include"]:
                st.markdown("**Additional Keywords:**")
                for keyword in cust_state["keywords_to_include"]:
                    st.markdown(f"- {keyword}")
        
        with col2:
            st.markdown("#### Preferences")
            active_preferences = [
                option["label"] 
                for key, option in get_standard_preference_options().items() 
                if cust_state["preferences"].get(key, False)
            ]
            
            if active_preferences:
                for pref in active_preferences:
                    st.markdown(f"- {pref}")
            else:
                st.markdown("No special preferences selected")
            
            if cust_state["custom_instructions"]:
                st.markdown("#### Custom Instructions")
                st.markdown(f"*{cust_state['custom_instructions']}*")
    
    # Pre-submission validation
    validation_issues = validate_customization_request()
    
    if validation_issues:
        st.warning("Please address the following issues before submitting:")
        for issue in validation_issues:
            st.markdown(f"- {issue}")
        return False
    
    # Display job description preview in an expander
    with st.expander("Review Job Description", expanded=False):
        st.markdown("#### Job Description for Customization")
        st.text_area("Job Description", job_state["processed_text"], height=200, disabled=True)
    
    # Submit button with confirmation
    st.markdown("### Ready to Submit")
    st.info("Your customization request is ready to be submitted. Click the button below to start the customization process.")
    
    submit_col1, submit_col2 = st.columns([3, 1])
    with submit_col1:
        submit_button = st.button(
            "Customize My Resume", 
            key="customization_submit_btn", 
            type="primary",
            use_container_width=True
        )
    
    with submit_col2:
        back_button = st.button(
            "Back to Options",
            key="back_to_options_btn",
            use_container_width=True
        )
    
    if back_button:
        # Reset the step to go back to customization options
        job_state["step"] = "input"
        st.rerun()
    
    if submit_button:
        return submit_customization_request()
    
    return False

def validate_customization_request() -> List[str]:
    """
    Validate the customization request and return a list of issues.
    
    Returns:
        List[str]: List of validation issues, empty if no issues.
    """
    issues = []
    
    # Get the necessary state variables
    cust_state = st.session_state.customization_state
    job_state = st.session_state.job_description_state
    upload_state = st.session_state.upload_state
    
    # Check for required fields
    if not upload_state["task_id"]:
        issues.append("No resume has been uploaded")
    
    if not job_state["processed_text"]:
        issues.append("No job description has been processed")
    
    # Check for other potential issues
    if len(job_state["processed_text"]) < 50:
        issues.append("Job description is too short (minimum 50 characters)")
    
    if cust_state["customization_level"] == "comprehensive" and len(job_state["processed_text"]) < 100:
        issues.append("Comprehensive customization requires a more detailed job description")
    
    # Return the list of issues
    return issues

def submit_customization_request() -> bool:
    """
    Submit the customization request to the API.
    
    Returns:
        bool: True if submission was successful, False otherwise.
    """
    # Get the necessary state variables
    cust_state = st.session_state.customization_state
    job_state = st.session_state.job_description_state
    upload_state = st.session_state.upload_state
    
    # Show a spinner while submitting
    with st.spinner("Submitting customization request..."):
        try:
            # Set submitting state
            cust_state["is_submitting"] = True
            
            # Prepare the keywords list
            keywords = []
            
            # Add keywords from job description if available
            if isinstance(job_state["keywords"], dict):
                # Original dictionary structure
                if job_state["keywords"].get("technical_skills"):
                    keywords.extend(job_state["keywords"]["technical_skills"][:10])
                
                if job_state["keywords"].get("soft_skills"):
                    keywords.extend(job_state["keywords"]["soft_skills"][:5])
            elif isinstance(job_state["keywords"], list):
                # Modified list structure
                keywords.extend(job_state["keywords"][:15])
            
            # Add custom keywords
            if cust_state["keywords_to_include"]:
                keywords.extend(cust_state["keywords_to_include"])
            
            # Create the industry string
            industry = cust_state["industry"]
            if industry and cust_state["subindustry"]:
                industry = f"{industry} - {cust_state['subindustry']}"
            
            # Create additional instructions combining preferences and custom instructions
            additional_instructions = []
            
            # Add active preferences as instructions
            active_prefs = [
                option["label"]
                for key, option in get_standard_preference_options().items() 
                if cust_state["preferences"].get(key, False)
            ]
            
            if active_prefs:
                additional_instructions.append("Preferences: " + ", ".join(active_prefs))
            
            # Add custom instructions
            if cust_state["custom_instructions"]:
                additional_instructions.append(cust_state["custom_instructions"])
            
            # Add keywords to exclude
            if cust_state["keywords_to_exclude"]:
                additional_instructions.append(
                    "De-emphasize or exclude these terms: " + 
                    ", ".join(cust_state["keywords_to_exclude"])
                )
            
            # Join all instructions
            custom_instructions = "\n".join(additional_instructions) if additional_instructions else None
            
            # Create the request dictionary directly
            request_dict = {
                "resume_id": upload_state["task_id"],
                "job_description": job_state["processed_text"],
                "customize_level": cust_state["customization_level"]
            }
            
            # Add industry if available
            if industry:
                request_dict["industry"] = industry
                
            # Add keywords if available
            if keywords:
                request_dict["keywords"] = keywords
            
            # Add custom instructions if available
            if custom_instructions:
                request_dict["custom_instructions"] = custom_instructions
            
            # Submit the request
            response = submit_customization(request_dict)
            
            # Update job description state with the response - use response directly
            job_state["customization_task_id"] = response.get("task_id")
            job_state["customization_status"] = response.get("status", "processing")
            job_state["customization_progress"] = 0
            job_state["last_status_check"] = datetime.now().isoformat()
            job_state["step"] = "complete"
            
            # Estimate completion time (in seconds) - default to 2 minutes if not provided
            est_time = response.get("estimated_completion_time", 120)
            if est_time is not None:
                job_state["estimated_completion_time"] = datetime.now() + timedelta(seconds=est_time)
            
            # Update navigation state to proceed to the next step
            st.session_state.nav_state["current_step"] = 3
            st.session_state.nav_state["can_proceed"] = True
            if 2 not in st.session_state.nav_state["steps_completed"]:
                st.session_state.nav_state["steps_completed"].append(2)
            
            # Show success message
            st.success("Customization request submitted successfully! Proceeding to results.")
            
            # Return success
            return True
            
        except Exception as e:
            cust_state["error"] = f"Error submitting customization request: {str(e)}"
            st.error(cust_state["error"])
            # Add guidance for the user
            st.markdown("**Troubleshooting:**")
            st.markdown(
                """
                - Check your internet connection
                - Ensure the backend service is running
                - Try with a different job description or resume
                """
            )
            # Add a retry button
            if st.button("Retry Submission"):
                return submit_customization_request()
            
            return False
        finally:
            # Reset submitting state
            cust_state["is_submitting"] = False

def get_standard_preference_options() -> Dict[str, Dict[str, Any]]:
    """Get the standard preference options."""
    return {
        "emphasize_leadership": {
            "label": "Emphasize Leadership Skills",
            "description": "Highlight management, team leadership, and decision-making capabilities",
            "default": False
        },
        "emphasize_technical_skills": {
            "label": "Emphasize Technical Skills",
            "description": "Focus on hard skills, tools, and technologies",
            "default": True
        },
        "emphasize_soft_skills": {
            "label": "Emphasize Soft Skills",
            "description": "Highlight communication, teamwork, and interpersonal abilities",
            "default": False
        },
        "emphasize_achievements": {
            "label": "Emphasize Achievements",
            "description": "Focus on quantifiable results and accomplishments",
            "default": True
        },
        "emphasize_education": {
            "label": "Emphasize Education",
            "description": "Give more prominence to educational background and credentials",
            "default": False
        },
        "emphasize_remote_work": {
            "label": "Emphasize Remote Work Experience",
            "description": "Highlight remote work capabilities and experience",
            "default": False
        },
        "academic_focus": {
            "label": "Academic Focus",
            "description": "Emphasize academic achievements, publications, and research",
            "default": False
        },
        "highlight_certifications": {
            "label": "Highlight Certifications",
            "description": "Give prominence to professional certifications and credentials",
            "default": False
        },
        "career_transition": {
            "label": "Career Transition Focus",
            "description": "Emphasize transferable skills for changing careers or industries",
            "default": False
        },
        "ats_optimization": {
            "label": "ATS Optimization",
            "description": "Maximize compatibility with Applicant Tracking Systems",
            "default": True
        }
    }
