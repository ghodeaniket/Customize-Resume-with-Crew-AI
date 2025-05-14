"""
Customization options component implementation (Phase 3).

This component provides a comprehensive UI for configuring resume customization options
including customization level, industry selection, preferences, and presets.
"""

import streamlit as st
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from utils.job_models import CustomizationRequest
from services.job_description_service import submit_customization


# Definition of industry categories and subcategories
INDUSTRY_CATEGORIES = {
    "Technology": [
        "Software Development",
        "Data Science & Analytics",
        "IT & Infrastructure",
        "Cybersecurity",
        "Product Management",
        "UX/UI Design",
        "Artificial Intelligence",
        "Cloud Computing",
    ],
    "Finance": [
        "Banking",
        "Investment Management",
        "Financial Analysis",
        "Accounting",
        "Insurance",
        "Fintech",
        "Risk Management",
    ],
    "Healthcare": [
        "Medical Practice",
        "Nursing",
        "Pharmaceutical",
        "Healthcare Administration",
        "Biotechnology",
        "Health Technology",
        "Mental Health",
    ],
    "Marketing & Sales": [
        "Digital Marketing",
        "Content Creation",
        "Public Relations",
        "Social Media",
        "Sales",
        "Market Research",
        "Brand Management",
    ],
    "Education": [
        "K-12 Education",
        "Higher Education",
        "Educational Technology",
        "Training & Development",
        "Research",
        "Academic Administration",
    ],
    "Engineering": [
        "Civil Engineering",
        "Mechanical Engineering",
        "Electrical Engineering",
        "Chemical Engineering",
        "Environmental Engineering",
        "Aerospace Engineering",
    ],
    "Business & Management": [
        "Project Management",
        "Operations",
        "Human Resources",
        "Consulting",
        "Business Analysis",
        "Administrative",
        "Entrepreneurship",
    ],
    "Creative Fields": [
        "Graphic Design",
        "Media Production",
        "Writing & Editing",
        "Performing Arts",
        "Fashion",
        "Architecture",
        "Game Design",
    ],
    "Legal": [
        "Law Practice",
        "Legal Counsel",
        "Compliance",
        "Intellectual Property",
        "Regulatory Affairs",
    ],
    "Other": ["General", "Non-Profit", "Government", "Customer Service", "Retail", "Manufacturing"]
}

