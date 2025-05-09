"""
Component for side-by-side resume comparison view.

This component provides a detailed side-by-side comparison of the
original and customized resumes with multiple viewing options.
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Tuple
import html

from utils.text_processing.diff_highlighter import (
    split_resume_into_sections,
    generate_diff_for_sections,
    generate_html_diff,
    highlight_added_removed_content
)


def render_compare_view(original_text: Optional[str], customized_text: Optional[str]) -> Dict[str, Any]:
    """
    Render a side-by-side comparison view with various display options.
    
    Args:
        original_text: The original resume text
        customized_text: The customized resume text
        
    Returns:
        Dict[str, Any]: Dictionary containing comparison metadata and analysis
    """
    # Ensure both texts are strings
    original_text = original_text or ""
    customized_text = customized_text or ""
    
    # Check if valid texts are available
    if not original_text and not customized_text:
        st.warning("No resume text available for comparison.")
        return {"error": "No text available for comparison"}
    
    # Create view options
    view_options = ["Basic View", "Highlighted Differences", "Section-by-Section", "Unified Diff"]
    selected_view = st.radio("Select View Mode:", view_options, horizontal=True)
    
    # Initialize comparison data
    comparison_data = {}
    
    # Render the appropriate view
    if selected_view == "Basic View":
        comparison_data = render_basic_view(original_text, customized_text)
    elif selected_view == "Highlighted Differences":
        comparison_data = render_highlighted_view(original_text, customized_text)
    elif selected_view == "Section-by-Section":
        comparison_data = render_section_view(original_text, customized_text)
    elif selected_view == "Unified Diff":
        comparison_data = render_unified_diff(original_text, customized_text)
    
    return comparison_data


def render_basic_view(original_text: str, customized_text: str) -> Dict[str, Any]:
    """
    Render a basic side-by-side comparison view.
    
    Args:
        original_text: The original resume text
        customized_text: The customized resume text
        
    Returns:
        Dict[str, Any]: Basic comparison metadata
    """
    # Create columns for side-by-side display
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Original Resume")
        if not original_text:
            st.info("No original resume text available.")
        else:
            st.text_area(
                "Original Content",
                value=original_text,
                height=500,
                disabled=True,
                key="basic_original_resume_textbox"
            )
    
    with col2:
        st.markdown("### Customized Resume")
        if not customized_text:
            st.info("No customized resume text available.")
        else:
            st.text_area(
                "Customized Content",
                value=customized_text,
                height=500,
                disabled=True,
                key="basic_customized_resume_textbox"
            )
    
    # Calculate basic metadata
    original_lines = len(original_text.splitlines()) if original_text else 0
    customized_lines = len(customized_text.splitlines()) if customized_text else 0
    original_words = len(original_text.split()) if original_text else 0
    customized_words = len(customized_text.split()) if customized_text else 0
    
    # Compare lengths
    lines_diff = customized_lines - original_lines
    words_diff = customized_words - original_words
    
    # Return comparison data
    return {
        "original_lines": original_lines,
        "customized_lines": customized_lines,
        "original_words": original_words,
        "customized_words": customized_words,
        "lines_diff": lines_diff,
        "words_diff": words_diff,
        "sections_modified": None,
        "diff_percentage": None
    }


def render_highlighted_view(original_text: str, customized_text: str) -> Dict[str, Any]:
    """
    Render a view with highlighted differences.
    
    Args:
        original_text: The original resume text
        customized_text: The customized resume text
        
    Returns:
        Dict[str, Any]: Comparison metadata with highlights
    """
    # Check if both texts are available
    if not original_text or not customized_text:
        st.warning("Both original and customized texts are required for highlighted differences view.")
        return {
            "original_lines": len(original_text.splitlines()) if original_text else 0,
            "customized_lines": len(customized_text.splitlines()) if customized_text else 0,
            "error": "Missing text for comparison"
        }
    
    # Generate highlighted versions
    highlighted_original, highlighted_customized = highlight_added_removed_content(
        original_text, customized_text
    )
    
    # Create columns for side-by-side display
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Original Resume")
        st.markdown(
            f"""<div class="highlighted-text" style="
                white-space: pre-wrap;
                font-family: monospace;
                background-color: #f8fafc;
                padding: 1rem;
                border-radius: 0.25rem;
                border: 1px solid #e2e8f0;
                height: 500px;
                overflow-y: auto;
                font-size: 0.85rem;
                line-height: 1.5;
            ">{highlighted_original}</div>""",
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown("### Customized Resume")
        st.markdown(
            f"""<div class="highlighted-text" style="
                white-space: pre-wrap;
                font-family: monospace;
                background-color: #f8fafc;
                padding: 1rem;
                border-radius: 0.25rem;
                border: 1px solid #e2e8f0;
                height: 500px;
                overflow-y: auto;
                font-size: 0.85rem;
                line-height: 1.5;
            ">{highlighted_customized}</div>""",
            unsafe_allow_html=True
        )
    
    # Provide a legend
    st.markdown(
        """
        <div style="display: flex; gap: 1rem; margin-top: 1rem; justify-content: center;">
            <div>
                <span style="display: inline-block; width: 1rem; height: 1rem; background-color: #fee2e2; margin-right: 0.5rem;"></span>
                <span>Removed content</span>
            </div>
            <div>
                <span style="display: inline-block; width: 1rem; height: 1rem; background-color: #d1fae5; margin-right: 0.5rem;"></span>
                <span>Added content</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Get sections for additional metadata
    original_sections = split_resume_into_sections(original_text)
    customized_sections = split_resume_into_sections(customized_text)
    diff_data = generate_diff_for_sections(original_sections, customized_sections)
    
    # Count modified sections
    sections_modified = sum(1 for section, data in diff_data.items() 
                         if data["status"] == "modified" and data["change_percentage"] > 5)
    
    # Calculate overall difference percentage (average of section changes)
    section_percentages = [data["change_percentage"] for _, data in diff_data.items() 
                         if data["status"] != "unchanged"]
    diff_percentage = sum(section_percentages) / len(section_percentages) if section_percentages else 0
    
    # Return comparison data
    return {
        "original_lines": len(original_text.splitlines()),
        "customized_lines": len(customized_text.splitlines()),
        "original_words": len(original_text.split()),
        "customized_words": len(customized_text.split()),
        "lines_diff": len(customized_text.splitlines()) - len(original_text.splitlines()),
        "words_diff": len(customized_text.split()) - len(original_text.split()),
        "sections_modified": sections_modified,
        "diff_percentage": diff_percentage,
        "diff_data": diff_data
    }


def render_section_view(original_text: str, customized_text: str) -> Dict[str, Any]:
    """
    Render a section-by-section comparison view.
    
    Args:
        original_text: The original resume text
        customized_text: The customized resume text
        
    Returns:
        Dict[str, Any]: Section comparison metadata
    """
    # Check if both texts are available
    if not original_text or not customized_text:
        st.warning("Both original and customized texts are required for section view.")
        return {
            "original_lines": len(original_text.splitlines()) if original_text else 0,
            "customized_lines": len(customized_text.splitlines()) if customized_text else 0,
            "error": "Missing text for section comparison"
        }
    
    # Split resumes into sections
    original_sections = split_resume_into_sections(original_text)
    customized_sections = split_resume_into_sections(customized_text)
    
    # Generate diff data
    diff_data = generate_diff_for_sections(original_sections, customized_sections)
    
    # Check if any sections were found
    if not diff_data:
        st.warning("No distinct sections could be identified in the resumes.")
        return {
            "original_lines": len(original_text.splitlines()),
            "customized_lines": len(customized_text.splitlines()),
            "error": "No sections identified"
        }
    
    # Create section selector
    all_sections = sorted(diff_data.keys())
    
    # Add status indicators to section names
    section_options = []
    for section in all_sections:
        status = diff_data[section]["status"]
        if status == "added":
            section_options.append(f"{section} 🟢")
        elif status == "removed":
            section_options.append(f"{section} 🔴")
        elif status == "modified":
            change_pct = diff_data[section]["change_percentage"]
            if change_pct > 20:
                section_options.append(f"{section} 🟠 ({change_pct}%)")
            else:
                section_options.append(f"{section} 🟡 ({change_pct}%)")
        else:
            section_options.append(f"{section} ⚪")
    
    selected_section = st.selectbox("Select Section:", section_options)
    
    # Extract the actual section name without the status indicator
    section_name = selected_section.split(" 🟢")[0].split(" 🔴")[0].split(" 🟠")[0].split(" 🟡")[0].split(" ⚪")[0]
    
    # Get the section data
    section_data = diff_data[section_name]
    
    # Display section status
    status_color = {
        "added": "#d1fae5",
        "removed": "#fee2e2",
        "modified": "#fef3c7",
        "unchanged": "#f1f5f9"
    }
    
    st.markdown(
        f"""
        <div style="
            background-color: {status_color[section_data['status']]};
            padding: 0.5rem 1rem;
            border-radius: 0.25rem;
            margin-bottom: 1rem;
        ">
            <p style="margin: 0; font-weight: bold;">
                Section Status: {section_data['status'].upper()}
                {f" • {section_data['change_percentage']}% changed" if section_data['status'] == 'modified' else ""}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Create columns for section comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Original Section")
        if section_data["status"] == "added":
            st.info("This section was not present in the original resume.")
        else:
            st.text_area(
                "Original Content",
                value=section_data["original"],
                height=400,
                disabled=True,
                key=f"section_original_{section_name}"
            )
    
    with col2:
        st.markdown("### Customized Section")
        if section_data["status"] == "removed":
            st.warning("This section was removed in the customized resume.")
        else:
            st.text_area(
                "Customized Content",
                value=section_data["customized"],
                height=400,
                disabled=True,
                key=f"section_customized_{section_name}"
            )
    
    # Show detailed diff for modified sections
    if section_data["status"] == "modified":
        with st.expander("View detailed differences", expanded=False):
            st.markdown(
                generate_html_diff(section_data["original"], section_data["customized"]),
                unsafe_allow_html=True
            )
    
    # Count sections by status
    sections_by_status = {status: 0 for status in ["added", "removed", "modified", "unchanged"]}
    for _, data in diff_data.items():
        sections_by_status[data["status"]] += 1
    
    # Calculate overall difference percentage (average of section changes)
    section_percentages = [data["change_percentage"] for _, data in diff_data.items() 
                          if data["status"] != "unchanged"]
    diff_percentage = sum(section_percentages) / len(section_percentages) if section_percentages else 0
    
    # Return comparison data
    return {
        "sections_by_status": sections_by_status,
        "sections_modified": sections_by_status["modified"],
        "sections_added": sections_by_status["added"],
        "sections_removed": sections_by_status["removed"],
        "diff_percentage": diff_percentage,
        "diff_data": diff_data
    }


def render_unified_diff(original_text: str, customized_text: str) -> Dict[str, Any]:
    """
    Render a unified diff view.
    
    Args:
        original_text: The original resume text
        customized_text: The customized resume text
        
    Returns:
        Dict[str, Any]: Comparison metadata
    """
    # Check if both texts are available
    if not original_text or not customized_text:
        st.warning("Both original and customized texts are required for unified diff view.")
        return {
            "original_lines": len(original_text.splitlines()) if original_text else 0,
            "customized_lines": len(customized_text.splitlines()) if customized_text else 0,
            "error": "Missing text for unified diff"
        }
    
    # Generate the HTML diff
    diff_html = generate_html_diff(original_text, customized_text)
    
    # Display the diff
    st.markdown(
        diff_html,
        unsafe_allow_html=True
    )
    
    # Provide a legend
    st.markdown(
        """
        <div style="display: flex; gap: 1rem; margin-top: 1rem; justify-content: center;">
            <div>
                <span style="display: inline-block; width: 1rem; height: 1rem; background-color: #fee2e2; margin-right: 0.5rem;"></span>
                <span>Removed content</span>
            </div>
            <div>
                <span style="display: inline-block; width: 1rem; height: 1rem; background-color: #d1fae5; margin-right: 0.5rem;"></span>
                <span>Added content</span>
            </div>
            <div>
                <span style="display: inline-block; width: 1rem; height: 1rem; background-color: #fef3c7; margin-right: 0.5rem;"></span>
                <span>Changed content</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Get sections for additional metadata
    original_sections = split_resume_into_sections(original_text)
    customized_sections = split_resume_into_sections(customized_text)
    diff_data = generate_diff_for_sections(original_sections, customized_sections)
    
    # Count modified sections
    sections_modified = sum(1 for section, data in diff_data.items() 
                         if data["status"] == "modified" and data["change_percentage"] > 5)
    
    # Calculate overall difference percentage (average of section changes)
    section_percentages = [data["change_percentage"] for _, data in diff_data.items() 
                         if data["status"] != "unchanged"]
    diff_percentage = sum(section_percentages) / len(section_percentages) if section_percentages else 0
    
    # Return comparison data
    return {
        "original_lines": len(original_text.splitlines()),
        "customized_lines": len(customized_text.splitlines()),
        "sections_modified": sections_modified,
        "diff_percentage": diff_percentage,
        "diff_data": diff_data
    }
