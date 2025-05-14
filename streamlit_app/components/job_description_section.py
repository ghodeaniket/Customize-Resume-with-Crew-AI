"""
Job description input and processing component.

This component provides the UI for Phase 2 of the Resume Customizer application,
allowing users to input, process, and preview job descriptions.
"""

import streamlit as st
import json
import time
import uuid
from datetime import datetime
import pandas as pd
from typing import Dict, Any, List, Optional

from utils.text_processing import (
    sanitize_text,
    escape_json_characters,
    validate_job_description,
    extract_keywords,
    clean_pasted_html
)
from utils.job_models import (
    JobDescriptionValidationResult,
    CustomizationRequest,
    SavedJobDescription
)
from services.job_description_service import submit_customization


def render_job_description_section():
    """Render the job description input and processing section."""
    st.markdown("## Step 2: Job Description")
    
    # Only show if resume has been processed
    if not st.session_state.upload_state["task_id"] or st.session_state.upload_state["status"] != "completed":
        st.info("Please upload and process a resume first before continuing to this step.")
        return
    
    # Create tabs for the different parts of the process
    tab1, tab2, tab3 = st.tabs(["Input", "Preview", "Saved Descriptions"])
    
    with tab1:
        render_text_input()
    
    with tab2:
        render_preview()
    
    with tab3:
        render_saved_descriptions()
    
    # Show processing controls
    render_processing_controls()