# Common job types with preset configurations
JOB_TYPE_PRESETS = {
    "Software Developer": {
        "customization_level": "standard",
        "industry": "Technology",
        "subindustry": "Software Development",
        "preferences": {
            "emphasize_technical_skills": True,
            "highlight_projects": True,
            "include_github": True,
            "focus_on_teamwork": True,
            "highlight_problem_solving": True
        },
        "description": "Emphasizes coding skills, technical projects, and collaborative problem-solving experience."
    },
    "Data Scientist": {
        "customization_level": "standard",
        "industry": "Technology",
        "subindustry": "Data Science & Analytics",
        "preferences": {
            "emphasize_technical_skills": True,
            "highlight_quantitative_achievements": True,
            "include_research": True,
            "focus_on_technical_communication": True,
            "highlight_problem_solving": True
        },
        "description": "Highlights statistical analysis, machine learning expertise, and data-driven decision making."
    },
    "Marketing Specialist": {
        "customization_level": "standard",
        "industry": "Marketing & Sales",
        "subindustry": "Digital Marketing",
        "preferences": {
            "emphasize_creative_skills": True,
            "highlight_campaigns": True,
            "include_results_metrics": True,
            "focus_on_communication": True,
            "highlight_social_media": True
        },
        "description": "Focuses on campaign results, creative content development, and audience engagement metrics."
    },
    "Project Manager": {
        "customization_level": "standard",
        "industry": "Business & Management",
        "subindustry": "Project Management",
        "preferences": {
            "emphasize_leadership": True,
            "highlight_project_deliverables": True,
            "include_methodologies": True,
            "focus_on_stakeholder_management": True,
            "highlight_budget_management": True
        },
        "description": "Emphasizes project delivery, team leadership, and organizational skills."
    },
    "Sales Professional": {
        "customization_level": "comprehensive",
        "industry": "Marketing & Sales",
        "subindustry": "Sales",
        "preferences": {
            "emphasize_achievements": True,
            "highlight_numbers": True,
            "include_client_relationships": True,
            "focus_on_negotiation": True,
            "highlight_territory_management": True
        },
        "description": "Focuses on sales achievements, revenue growth metrics, and relationship building."
    },
    "Healthcare Professional": {
        "customization_level": "standard",
        "industry": "Healthcare",
        "subindustry": "Medical Practice",
        "preferences": {
            "emphasize_credentials": True,
            "highlight_patient_care": True,
            "include_specialized_skills": True,
            "focus_on_teamwork": True,
            "highlight_continuous_education": True
        },
        "description": "Highlights clinical skills, patient care experience, and medical credentials."
    },
    "Teacher/Educator": {
        "customization_level": "standard",
        "industry": "Education",
        "subindustry": "K-12 Education",
        "preferences": {
            "emphasize_teaching_methods": True,
            "highlight_curriculum_development": True,
            "include_assessment": True,
            "focus_on_student_engagement": True,
            "highlight_classroom_management": True
        },
        "description": "Focuses on teaching methods, student outcomes, and educational innovation."
    },
    "Executive/Leadership": {
        "customization_level": "comprehensive",
        "industry": "Business & Management",
        "subindustry": "General",
        "preferences": {
            "emphasize_leadership": True,
            "highlight_strategic_vision": True,
            "include_executive_decisions": True,
            "focus_on_team_building": True,
            "highlight_business_growth": True
        },
        "description": "Emphasizes leadership philosophy, strategic vision, and organizational impact."
    },
    "Remote Worker": {
        "customization_level": "standard",
        "industry": "Other",
        "subindustry": "General",
        "preferences": {
            "emphasize_remote_skills": True,
            "highlight_self_management": True,
            "include_digital_tools": True,
            "focus_on_communication": True,
            "highlight_time_management": True
        },
        "description": "Highlights remote work capabilities, digital collaboration, and independent productivity."
    }
}

# Standard preference options available for all job types
STANDARD_PREFERENCE_OPTIONS = {
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


def render_customization_options():
    """Render the complete customization options interface."""
    st.markdown("## Step 3: Customization Options")
    
    # Initialize the customization state if not already present
    initialize_customization_state()
    
    # Only show if resume has been processed and job description is valid
    if (not st.session_state.upload_state["task_id"] or 
        st.session_state.upload_state["status"] != "completed" or
        not st.session_state.job_description_state["processed_text"]):
        st.info("Please complete the previous steps before configuring customization options.")
        return
    
    # Create tabs for different customization sections
    tab1, tab2, tab3 = st.tabs(["Basic Options", "Advanced Options", "Presets"])
    
    with tab1:
        render_basic_options()
    
    with tab2:
        render_advanced_options()
    
    with tab3:
        render_preset_configurations()
    
    # Separator before submit section
    st.markdown("---")
    
    # Summary and submission section
    render_summary_and_submit()


def initialize_customization_state():
    """Initialize the customization state variables if they don't exist."""
    if "customization_state" not in st.session_state:
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
            "saved_presets": {},
            "active_preset": None,
            "is_submitting": False,
            "error": None
        }


