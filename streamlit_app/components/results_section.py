"""
Results Section component implementation (Phase 4).

This component provides a UI for displaying customization results,
showing the original vs. customized resume, highlighting changes,
and providing download options.
"""

import streamlit as st
import time
import difflib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import json
import re


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
            if st.button("View Status"):
                st.session_state.job_description_state["customization_view_results"] = False
                st.rerun()
                
            return
        elif st.session_state.job_description_state.get("customization_status") == "failed":
            # Show error message
            error_message = st.session_state.job_description_state.get("customization_error", "Unknown error")
            st.error(f"Customization failed: {error_message}")
            
            # Offer retry button
            if st.button("Retry Customization"):
                st.session_state.job_description_state["step"] = "input"
                st.session_state.nav_state["current_step"] = 2
                st.rerun()
                
            return
        else:
            # Show message if no customization has been performed
            st.warning("No customization results available yet.")
            
            # Link to start customization
            if st.button("Start Customization"):
                st.session_state.nav_state["current_step"] = 2
                st.rerun()
                
            return
    
    # Create tabs for different views
    tabs = st.tabs(["Side by Side Comparison", "Key Changes", "Download Options"])
    
    with tabs[0]:
        render_side_by_side_comparison(result)
    
    with tabs[1]:
        render_key_changes(result)
    
    with tabs[2]:
        render_download_options(result)
    
    # Add ability to start a new customization
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Customize for Another Job", type="secondary", use_container_width=True):
            # Reset the job description state but keep the resume
            reset_for_new_job()
    
    with col2:
        if st.button("Start Over with New Resume", type="secondary", use_container_width=True):
            # Reset everything and go back to step 1
            reset_everything()


def render_side_by_side_comparison(result):
    """
    Render a side-by-side comparison of original and customized resumes.
    
    Args:
        result: The customization result data
    """
    st.subheader("Before and After Comparison")
    
    # Get original resume text from session state
    original_text = st.session_state.upload_state.get("extracted_text", "")
    customized_text = result.get("customized_text", "")
    
    # Create columns for side-by-side display
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Original Resume")
        st.text_area(
            "Original Content",
            value=original_text,
            height=400,
            disabled=True,
            key="original_resume_textbox"
        )
    
    with col2:
        st.markdown("### Customized Resume")
        st.text_area(
            "Customized Content",
            value=customized_text,
            height=400,
            disabled=True,
            key="customized_resume_textbox"
        )
    
    # Show optimization metrics if available
    if "optimization_metrics" in result:
        metrics = result["optimization_metrics"]
        
        st.markdown("### Optimization Metrics")
        
        # Create metrics display with columns
        metric_cols = st.columns(len(metrics))
        
        for i, (key, value) in enumerate(metrics.items()):
            with metric_cols[i]:
                # Format the metric name
                metric_name = key.replace("_", " ").title()
                
                # Format the value
                if isinstance(value, float):
                    if 0 <= value <= 1:
                        # If value is between 0-1, display as percentage
                        value_display = f"{value * 100:.1f}%"
                    else:
                        # Otherwise display with 1 decimal place
                        value_display = f"{value:.1f}"
                else:
                    value_display = str(value)
                
                # Show metric
                st.metric(metric_name, value_display)


def render_key_changes(result):
    """
    Render a summary of key changes made during customization.
    
    Args:
        result: The customization result data
    """
    st.subheader("Key Changes Summary")
    
    if "changes_summary" in result:
        changes = result["changes_summary"]
        
        # Show summary in expandable sections
        for section, items in changes.items():
            # Format section name
            section_name = section.replace("_", " ").title()
            
            with st.expander(f"{section_name}", expanded=True):
                if isinstance(items, list):
                    # Display list items
                    for item in items:
                        st.markdown(f"- {item}")
                elif isinstance(items, dict):
                    # Display dictionary items
                    for key, value in items.items():
                        st.markdown(f"**{key}**: {value}")
                else:
                    # Display simple value
                    st.markdown(str(items))
    else:
        # If no changes summary is available
        st.info("No detailed changes summary available.")
        
        # Try to generate a simple diff
        st.markdown("### Changes Highlighted")
        try:
            # Get original and customized text
            original_text = st.session_state.upload_state.get("extracted_text", "")
            customized_text = result.get("customized_text", "")
            
            # Generate diff
            diff = generate_text_diff(original_text, customized_text)
            
            # Display diff with highlights
            st.markdown(diff, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error generating diff: {str(e)}")


def render_download_options(result):
    """
    Render options for downloading the customized resume.
    
    Args:
        result: The customization result data
    """
    st.subheader("Download Your Customized Resume")
    
    # Get customized text
    customized_text = result.get("customized_text", "")
    
    if not customized_text:
        st.warning("No customized resume content available for download.")
        return
    
    st.info("Currently, only plain text download is available. More formats will be available in future updates.")
    
    # Create download button for text version
    download_text_as_file(customized_text, "customized_resume.txt", "Download as Text (.txt)")
    
    # Placeholder for future download options
    with st.expander("Future Download Options"):
        st.markdown("""
        The following formats will be available in upcoming updates:
        
        - PDF (.pdf)
        - Microsoft Word (.docx)
        - Rich Text Format (.rtf)
        - HTML (.html)
        - Markdown (.md)
        """)
        
        # Disabled buttons for future formats
        col1, col2 = st.columns(2)
        with col1:
            st.button("Download as PDF", disabled=True, use_container_width=True)
            st.button("Download as Word Document", disabled=True, use_container_width=True)
        
        with col2:
            st.button("Download as Rich Text", disabled=True, use_container_width=True)
            st.button("Download as HTML", disabled=True, use_container_width=True)


def generate_text_diff(original_text, customized_text):
    """
    Generate an HTML diff between original and customized text.
    
    Args:
        original_text: The original resume text
        customized_text: The customized resume text
        
    Returns:
        str: HTML markup with differences highlighted
    """
    # Split text into lines
    original_lines = original_text.splitlines()
    customized_lines = customized_text.splitlines()
    
    # Generate diff
    differ = difflib.HtmlDiff()
    diff_html = differ.make_file(original_lines, customized_lines, context=True)
    
    # Extract just the table part of the diff
    table_match = re.search(r'<table.*?>(.*?)</table>', diff_html, re.DOTALL)
    if table_match:
        table_html = table_match.group(0)
        
        # Add custom styling
        styled_html = f"""
        <style>
        .diff {{
            font-family: monospace;
            border-collapse: collapse;
            width: 100%;
        }}
        .diff td {{
            padding: 3px;
            border: 1px solid #ddd;
        }}
        .diff .diff_add {{
            background-color: #d4edda;
        }}
        .diff .diff_sub {{
            background-color: #f8d7da;
        }}
        .diff .diff_chg {{
            background-color: #fff3cd;
        }}
        </style>
        
        <div style="overflow-x: auto;">
        {table_html}
        </div>
        """
        
        return styled_html
    else:
        # If table extraction fails, return a simple comparison
        return "<p>Diff generation failed. Please use the side-by-side comparison.</p>"


def download_text_as_file(text_content, filename, button_text):
    """
    Create a download button for text content.
    
    Args:
        text_content: The text to download
        filename: The filename to use
        button_text: Text to display on the button
    """
    # Create a button that triggers download when clicked
    st.download_button(
        label=button_text,
        data=text_content,
        file_name=filename,
        mime="text/plain",
        use_container_width=True
    )


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