def render_text_input():
    """Render the job description text input area."""
    job_state = st.session_state.job_description_state
    
    # Instruction box
    st.markdown(
        """
        <div class="info-box">
            <h4>📝 Paste Your Job Description</h4>
            <p>Copy and paste the complete job description from any job site. 
            The text will be automatically processed to ensure compatibility with our system.</p>
            <p><strong>Tip:</strong> Include as much detail as possible for the best results.</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Text input area
    input_placeholder = (
        "Paste job description here...\n\n"
        "Example:\n"
        "Senior Software Engineer\n\n"
        "About Us:\n"
        "Our company is looking for an experienced software engineer to join our team...\n\n"
        "Responsibilities:\n"
        "- Design and develop scalable applications\n"
        "- Collaborate with cross-functional teams\n\n"
        "Requirements:\n"
        "- 5+ years of experience in software development\n"
        "- Proficiency in Python and JavaScript\n"
        "- Bachelor's degree in Computer Science or related field"
    )
    
    # Create a key for the text area - this helps control when it updates
    text_area_key = "job_description_input"
    
    # Job title input (optional)
    job_title = st.text_input(
        "Job Title (Optional):",
        key="job_title_input", 
        help="Enter the job title for easier reference later."
    )
    
    # Company name input (optional)
    company = st.text_input(
        "Company (Optional):",
        key="company_input", 
        help="Enter the company name for easier reference later."
    )
    
    # Source URL input (optional)
    source_url = st.text_input(
        "Source URL (Optional):",
        key="source_url_input", 
        help="Enter the job posting URL for reference."
    )
    
    # Text area for job description
    raw_text = st.text_area(
        "Job Description:",
        value=job_state["raw_text"],
        height=300,
        key=text_area_key,
        placeholder=input_placeholder,
        help="Paste the complete job description here."
    )
    
    # Update the state when text changes
    if raw_text != job_state["raw_text"]:
        job_state["raw_text"] = raw_text
        job_state["is_valid"] = False
        job_state["error"] = None
        job_state["last_update"] = datetime.now().isoformat()
        
        # Process the text if auto-preview is enabled
        if job_state["auto_preview"] and raw_text:
            process_text(raw_text)
    
    # Character count and controls
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if raw_text:
            char_count = len(raw_text)
            word_count = len(raw_text.split())
            st.caption(f"Character count: {char_count} | Word count: {word_count}")
    
    with col2:
        auto_preview = st.checkbox("Auto Preview", value=job_state["auto_preview"])
        if auto_preview != job_state["auto_preview"]:
            job_state["auto_preview"] = auto_preview
    
    # Process button (only shown if auto-preview is disabled)
    if not job_state["auto_preview"]:
        if st.button("Process Text", key="process_text_btn"):
            process_text(raw_text)
    
    # Show any errors
    if job_state["error"]:
        st.error(job_state["error"])
    
    # Add save button
    if raw_text and job_state["processed_text"]:
        if st.button("Save Description", key="save_description_btn"):
            save_description(raw_text, job_state["processed_text"], job_title, company, source_url)


def process_text(text: str):
    """
    Process the job description text to prepare it for API submission.
    
    Args:
        text: The raw job description text
    """
    job_state = st.session_state.job_description_state
    
    if not text:
        job_state["error"] = "Please enter a job description."
        return
    
    # Set processing state
    job_state["is_processing"] = True
    
    try:
        # Check for HTML content and clean if necessary
        if "<" in text and ">" in text:
            text = clean_pasted_html(text)
        
        # Sanitize the text
        processed_text = sanitize_text(text)
        
        # Test JSON serialization by creating a sample request
        test_obj = {"job_description": processed_text}
        json_str = json.dumps(test_obj)
        json.loads(json_str)  # Validate it can be parsed back
        
        # Validate the job description
        validation_result = validate_job_description(processed_text)
        
        # Extract keywords
        keywords = extract_keywords(processed_text)
        
        # Update state
        job_state["processed_text"] = processed_text
        job_state["is_valid"] = validation_result["is_valid"]
        job_state["validation_result"] = validation_result
        job_state["keywords"] = keywords
        job_state["error"] = None
        job_state["step"] = "preview"
        
    except Exception as e:
        # If there's an error in processing, try more aggressive sanitization
        try:
            # Use more aggressive JSON escaping
            processed_text = escape_json_characters(text)
            
            # Test JSON serialization again
            test_obj = {"job_description": processed_text}
            json_str = json.dumps(test_obj)
            json.loads(json_str)  # Validate it can be parsed back
            
            # If we get here, the aggressive sanitization worked
            job_state["processed_text"] = processed_text
            job_state["is_valid"] = True
            job_state["error"] = None
            job_state["step"] = "preview"
            
            # Add a warning about aggressive processing
            validation_result = {
                "is_valid": True,
                "errors": [],
                "warnings": ["Special characters were removed to prevent JSON parsing errors."],
                "suggestions": ["Review the processed text to ensure all important information is preserved."],
                "character_count": len(processed_text)
            }
            job_state["validation_result"] = validation_result
            
        except Exception as e2:
            # Try emergency sanitization if both regular and aggressive sanitization fail
            try:
                # First try deep_clean_text
                from utils.text_processing import deep_clean_text, character_by_character_clean
                
                # Try the deep cleaning approach
                processed_text = deep_clean_text(text)
                
                # Test JSON serialization with deep cleaned text
                test_obj = {"job_description": processed_text}
                json_str = json.dumps(test_obj)
                json.loads(json_str)  # Validate it can be parsed back
                
                # Extract keywords (might fail, so wrap in try-except)
                try:
                    keywords = extract_keywords(processed_text)
                except:
                    keywords = {"technical_skills": [], "soft_skills": [], "education": [], "experience": [], "other": []}
                
                # Update state with emergency processed text
                job_state["processed_text"] = processed_text
                job_state["is_valid"] = True
                job_state["error"] = None
                job_state["step"] = "preview"
                job_state["keywords"] = keywords
                
                # Add a warning about emergency processing
                validation_result = {
                    "is_valid": True,
                    "errors": [],
                    "warnings": ["Emergency text processing was applied to prevent parsing errors."],
                    "suggestions": ["Review the processed text carefully to ensure important information is preserved."],
                    "character_count": len(processed_text)
                }
                job_state["validation_result"] = validation_result
                
            except Exception as e3:
                # Last resort: character-by-character processing
                try:
                    # Use character-by-character processing as last resort
                    processed_text = character_by_character_clean(text)
                    
                    # Test if it can be serialized
                    test_obj = {"job_description": processed_text}
                    json_str = json.dumps(test_obj)
                    
                    # Update state with emergency processed text
                    job_state["processed_text"] = processed_text
                    job_state["is_valid"] = True
                    job_state["error"] = None
                    job_state["step"] = "preview"
                    
                    # Use empty keywords
                    job_state["keywords"] = {"technical_skills": [], "soft_skills": [], "education": [], "experience": [], "other": []}
                    
                    # Add a warning about emergency processing
                    validation_result = {
                        "is_valid": True,
                        "errors": [],
                        "warnings": ["Extreme text processing was necessary. All special characters were removed."],
                        "suggestions": ["Review the processed text carefully. You may need to manually edit some sections."],
                        "character_count": len(processed_text)
                    }
                    job_state["validation_result"] = validation_result
                    
                except Exception as e4:
                    # If all sanitization approaches fail
                    job_state["error"] = f"Error processing text: {str(e4)}. Please manually remove special characters or formatting."
                    job_state["is_valid"] = False
    
    finally:
        # Reset processing state
        job_state["is_processing"] = False


def render_preview():
    """Render the preview of the processed job description."""
    job_state = st.session_state.job_description_state
    
    # Show preview only if there's processed text
    if not job_state["processed_text"]:
        st.info("Process a job description to see the preview.")
        return
    
    st.markdown("### Processed Job Description")
    
    # Show validation results
    validation = job_state["validation_result"]
    if validation:
        # Determine overall status
        if validation["is_valid"]:
            if validation["warnings"]:
                st.warning(
                    "Job description processed with warnings. "
                    "We've automatically resolved potential issues, but please review the text below."
                )
            else:
                st.success("Job description processed successfully!")
        else:
            st.error("Job description has issues that need to be addressed.")
        
        # Show specific errors, warnings, and suggestions
        if validation["errors"]:
            for error in validation["errors"]:
                st.error(error)
                
        if validation["warnings"]:
            for warning in validation["warnings"]:
                st.warning(warning)
                
        if validation["suggestions"]:
            st.markdown("#### Suggestions:")
            for suggestion in validation["suggestions"]:
                st.info(suggestion)
    
    # Show the processed text
    st.markdown("#### Preview:")
    st.text_area(
        "Processed Text (Ready for API submission):",
        value=job_state["processed_text"],
        height=200,
        key="processed_text_preview",
        disabled=True
    )
    
    # Show extracted keywords
    if job_state["keywords"]:
        st.markdown("#### Extracted Keywords:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if job_state["keywords"]["technical_skills"]:
                st.markdown("**Technical Skills:**")
                for skill in job_state["keywords"]["technical_skills"]:
                    st.markdown(f"- {skill}")
                    
            if job_state["keywords"]["education"]:
                st.markdown("**Education:**")
                for edu in job_state["keywords"]["education"]:
                    st.markdown(f"- {edu}")
        
        with col2:
            if job_state["keywords"]["soft_skills"]:
                st.markdown("**Soft Skills:**")
                for skill in job_state["keywords"]["soft_skills"]:
                    st.markdown(f"- {skill}")
                    
            if job_state["keywords"]["experience"]:
                st.markdown("**Experience:**")
                for exp in job_state["keywords"]["experience"]:
                    st.markdown(f"- {exp}")
    
    # JSON validation test
    st.markdown("#### JSON Validation:")
    expander = st.expander("View JSON Representation")
    with expander:
        try:
            test_obj = {"job_description": job_state["processed_text"]}
            json_str = json.dumps(test_obj, indent=2)
            st.code(json_str, language="json")
            st.success("✅ Valid JSON - No parsing errors detected")
        except Exception as e:
            st.error(f"❌ Invalid JSON: {str(e)}")


def render_saved_descriptions():
    """Render the saved job descriptions list."""
    job_state = st.session_state.job_description_state
    
    st.markdown("### Saved Job Descriptions")
    
    if not job_state["saved_descriptions"]:
        st.info("You haven't saved any job descriptions yet.")
        return
    
    # Create a dataframe from saved descriptions
    saved_data = []
    for desc in job_state["saved_descriptions"]:
        title = desc.title or "Untitled"
        company = desc.company or "N/A"
        created = desc.created_at.split("T")[0] if "T" in desc.created_at else desc.created_at
        preview = desc.description[:50] + "..." if len(desc.description) > 50 else desc.description
        
        saved_data.append({
            "ID": desc.id,
            "Title": title,
            "Company": company,
            "Date": created,
            "Preview": preview
        })
    
    df = pd.DataFrame(saved_data)
    
    # Show the table
    st.dataframe(df, use_container_width=True)
    
    # Add load/delete functionality
    col1, col2 = st.columns(2)
    
    with col1:
        selected_id = st.selectbox(
            "Select saved description:",
            options=[desc.id for desc in job_state["saved_descriptions"]],
            format_func=lambda x: next((f"{desc.title} ({desc.company})" if desc.company else desc.title) 
                                        for desc in job_state["saved_descriptions"] if desc.id == x)
        )
    
    with col2:
        load_col, delete_col = st.columns(2)
        
        with load_col:
            if st.button("Load", key="load_saved_desc_btn"):
                load_saved_description(selected_id)
                
        with delete_col:
            if st.button("Delete", key="delete_saved_desc_btn"):
                delete_saved_description(selected_id)


def render_processing_controls():
    """Render the controls for processing the job description."""
    job_state = st.session_state.job_description_state
    
    # Only show if we have a valid processed text
    if not job_state["is_valid"] or not job_state["processed_text"]:
        return
    
    st.markdown("### Customization Options")
    
    # Customization level
    st.radio(
        "Customization Level:",
        options=["minimal", "standard", "comprehensive"],
        index=1,  # Default to standard
        key="customization_level_radio",
        help="""
        - Minimal: Light customization preserving most of the original content
        - Standard: Balanced customization for most job applications
        - Comprehensive: Extensive customization for highly competitive positions
        """
    )
    
    # Industry selection
    industries = [
        "Technology", "Healthcare", "Finance", "Education", "Manufacturing", 
        "Retail", "Government", "Nonprofit", "Media", "Other"
    ]
    
    industry = st.selectbox(
        "Industry (Optional):",
        options=[None] + industries,
        index=0,
        key="industry_selectbox",
        help="Select the industry for better customization results"
    )
    
    # Custom keywords
    # Check if keywords is a dictionary (expected structure) or a list (modified structure)
    keyword_options = []
    if isinstance(job_state["keywords"], dict):
        # Original dictionary structure from keyword extraction
        if "technical_skills" in job_state["keywords"]:
            keyword_options.extend(job_state["keywords"].get("technical_skills", []))
        if "soft_skills" in job_state["keywords"]:
            keyword_options.extend(job_state["keywords"].get("soft_skills", []))
        if "other" in job_state["keywords"]:
            keyword_options.extend(job_state["keywords"].get("other", []))
    elif isinstance(job_state["keywords"], list):
        # Modified list structure from customization options
        keyword_options = job_state["keywords"]
    
    custom_keywords = st.multiselect(
        "Emphasize Keywords (Optional):",
        options=keyword_options,
        default=[],
        key="custom_keywords_multiselect",
        help="Select keywords to emphasize in your resume customization"
    )
    
    # Save settings to state
    job_state["customization_level"] = st.session_state.customization_level_radio
    job_state["industry"] = industry
    job_state["keywords"] = custom_keywords
    
    # Submit button
    if st.button("Customize Resume", key="customize_resume_btn", type="primary"):
        submit_customization_request()


def submit_customization_request():
    """Submit the customization request to the API."""
    job_state = st.session_state.job_description_state
    upload_state = st.session_state.upload_state
    
    # Validate we have everything we need
    if not upload_state["task_id"]:
        st.error("No resume has been uploaded. Please upload a resume first.")
        return
    
    if not job_state["processed_text"]:
        st.error("No job description has been processed. Please enter and process a job description.")
        return
    
    # Create the request
    request = CustomizationRequest(
        resume_id=upload_state["task_id"],
        job_description=job_state["processed_text"],
        customize_level=job_state["customization_level"],
        industry=job_state["industry"],
        keywords=job_state["keywords"]
    )
    
    # Set processing state
    job_state["is_processing"] = True
    job_state["step"] = "submitting"
    
    try:
        # Submit the request
        response = submit_customization(request)
        
        # Update state with the response
        job_state["customization_task_id"] = response["data"]["task_id"]
        job_state["customization_status"] = response["data"]["status"]
        job_state["customization_progress"] = 0
        job_state["step"] = "complete"
        
        # Update navigation state to proceed to the next step
        st.session_state.nav_state["current_step"] = 3
        st.session_state.nav_state["can_proceed"] = True
        if 2 not in st.session_state.nav_state["steps_completed"]:
            st.session_state.nav_state["steps_completed"].append(2)
        
        # Show success message
        st.success("Customization request submitted successfully! Proceeding to results.")
        
        # Rerun to update UI
        st.rerun()
        
    except Exception as e:
        job_state["error"] = f"Error submitting customization request: {str(e)}"
        job_state["step"] = "preview"
    
    finally:
        # Reset processing state
        job_state["is_processing"] = False


def save_description(
    raw_text: str, 
    processed_text: str, 
    title: Optional[str] = None, 
    company: Optional[str] = None, 
    source_url: Optional[str] = None
):
    """
    Save a job description for later use.
    
    Args:
        raw_text: Original job description text
        processed_text: Processed job description text
        title: Optional job title
        company: Optional company name
        source_url: Optional source URL
    """
    job_state = st.session_state.job_description_state
    
    # Create a unique ID
    description_id = str(uuid.uuid4())
    
    # Set a default title if none provided
    if not title:
        title = f"Job Description {len(job_state['saved_descriptions']) + 1}"
    
    # Create the saved description object
    saved_desc = SavedJobDescription(
        id=description_id,
        title=title,
        description=raw_text,
        processed_description=processed_text,
        company=company,
        source_url=source_url,
        keywords=job_state["keywords"].get("technical_skills", [])[:5],
        created_at=datetime.now().isoformat()
    )
    
    # Add to saved descriptions
    job_state["saved_descriptions"].append(saved_desc)
    
    # Show success message
    st.success(f"Job description saved as '{title}'.")


def load_saved_description(description_id: str):
    """
    Load a saved job description.
    
    Args:
        description_id: ID of the saved description to load
    """
    job_state = st.session_state.job_description_state
    
    # Find the saved description
    saved_desc = next((desc for desc in job_state["saved_descriptions"] if desc.id == description_id), None)
    
    if saved_desc:
        # Load the description into the current state
        job_state["raw_text"] = saved_desc.description
        job_state["processed_text"] = saved_desc.processed_description
        job_state["is_valid"] = True
        job_state["error"] = None
        job_state["step"] = "preview"
        
        # Process to update validation and keywords
        process_text(saved_desc.description)
        
        # Show success message
        st.success(f"Loaded job description: {saved_desc.title}")
        
        # Rerun to update UI
        st.rerun()
    else:
        st.error(f"Could not find saved description with ID: {description_id}")


def delete_saved_description(description_id: str):
    """
    Delete a saved job description.
    
    Args:
        description_id: ID of the saved description to delete
    """
    job_state = st.session_state.job_description_state
    
    # Find the saved description
    saved_desc = next((desc for desc in job_state["saved_descriptions"] if desc.id == description_id), None)
    
    if saved_desc:
        # Remove from saved descriptions
        job_state["saved_descriptions"] = [desc for desc in job_state["saved_descriptions"] if desc.id != description_id]
        
        # Show success message
        st.success(f"Deleted job description: {saved_desc.title}")
        
        # Rerun to update UI
        st.rerun()
    else:
        st.error(f"Could not find saved description with ID: {description_id}")