def render_basic_options():
    """Render the basic customization options."""
    st.markdown("### Basic Customization Options")
    
    # Customization level selection
    st.markdown("#### Customization Level")
    
    # Create columns for the customization level options
    col1, col2, col3 = st.columns(3)
    
    # Define the customization levels with details
    customization_levels = {
        "minimal": {
            "title": "Minimal",
            "description": "Light customization preserving 90% of original content",
            "icon": "🔍",
            "details": "Makes targeted keyword adjustments while maintaining most of your original resume content."
        },
        "standard": {
            "title": "Standard",
            "description": "Balanced customization for most applications",
            "icon": "⚖️",
            "details": "Optimizes your resume with appropriate keyword integration and structural adjustments."
        },
        "comprehensive": {
            "title": "Comprehensive",
            "description": "Extensive customization for competitive roles",
            "icon": "🚀",
            "details": "Complete resume transformation with significant content adjustments and optimal keyword placement."
        }
    }
    
    # Display the customization level options in cards
    with col1:
        minimal_selected = st.session_state.customization_state["customization_level"] == "minimal"
        minimal_container = st.container(border=True)
        minimal_container.markdown(f"### {customization_levels['minimal']['icon']} {customization_levels['minimal']['title']}")
        minimal_container.markdown(f"*{customization_levels['minimal']['description']}*")
        minimal_container.markdown(customization_levels['minimal']['details'])
        minimal_select = minimal_container.button("Select Minimal", key="minimal_level_btn", 
                                                 type="primary" if minimal_selected else "secondary",
                                                 disabled=minimal_selected)
        if minimal_select:
            st.session_state.customization_state["customization_level"] = "minimal"
            st.rerun()
            
    with col2:
        standard_selected = st.session_state.customization_state["customization_level"] == "standard"
        standard_container = st.container(border=True)
        standard_container.markdown(f"### {customization_levels['standard']['icon']} {customization_levels['standard']['title']}")
        standard_container.markdown(f"*{customization_levels['standard']['description']}*")
        standard_container.markdown(customization_levels['standard']['details'])
        standard_select = standard_container.button("Select Standard", key="standard_level_btn", 
                                                   type="primary" if standard_selected else "secondary",
                                                   disabled=standard_selected)
        if standard_select:
            st.session_state.customization_state["customization_level"] = "standard"
            st.rerun()
            
    with col3:
        comprehensive_selected = st.session_state.customization_state["customization_level"] == "comprehensive"
        comprehensive_container = st.container(border=True)
        comprehensive_container.markdown(f"### {customization_levels['comprehensive']['icon']} {customization_levels['comprehensive']['title']}")
        comprehensive_container.markdown(f"*{customization_levels['comprehensive']['description']}*")
        comprehensive_container.markdown(customization_levels['comprehensive']['details'])
        comprehensive_select = comprehensive_container.button("Select Comprehensive", key="comprehensive_level_btn", 
                                                           type="primary" if comprehensive_selected else "secondary",
                                                           disabled=comprehensive_selected)
        if comprehensive_select:
            st.session_state.customization_state["customization_level"] = "comprehensive"
            st.rerun()
    
    # Industry selection
    st.markdown("#### Industry Selection")
    
    # Industry category dropdown
    industry = st.selectbox(
        "Select Industry:",
        options=[None] + list(INDUSTRY_CATEGORIES.keys()),
        index=0 if st.session_state.customization_state["industry"] is None else 
              list(INDUSTRY_CATEGORIES.keys()).index(st.session_state.customization_state["industry"]) + 1,
        key="customization_industry_selectbox",
        help="Select the industry that best matches the job you're applying for"
    )
    
    # Update industry in state
    if industry != st.session_state.customization_state["industry"]:
        st.session_state.customization_state["industry"] = industry
        st.session_state.customization_state["subindustry"] = None
    
    # Sub-industry selection if an industry is selected
    if industry:
        subindustries = INDUSTRY_CATEGORIES[industry]
        subindustry = st.selectbox(
            "Select Specialty/Sub-industry:",
            options=[None] + subindustries,
            index=0 if st.session_state.customization_state["subindustry"] is None else 
                  subindustries.index(st.session_state.customization_state["subindustry"]) + 1,
            key="customization_subindustry_selectbox",
            help="Select a more specific area within the industry"
        )
        
        # Update subindustry in state
        if subindustry != st.session_state.customization_state["subindustry"]:
            st.session_state.customization_state["subindustry"] = subindustry
    
    # Extract and display keywords from job description
    if st.session_state.job_description_state["keywords"]:
        st.markdown("#### Extracted Keywords")
        st.info("These keywords were automatically extracted from the job description and will be emphasized in your resume.")
        
        keywords_container = st.container()
        keywords_col1, keywords_col2 = keywords_container.columns(2)
        
        # Check if keywords is a dictionary (expected structure) or a list (modified structure)
        if isinstance(st.session_state.job_description_state["keywords"], dict):
            # Technical skills
            if "technical_skills" in st.session_state.job_description_state["keywords"] and st.session_state.job_description_state["keywords"]["technical_skills"]:
                with keywords_col1:
                    st.markdown("**Technical Skills:**")
                    for skill in st.session_state.job_description_state["keywords"]["technical_skills"][:10]:
                        st.markdown(f"- {skill}")
            
            # Soft skills
            if "soft_skills" in st.session_state.job_description_state["keywords"] and st.session_state.job_description_state["keywords"]["soft_skills"]:
                with keywords_col2:
                    st.markdown("**Soft Skills:**")
                    for skill in st.session_state.job_description_state["keywords"]["soft_skills"][:10]:
                        st.markdown(f"- {skill}")
        elif isinstance(st.session_state.job_description_state["keywords"], list) and st.session_state.job_description_state["keywords"]:
            # If keywords is a list, display all in a single column
            with keywords_col1:
                st.markdown("**Keywords:**")
                for skill in st.session_state.job_description_state["keywords"][:15]:
                    st.markdown(f"- {skill}")
        
        # Custom keywords
        st.markdown("#### Additional Keywords")
        st.caption("Add any specific keywords you want to emphasize that weren't automatically detected.")
        
        custom_keywords = st.multiselect(
            "Add keywords to emphasize:",
            options=[],  # Empty because we want user to type their own
            default=st.session_state.customization_state["keywords_to_include"],
            key="custom_keywords_multiselect",
            help="Type any additional keywords you want to emphasize in your resume",
            placeholder="Type to add custom keywords..."
        )
        
        # Update custom keywords in state
        st.session_state.customization_state["keywords_to_include"] = custom_keywords


