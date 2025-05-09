"""
Results Section component implementation (Phase 5).

This component provides a comprehensive UI for displaying customization results,
showing the original vs. customized resume with detailed comparison,
providing analytics, and offering multiple export options.
"""

import streamlit as st
import time
import difflib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import json
import re

# Import components
from components.compare_view import render_compare_view
from components.results_dashboard import render_results_dashboard

# Import utilities
from utils.text_processing.diff_highlighter import (
    split_resume_into_sections,
    generate_diff_for_sections,
    extract_key_changes
)
from utils.text_processing.export import (
    export_as_text,
    export_as_html, 
    export_as_pdf,
    export_as_docx,
    copy_to_clipboard,
    get_print_friendly_view
)


def render_results_section():
    """Render the customization results section."""
    
    st.markdown("## Customization Results")
    
    # Get the result from session state
    result = st.session_state.job_description_state.get("customization_result")
    
    if not result:
        # If no result is available, show loading or error message
        if st.session_state.job_description_state.get("customization_status") == "processing":
            # Show processing message
            st.info("Your resume is still being customized. Please wait for the process to complete.")
            
            # Link back to status section
            if st.button("View Status", key="results_view_status_btn"):
                st.session_state.job_description_state["customization_view_results"] = False
                st.rerun()
                
            return
        elif st.session_state.job_description_state.get("customization_status") == "failed":
            # Show error message
            error_message = st.session_state.job_description_state.get("customization_error", "Unknown error")
            st.error(f"Customization failed: {error_message}")
            
            # Offer retry button
            if st.button("Retry Customization", key="results_retry_customization_btn"):
                st.session_state.job_description_state["step"] = "input"
                st.session_state.nav_state["current_step"] = 2
                st.rerun()
                
            return
        else:
            # Show message if no customization has been performed
            st.warning("No customization results available yet.")
            
            # Link to start customization
            if st.button("Start Customization", key="results_start_customization_btn"):
                st.session_state.nav_state["current_step"] = 2
                st.rerun()
                
            return
    
    # Validate result is a dictionary
    if not isinstance(result, dict):
        st.error("Invalid result format. Please try again.")
        
        # Show result for debugging
        with st.expander("Debug Information", expanded=False):
            st.write("Result type:", type(result))
            st.write("Result content:", result)
        
        # Offer retry button
        if st.button("Retry Customization", key="results_retry_invalid_btn"):
            st.session_state.job_description_state["step"] = "input"
            st.session_state.nav_state["current_step"] = 2
            st.rerun()
            
        return
    
    # Extract the customized text
    customized_text = None
    
    # Check for common result formats
    if "customized_text" in result:
        customized_text = result["customized_text"]
    elif "result" in result:
        customized_text = result["result"]
    elif "text" in result:
        customized_text = result["text"]
    
    # Create a copy of the result with the extracted customized text
    processed_result = dict(result)
    processed_result["customized_text"] = customized_text
    
    # Create tabs for different views
    tabs = st.tabs(["Comparison", "Analysis", "Export", "Feedback"])
    
    with tabs[0]:
        # Get original resume text from session state
        original_text = st.session_state.upload_state.get("extracted_text", "")
        
        # Debug info
        with st.expander("Debug Information", expanded=False):
            st.write("Original text available:", original_text is not None)
            st.write("Original text length:", len(original_text) if original_text else 0)
            st.write("Customized text available:", customized_text is not None)
            st.write("Customized text length:", len(customized_text) if customized_text else 0)
        
        # Render the comparison view and get comparison data
        comparison_data = render_compare_view(original_text, customized_text)
    
    with tabs[1]:
        # Render the results dashboard
        render_results_dashboard(processed_result, comparison_data)
    
    with tabs[2]:
        # Render export options with our enhanced export functionality
        render_export_options(processed_result)
    
    with tabs[3]:
        # Render feedback section
        render_feedback_section(processed_result)
    
    # Add ability to start a new customization
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Customize for Another Job", type="secondary", use_container_width=True, key="results_new_job_btn"):
            # Reset the job description state but keep the resume
            reset_for_new_job()
    
    with col2:
        if st.button("Start Over with New Resume", type="secondary", use_container_width=True, key="results_start_over_btn"):
            # Reset everything and go back to step 1
            reset_everything()