def render_advanced_options():
    """Render the advanced customization options."""
    st.markdown("### Advanced Customization Options")
    
    # Preferences section
    st.markdown("#### Customization Preferences")
    st.caption("Select specific aspects to emphasize in your resume customization.")
    
    # Create a container for the preferences
    preferences_container = st.container()
    
    # Create columns within the container
    col1, col2 = preferences_container.columns(2)
    
    # Iterate through preferences and create toggles
    preferences = st.session_state.customization_state["preferences"]
    preference_keys = list(STANDARD_PREFERENCE_OPTIONS.keys())
    half_length = (len(preference_keys) + 1) // 2
    
    # First column of preferences
    with col1:
        for key in preference_keys[:half_length]:
            option = STANDARD_PREFERENCE_OPTIONS[key]
            preference_value = preferences.get(key, option["default"])
            
            # Create the toggle with a label and help text
            new_value = st.checkbox(
                option["label"],
                value=preference_value,
                key=f"preference_{key}",
                help=option["description"]
            )
            
            # Update the preference in the state if it changed
            if new_value != preference_value:
                preferences[key] = new_value
    
    # Second column of preferences
    with col2:
        for key in preference_keys[half_length:]:
            option = STANDARD_PREFERENCE_OPTIONS[key]
            preference_value = preferences.get(key, option["default"])
            
            # Create the toggle with a label and help text
            new_value = st.checkbox(
                option["label"],
                value=preference_value,
                key=f"preference_{key}",
                help=option["description"]
            )
            
            # Update the preference in the state if it changed
            if new_value != preference_value:
                preferences[key] = new_value
    
    # Custom instructions
    st.markdown("#### Custom Instructions")
    st.caption("Add any specific instructions for how you want your resume customized.")
    
    custom_instructions = st.text_area(
        "Additional Instructions (Optional):",
        value=st.session_state.customization_state["custom_instructions"],
        key="custom_instructions_textarea",
        help="Include any specific requests or instructions for your resume customization",
        placeholder="Examples: 'Focus on my management experience', 'Emphasize my technical projects', etc."
    )
    
    # Update custom instructions in state
    if custom_instructions != st.session_state.customization_state["custom_instructions"]:
        st.session_state.customization_state["custom_instructions"] = custom_instructions
    
    # Keywords to exclude
    st.markdown("#### Excluded Content")
    st.caption("Specify any keywords or phrases you want to de-emphasize or exclude from your customized resume.")
    
    excluded_keywords = st.multiselect(
        "Keywords to de-emphasize:",
        options=[],  # Empty because we want user to type their own
        default=st.session_state.customization_state["keywords_to_exclude"],
        key="excluded_keywords_multiselect",
        help="Type any keywords you want to de-emphasize in your resume",
        placeholder="Type to add keywords to de-emphasize..."
    )
    
    # Update excluded keywords in state
    st.session_state.customization_state["keywords_to_exclude"] = excluded_keywords


def render_preset_configurations():
    """Render the preset configurations section."""
    st.markdown("### Preset Configurations")
    st.caption("Use or create preset configurations for common job types.")
    
    # Display the built-in presets
    st.markdown("#### Built-in Presets")
    preset_options = list(JOB_TYPE_PRESETS.keys())
    
    # Create 3 columns for preset selection
    cols = st.columns(3)
    
    # Create a button for each preset
    for i, preset_name in enumerate(preset_options):
        preset = JOB_TYPE_PRESETS[preset_name]
        col_index = i % 3
        
        with cols[col_index]:
            preset_container = st.container(border=True)
            preset_container.markdown(f"### {preset_name}")
            preset_container.caption(f"*{preset['industry']} - {preset['subindustry']}*")
            preset_container.markdown(preset["description"])
            
            # Button to apply the preset
            if preset_container.button(f"Apply", key=f"preset_{preset_name}_btn"):
                apply_preset(preset_name, preset)
                st.toast(f"Applied '{preset_name}' preset configuration")
                st.rerun()
    
    # Custom preset saving section
    st.markdown("#### Save Current Configuration as Preset")
    
    custom_preset_name = st.text_input(
        "Preset Name:",
        key="custom_preset_name",
        placeholder="Enter a name for your custom preset",
        help="Give your configuration a descriptive name"
    )
    
    # Save button
    if st.button("Save Current Configuration", key="save_preset_btn", disabled=not custom_preset_name):
        save_custom_preset(custom_preset_name)
        st.toast(f"Saved configuration as '{custom_preset_name}'")
        st.rerun()
    
    # Display saved custom presets
    if st.session_state.customization_state["saved_presets"]:
        st.markdown("#### Your Saved Presets")
        
        # Create columns for saved presets
        saved_cols = st.columns(3)
        
        # Display each saved preset
        for i, (preset_name, preset) in enumerate(st.session_state.customization_state["saved_presets"].items()):
            col_index = i % 3
            
            with saved_cols[col_index]:
                saved_container = st.container(border=True)
                saved_container.markdown(f"### {preset_name}")
                
                # Show industry info if available
                if preset.get("industry"):
                    subindustry_text = f" - {preset.get('subindustry')}" if preset.get("subindustry") else ""
                    saved_container.caption(f"*{preset['industry']}{subindustry_text}*")
                
                # Show customization level
                saved_container.markdown(f"Level: {preset.get('customization_level', 'standard').capitalize()}")
                
                # Buttons to apply or delete
                col1, col2 = saved_container.columns(2)
                
                with col1:
                    if st.button("Apply", key=f"apply_saved_{preset_name}_btn"):
                        apply_preset(preset_name, preset)
                        st.toast(f"Applied '{preset_name}' preset")
                        st.rerun()
                
                with col2:
                    if st.button("Delete", key=f"delete_saved_{preset_name}_btn"):
                        delete_custom_preset(preset_name)
                        st.toast(f"Deleted '{preset_name}' preset")
                        st.rerun()


def render_summary_and_submit():
    """Render a summary of the customization options and submit button."""
    st.markdown("### Customization Summary")
    
    # Create a container for the summary
    summary_container = st.container(border=True)
    
    # Basic info
    with summary_container:
        # Show active preset if any
        if st.session_state.customization_state["active_preset"]:
            st.success(f"Using preset: {st.session_state.customization_state['active_preset']}")
        
        # Create two columns for the summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Basic Settings")
            st.markdown(f"**Customization Level:** {st.session_state.customization_state['customization_level'].capitalize()}")
            
            industry_text = st.session_state.customization_state["industry"] or "Not specified"
            st.markdown(f"**Industry:** {industry_text}")
            
            if st.session_state.customization_state["subindustry"]:
                st.markdown(f"**Specialty:** {st.session_state.customization_state['subindustry']}")
            
            if st.session_state.customization_state["keywords_to_include"]:
                st.markdown("**Additional Keywords:**")
                for keyword in st.session_state.customization_state["keywords_to_include"]:
                    st.markdown(f"- {keyword}")
        
        with col2:
            st.markdown("#### Preferences")
            active_preferences = [
                STANDARD_PREFERENCE_OPTIONS[key]["label"] 
                for key, value in st.session_state.customization_state["preferences"].items() 
                if value
            ]
            
            if active_preferences:
                for pref in active_preferences:
                    st.markdown(f"- {pref}")
            else:
                st.markdown("No special preferences selected")
            
            if st.session_state.customization_state["custom_instructions"]:
                st.markdown("#### Custom Instructions")
                st.markdown(f"*{st.session_state.customization_state['custom_instructions']}*")
    
    # Submit button
    st.markdown("### Submit for Customization")
    submit_container = st.container()
    
    with submit_container:
        if st.button("Customize My Resume", key="final_submit_btn", type="primary"):
            submit_customization_request()