def render_export_options(result: Dict[str, Any]):
    """
    Render comprehensive export options for the customized resume.
    
    Args:
        result: The customization result data
    """
    st.subheader("Export Your Customized Resume")
    
    # Get customized text
    customized_text = result.get("customized_text", "")
    
    if not customized_text:
        st.warning("No customized resume content available for export.")
        return
    
    # Create copy button
    st.markdown("<p style='margin-bottom: 0.5rem;'>Quick Copy:</p>", unsafe_allow_html=True)
    copy_to_clipboard(customized_text)
    
    # Create file name base - include date in format YYYY-MM-DD
    today = datetime.now().strftime("%Y-%m-%d")
    job_title = result.get("job_title", "")
    if not job_title and "metadata" in result:
        job_title = result.get("metadata", {}).get("job_title", "")
    
    # Create a base filename
    if job_title:
        base_filename = f"Resume_{today}_{job_title.replace(' ', '_')}"
    else:
        base_filename = f"Customized_Resume_{today}"
    
    # Display export options
    st.markdown("<p style='margin: 1.5rem 0 0.5rem 0;'>Download Options:</p>", unsafe_allow_html=True)
    
    # Create two columns layout for export buttons
    col1, col2 = st.columns(2)
    
    with col1:
        # Text export
        export_as_text(customized_text, f"{base_filename}.txt")
        
        # HTML export
        export_as_html(customized_text, "Customized Resume", f"{base_filename}.html")
    
    with col2:
        # PDF export
        export_as_pdf(customized_text, f"{base_filename}.pdf")
        
        # DOCX export
        export_as_docx(customized_text, f"{base_filename}.docx")
    
    # Print-friendly view
    st.markdown("<p style='margin: 1.5rem 0 0.5rem 0;'>Print-Friendly View:</p>", unsafe_allow_html=True)
    
    # Create print-friendly HTML view
    print_html = get_print_friendly_view(customized_text)
    
    # Display the print-friendly view in an iframe
    st.markdown(
        f"""
        <iframe srcdoc='{print_html}' width="100%" height="600px" style="border: 1px solid #e2e8f0; border-radius: 0.5rem;"></iframe>
        """,
        unsafe_allow_html=True
    )
    
    # Provide edit options
    st.markdown("<p style='margin: 1.5rem 0 0.5rem 0;'>Edit Before Export:</p>", unsafe_allow_html=True)
    
    # Create editable text area
    edited_text = st.text_area(
        "Make your final edits before exporting:",
        value=customized_text,
        height=300,
        key="editable_resume_text"
    )
    
    # Only show save button if text has been changed
    if edited_text != customized_text:
        if st.button("Save Edits", key="save_edits_btn"):
            # Update the result in session state
            result["customized_text"] = edited_text
            st.session_state.job_description_state["customization_result"] = result
            st.success("Your edits have been saved!")
            st.rerun()


def render_feedback_section(result: Dict[str, Any]):
    """
    Render feedback collection and customization quality rating.
    
    Args:
        result: The customization result data
    """
    st.subheader("Provide Feedback")
    
    # Create rating system
    st.markdown("<p>How would you rate the quality of this customization?</p>", unsafe_allow_html=True)
    
    # Get current rating from session state if available
    current_rating = st.session_state.get("customization_rating", 0)
    
    # Create 5-star rating
    rating = st.slider(
        "Rating",
        min_value=1,
        max_value=5,
        value=current_rating if current_rating > 0 else 3,
        step=1,
        help="Rate the quality of the customized resume from 1 (poor) to 5 (excellent)",
        key="customization_rating_slider"
    )
    
    # Store rating in session state
    st.session_state["customization_rating"] = rating
    
    # Render star icons based on rating
    rating_stars = "⭐" * rating + "☆" * (5 - rating)
    st.markdown(f"<p style='font-size: 1.5rem; text-align: center;'>{rating_stars}</p>", unsafe_allow_html=True)
    
    # Additional feedback text area
    feedback_text = st.text_area(
        "Additional feedback or suggestions (optional):",
        key="customization_feedback_text"
    )
    
    # Submit feedback button
    if st.button("Submit Feedback", key="submit_feedback_btn"):
        # Store feedback in session state
        st.session_state["customization_feedback"] = {
            "rating": rating,
            "feedback": feedback_text,
            "timestamp": datetime.now().isoformat()
        }
        
        # Show success message
        st.success("Thank you for your feedback!")
    
    # Option to regenerate with different parameters
    st.markdown("<p style='margin-top: 1.5rem;'>Not satisfied? You can regenerate your resume with different parameters:</p>", unsafe_allow_html=True)
    
    if st.button("Regenerate with Different Parameters", key="regenerate_params_btn"):
        # Keep the job description but reset customization state
        st.session_state.job_description_state["customization_task_id"] = None
        st.session_state.job_description_state["customization_status"] = None
        st.session_state.job_description_state["customization_progress"] = 0
        st.session_state.job_description_state["customization_result"] = None
        st.session_state.job_description_state["step"] = "input"
        st.session_state.nav_state["current_step"] = 2
        st.rerun()


def reset_for_new_job():
    """Reset state for customizing for a new job while keeping the resume."""
    # Keep the resume but reset the job description and customization
    st.session_state.job_description_state = {
        "raw_text": "",
        "processed_text": "",
        "is_processing": False,
        "is_valid": False,
        "error": None,
        "validation_result": None,
        "last_update": None,
        "keywords": [],
        "saved_descriptions": [],
        "customization_level": "standard",
        "industry": None,
        "customization_task_id": None,
        "customization_status": None,
        "customization_progress": 0,
        "customization_result": None,
        "step": "input",
        "auto_preview": True,
    }
    
    # Reset customization state but keep preferences
    preferences = st.session_state.customization_state.get("preferences", {})
    saved_presets = st.session_state.customization_state.get("saved_presets", {})
    
    st.session_state.customization_state = {
        "customization_level": "standard",
        "industry": None,
        "subindustry": None,
        "preferences": preferences,
        "custom_preferences": {},
        "custom_instructions": "",
        "keywords_to_include": [],
        "keywords_to_exclude": [],
        "saved_presets": saved_presets,
        "active_preset": None,
        "is_submitting": False,
        "error": None
    }
    
    # Update navigation state
    st.session_state.nav_state["current_step"] = 2
    
    # Rerun to update UI
    st.rerun()


def reset_everything():
    """Reset all state and start over from the beginning."""
    # Reset all state
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
    
    st.session_state.job_description_state = {
        "raw_text": "",
        "processed_text": "",
        "is_processing": False,
        "is_valid": False,
        "error": None,
        "validation_result": None,
        "last_update": None,
        "keywords": [],
        "saved_descriptions": [],
        "customization_level": "standard",
        "industry": None,
        "customization_task_id": None,
        "customization_status": None,
        "customization_progress": 0,
        "customization_result": None,
        "step": "input",
        "auto_preview": True,
    }
    
    # Keep saved presets
    saved_presets = st.session_state.customization_state.get("saved_presets", {})
    
    st.session_state.customization_state = {
        "customization_level": "standard",
        "industry": None,
        "subindustry": None,
        "preferences": {
            "emphasize_leadership": False,
            "emphasize_technical_skills": True,
            "emphasize_soft_skills": False,
            "emphasize_achievements": True,
            "emphasize_education": False,
            "emphasize_remote_work": False,
            "academic_focus": False,
            "highlight_certifications": False,
            "career_transition": False,
            "ats_optimization": True
        },
        "custom_preferences": {},
        "custom_instructions": "",
        "keywords_to_include": [],
        "keywords_to_exclude": [],
        "saved_presets": saved_presets,
        "active_preset": None,
        "is_submitting": False,
        "error": None
    }
    
    # Reset navigation state
    st.session_state.nav_state = {
        "current_step": 1,
        "can_proceed": False,
        "steps_completed": [],
    }
    
    # Rerun to update UI
    st.rerun()