def apply_preset(preset_name: str, preset: Dict[str, Any]):
    """
    Apply a preset configuration to the customization state.
    
    Args:
        preset_name: Name of the preset
        preset: Preset configuration dictionary
    """
    # Update all the customization settings
    st.session_state.customization_state["customization_level"] = preset.get("customization_level", "standard")
    st.session_state.customization_state["industry"] = preset.get("industry")
    st.session_state.customization_state["subindustry"] = preset.get("subindustry")
    
    # Update preferences
    if "preferences" in preset:
        # Start with the default preferences
        preferences = {k: False for k in STANDARD_PREFERENCE_OPTIONS.keys()}
        
        # Update with the preset preferences
        for key, value in preset["preferences"].items():
            if key in STANDARD_PREFERENCE_OPTIONS:
                preferences[key] = value
        
        st.session_state.customization_state["preferences"] = preferences
    
    # Set active preset
    st.session_state.customization_state["active_preset"] = preset_name


def save_custom_preset(preset_name: str):
    """
    Save the current configuration as a custom preset.
    
    Args:
        preset_name: Name for the preset
    """
    # Get all the current settings
    current_config = {
        "customization_level": st.session_state.customization_state["customization_level"],
        "industry": st.session_state.customization_state["industry"],
        "subindustry": st.session_state.customization_state["subindustry"],
        "preferences": st.session_state.customization_state["preferences"].copy(),
        "keywords_to_include": st.session_state.customization_state["keywords_to_include"].copy(),
        "keywords_to_exclude": st.session_state.customization_state["keywords_to_exclude"].copy(),
        "custom_instructions": st.session_state.customization_state["custom_instructions"],
        "saved_on": datetime.now().isoformat()
    }
    
    # Save the preset
    if "saved_presets" not in st.session_state.customization_state:
        st.session_state.customization_state["saved_presets"] = {}
    
    st.session_state.customization_state["saved_presets"][preset_name] = current_config


def delete_custom_preset(preset_name: str):
    """
    Delete a saved custom preset.
    
    Args:
        preset_name: Name of the preset to delete
    """
    if preset_name in st.session_state.customization_state["saved_presets"]:
        del st.session_state.customization_state["saved_presets"][preset_name]
        
        # If this was the active preset, clear the active preset
        if st.session_state.customization_state["active_preset"] == preset_name:
            st.session_state.customization_state["active_preset"] = None


def submit_customization_request():
    """Submit the customization request to the API."""
    # Get the necessary state variables
    cust_state = st.session_state.customization_state
    job_state = st.session_state.job_description_state
    upload_state = st.session_state.upload_state
    
    # Validate we have everything we need
    if not upload_state["task_id"]:
        st.error("No resume has been uploaded. Please upload a resume first.")
        return
    
    if not job_state["processed_text"]:
        st.error("No job description has been processed. Please enter and process a job description.")
        return
    
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
                STANDARD_PREFERENCE_OPTIONS[key]["label"]
                for key, value in cust_state["preferences"].items()
                if value
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
            
            # Update job description state with the response
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
            
            # Rerun to update UI
            st.rerun()
            
        except Exception as e:
            cust_state["error"] = f"Error submitting customization request: {str(e)}"
            st.error(cust_state["error"])
        finally:
            # Reset submitting state
            cust_state["is_submitting"] = False
