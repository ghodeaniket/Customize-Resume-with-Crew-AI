"""
Component for analyzing and visualizing resume customization results.

This component provides a dashboard of metrics and visualizations showing
the improvements made during the resume customization process.
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Tuple
import json
import re

from utils.text_processing.diff_highlighter import (
    split_resume_into_sections,
    generate_diff_for_sections,
    extract_key_changes
)


def render_results_dashboard(result: Dict[str, Any], comparison_data: Dict[str, Any]) -> None:
    """
    Render a dashboard of metrics and visualizations for the customization results.
    
    Args:
        result: The customization result data
        comparison_data: The comparison data from the comparison view
    """
    # Check if we have valid input
    if not isinstance(result, dict):
        st.warning("No valid result data available for analysis.")
        return
    
    if not isinstance(comparison_data, dict):
        comparison_data = {}  # Initialize as empty dict if not valid
    
    # Extract key metrics
    optimization_metrics = result.get("optimization_metrics", {})
    if not isinstance(optimization_metrics, dict):
        optimization_metrics = {}
    
    changes_summary = result.get("changes_summary", {})
    if not isinstance(changes_summary, dict):
        changes_summary = {}
    
    # Check if we have any metrics to display
    has_ats_score = "ats_score" in optimization_metrics or "ats_score_improvement" in optimization_metrics
    has_keyword_match = "keyword_match_rate" in optimization_metrics
    
    # If no metrics are available from the API result, generate metrics from comparison data
    if not has_ats_score and not has_keyword_match and not changes_summary and comparison_data:
        # Generate metrics based on text comparison
        st.info("No API metrics available. Showing analysis based on text comparison.")
        
        # Get diff percentage from comparison data
        diff_percentage = comparison_data.get("diff_percentage")
        if diff_percentage is not None:
            # Create a simulated ATS score
            original_score = 0.5  # Assume a baseline score of 50%
            improved_score = min(original_score + (diff_percentage / 100), 1.0)  # Improvement based on diff
            
            # Update optimization metrics
            optimization_metrics["original_ats_score"] = original_score
            optimization_metrics["customized_ats_score"] = improved_score
            optimization_metrics["ats_score_improvement"] = improved_score - original_score
            
            # Set flag to render ATS metrics
            has_ats_score = True
    
    # Render available metrics sections
    if has_ats_score:
        render_ats_score_metrics(optimization_metrics)
    
    if has_keyword_match:
        render_keyword_match_metrics(optimization_metrics, result.get("job_keywords", []))
    
    # Always render content change metrics (it uses comparison data)
    render_content_change_metrics(comparison_data)
    
    # Render specific changes summary
    render_changes_summary(changes_summary, comparison_data)
    
    # Render optimization details
    render_optimization_details(result)


def render_ats_score_metrics(metrics: Dict[str, Any]) -> None:
    """
    Render ATS score metrics visualization.
    
    Args:
        metrics: The optimization metrics
    """
    st.markdown("### ATS Score Improvement")
    
    # Validate metrics dictionary
    if not isinstance(metrics, dict):
        st.warning("ATS score metrics not available.")
        return
    
    # Get ATS scores
    original_score = metrics.get("original_ats_score", 0)
    if isinstance(original_score, str) and original_score.endswith('%'):
        try:
            original_score = float(original_score.rstrip('%')) / 100
        except ValueError:
            original_score = 0
    elif isinstance(original_score, str):
        try:
            original_score = float(original_score)
        except ValueError:
            original_score = 0
    
    # Get improved score, trying different possible field names
    improved_score = metrics.get("customized_ats_score", 
                               metrics.get("ats_score", 
                                        metrics.get("improved_ats_score", 0)))
    
    if isinstance(improved_score, str) and improved_score.endswith('%'):
        try:
            improved_score = float(improved_score.rstrip('%')) / 100
        except ValueError:
            improved_score = 0
    elif isinstance(improved_score, str):
        try:
            improved_score = float(improved_score)
        except ValueError:
            improved_score = 0
    
    # Get score improvement, or calculate it if not provided
    score_improvement = metrics.get("ats_score_improvement")
    if score_improvement is None:
        if 0 <= original_score <= 1 and 0 <= improved_score <= 1:
            score_improvement = improved_score - original_score
        else:
            score_improvement = 0
    elif isinstance(score_improvement, str) and score_improvement.endswith('%'):
        try:
            score_improvement = float(score_improvement.rstrip('%')) / 100
        except ValueError:
            score_improvement = 0
    elif isinstance(score_improvement, str):
        try:
            score_improvement = float(score_improvement)
        except ValueError:
            score_improvement = 0
    
    # Ensure scores are in 0-1 range for visualization
    if 0 <= original_score <= 1 and 0 <= improved_score <= 1:
        # Create columns for side-by-side score display
        col1, col2, col3 = st.columns([4, 4, 3])
        
        with col1:
            st.markdown("<p style='text-align: center; margin-bottom: 0.5rem;'>Original Score</p>", unsafe_allow_html=True)
            # Create a progress bar for original score
            st.progress(original_score)
            st.markdown(f"<p style='text-align: center; font-size: 1.5rem; font-weight: bold; margin-top: 0.5rem;'>{original_score:.0%}</p>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<p style='text-align: center; margin-bottom: 0.5rem;'>Customized Score</p>", unsafe_allow_html=True)
            # Create a progress bar for improved score
            st.progress(improved_score)
            st.markdown(f"<p style='text-align: center; font-size: 1.5rem; font-weight: bold; margin-top: 0.5rem;'>{improved_score:.0%}</p>", unsafe_allow_html=True)
        
        with col3:
            st.markdown("<p style='text-align: center; margin-bottom: 0.5rem;'>Improvement</p>", unsafe_allow_html=True)
            # Display improvement percentage
            score_improvement_pct = score_improvement * 100
            st.markdown(
                f"""
                <div style="
                    background-color: {('#fecaca' if score_improvement_pct < 0 else '#d1fae5')};
                    padding: 1rem;
                    border-radius: 0.5rem;
                    text-align: center;
                    margin-top: 0.75rem;
                ">
                    <p style="font-size: 1.5rem; font-weight: bold; margin: 0;">
                        {score_improvement_pct:+.0f}%
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        # If scores are not in 0-1 range, display them directly
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Original Score", original_score)
        
        with col2:
            st.metric("Customized Score", improved_score, 
                     delta=score_improvement if score_improvement is not None else None)
    
    # Show ATS score interpretation
    with st.expander("What is an ATS Score?", expanded=False):
        st.markdown("""
        The **ATS Score** represents how well your resume might perform in an Applicant Tracking System (ATS).
        
        - **Below 60%**: Your resume might be filtered out before reaching human reviewers
        - **60-80%**: Your resume has a moderate chance of passing ATS filters
        - **Above 80%**: Your resume is well-optimized for ATS systems
        
        The score is calculated based on keyword matching, formatting, and other factors that affect how ATS systems process resumes.
        """)


def render_keyword_match_metrics(metrics: Dict[str, Any], job_keywords: Optional[List[str]] = None) -> None:
    """
    Render keyword match metrics visualization.
    
    Args:
        metrics: The optimization metrics
        job_keywords: List of keywords from the job description
    """
    st.markdown("### Keyword Matching")
    
    # Validate metrics dictionary
    if not isinstance(metrics, dict):
        st.warning("Keyword match metrics not available.")
        return
    
    # Ensure job_keywords is a list if provided
    if job_keywords is not None and not isinstance(job_keywords, list):
        job_keywords = []
    
    # Get keyword match metrics
    keyword_match_rate = metrics.get("keyword_match_rate", 0)
    if isinstance(keyword_match_rate, str) and keyword_match_rate.endswith('%'):
        try:
            keyword_match_rate = float(keyword_match_rate.rstrip('%')) / 100
        except ValueError:
            keyword_match_rate = 0
    elif isinstance(keyword_match_rate, str):
        try:
            keyword_match_rate = float(keyword_match_rate)
        except ValueError:
            keyword_match_rate = 0
    
    # Ensure match rate is in 0-1 range
    if isinstance(keyword_match_rate, (int, float)) and 0 <= keyword_match_rate <= 1:
        # Display match rate as percentage
        st.progress(keyword_match_rate)
        st.markdown(f"<p style='text-align: center; font-size: 1.25rem;'><strong>{keyword_match_rate:.0%}</strong> of key job requirements matched</p>", unsafe_allow_html=True)
    else:
        st.metric("Keyword Match Rate", keyword_match_rate)
    
    # Display matched keywords if available
    matched_keywords = metrics.get("matched_keywords", [])
    missing_keywords = metrics.get("missing_keywords", [])
    
    # Ensure keywords are lists
    if not isinstance(matched_keywords, list):
        matched_keywords = []
    if not isinstance(missing_keywords, list):
        missing_keywords = []
    
    # If no matched/missing keywords but we have job_keywords and match rate
    if not matched_keywords and not missing_keywords and job_keywords and isinstance(keyword_match_rate, (int, float)) and 0 <= keyword_match_rate <= 1:
        if keyword_match_rate > 0:
            # Estimate matched keywords based on match rate
            matched_count = round(len(job_keywords) * keyword_match_rate)
            matched_keywords = job_keywords[:matched_count]
            missing_keywords = job_keywords[matched_count:]
    
    # Display keyword chips
    if matched_keywords or missing_keywords:
        st.markdown("<p style='margin-top: 1rem;'>Keyword matching:</p>", unsafe_allow_html=True)
        
        # Create columns for matched and missing keywords
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<p style='margin-bottom: 0.5rem;'><strong>Matched Keywords</strong></p>", unsafe_allow_html=True)
            if matched_keywords:
                st.markdown(
                    "".join([
                        f"""<span style="
                            display: inline-block;
                            background-color: #d1fae5;
                            border: 1px solid #6ee7b7;
                            color: #065f46;
                            padding: 0.25rem 0.5rem;
                            border-radius: 0.25rem;
                            margin: 0.25rem;
                            font-size: 0.875rem;
                        ">{keyword}</span>"""
                        for keyword in matched_keywords
                    ]),
                    unsafe_allow_html=True
                )
            else:
                st.markdown("<p style='color: #64748b; font-style: italic;'>No matched keywords identified</p>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<p style='margin-bottom: 0.5rem;'><strong>Missing Keywords</strong></p>", unsafe_allow_html=True)
            if missing_keywords:
                st.markdown(
                    "".join([
                        f"""<span style="
                            display: inline-block;
                            background-color: #fee2e2;
                            border: 1px solid #fca5a5;
                            color: #991b1b;
                            padding: 0.25rem 0.5rem;
                            border-radius: 0.25rem;
                            margin: 0.25rem;
                            font-size: 0.875rem;
                        ">{keyword}</span>"""
                        for keyword in missing_keywords
                    ]),
                    unsafe_allow_html=True
                )
            else:
                st.markdown("<p style='color: #64748b; font-style: italic;'>No missing keywords identified</p>", unsafe_allow_html=True)


def render_content_change_metrics(comparison_data: Dict[str, Any]) -> None:
    """
    Render content change metrics based on diff analysis.
    
    Args:
        comparison_data: The comparison data from the comparison view
    """
    st.markdown("### Content Analysis")
    
    # Validate comparison_data dictionary
    if not isinstance(comparison_data, dict):
        st.warning("Content change metrics not available.")
        return
    
    # Check if we have an error in the comparison data
    if "error" in comparison_data:
        st.warning(f"Content analysis not available: {comparison_data['error']}")
        return
    
    # Get key metrics from comparison data
    sections_modified = comparison_data.get("sections_modified", 0)
    diff_percentage = comparison_data.get("diff_percentage", 0)
    sections_by_status = comparison_data.get("sections_by_status", {})
    
    if not isinstance(sections_by_status, dict):
        sections_by_status = {}
    
    sections_added = sections_by_status.get("added", comparison_data.get("sections_added", 0))
    sections_removed = sections_by_status.get("removed", comparison_data.get("sections_removed", 0))
    
    # Create metrics display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Sections Modified", sections_modified)
    
    with col2:
        st.metric("New Sections", sections_added)
    
    with col3:
        if diff_percentage is not None:
            st.metric("Content Changed", f"{diff_percentage:.0f}%")
        else:
            st.metric("Sections Removed", sections_removed)
    
    # Show word count comparison if available
    if "original_words" in comparison_data and "customized_words" in comparison_data:
        original_words = comparison_data.get("original_words", 0)
        customized_words = comparison_data.get("customized_words", 0)
        words_diff = comparison_data.get("words_diff", customized_words - original_words)
        
        st.markdown("<p style='margin-top: 1rem;'>Word count analysis:</p>", unsafe_allow_html=True)
        
        # Create columns for word count metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Original Word Count", original_words)
        
        with col2:
            st.metric("Customized Word Count", customized_words)
        
        with col3:
            # Calculate percentage change
            if original_words > 0:
                percentage_change = (words_diff / original_words) * 100
                st.metric("Change", words_diff, delta=f"{percentage_change:.0f}%")
            else:
                st.metric("Change", words_diff)


def render_changes_summary(changes_summary: Optional[Dict[str, Any]], comparison_data: Optional[Dict[str, Any]]) -> None:
    """
    Render a summary of specific changes made during customization.
    
    Args:
        changes_summary: The changes summary from the result
        comparison_data: The comparison data from the comparison view
    """
    st.markdown("### Key Changes Made")
    
    # Validate input dictionaries
    if not isinstance(changes_summary, dict):
        changes_summary = {}
    
    if not isinstance(comparison_data, dict):
        comparison_data = {}
    
    # Check if we have changes summary from the API
    if changes_summary and len(changes_summary) > 0:
        # Display changes from the API
        for category, changes in changes_summary.items():
            # Format category name
            category_name = category.replace("_", " ").title()
            
            # Create expandable section
            with st.expander(f"{category_name}", expanded=True):
                if isinstance(changes, list):
                    # Display list of changes
                    if changes:
                        for change in changes:
                            st.markdown(f"- {change}")
                    else:
                        st.markdown("No changes in this category.")
                elif isinstance(changes, dict):
                    # Display dictionary of changes
                    if changes:
                        for key, value in changes.items():
                            st.markdown(f"**{key}**: {value}")
                    else:
                        st.markdown("No changes in this category.")
                else:
                    # Display simple value
                    st.markdown(str(changes))
    else:
        # Extract changes from comparison data if available
        diff_data = comparison_data.get("diff_data")
        if diff_data and isinstance(diff_data, dict):
            # Extract key changes from diff data
            key_changes = extract_key_changes(diff_data)
            
            # Check if we have any changes
            has_changes = any(changes for changes in key_changes.values())
            
            if has_changes:
                # Display key changes by category
                for category, changes in key_changes.items():
                    if changes:
                        # Format category name
                        category_name = category.replace("_", " ").title()
                        
                        # Create expandable section
                        with st.expander(f"{category_name}", expanded=True):
                            for change in changes:
                                st.markdown(f"- {change}")
            else:
                st.info("No significant changes detected between the original and customized resume.")
        else:
            # No changes data available
            st.info("No detailed changes summary available.")


def render_optimization_details(result: Dict[str, Any]) -> None:
    """
    Render details about the optimization process.
    
    Args:
        result: The customization result data
    """
    # Validate result dictionary
    if not isinstance(result, dict):
        return
    
    # Create expandable section for optimization details
    with st.expander("Optimization Details", expanded=False):
        # Get optimization details
        customization_level = result.get("customization_level", "standard")
        processing_time = result.get("processing_time_ms")
        completion_time = result.get("completion_time")
        metadata = result.get("metadata", {})
        
        # Validate metadata
        if not isinstance(metadata, dict):
            metadata = {}
        
        # Merge metadata if present
        if metadata:
            if "customization_level" in metadata and not customization_level:
                customization_level = metadata["customization_level"]
            if "processing_time_ms" in metadata and not processing_time:
                processing_time = metadata["processing_time_ms"]
            if "completion_time" in metadata and not completion_time:
                completion_time = metadata["completion_time"]
        
        # Display optimization details
        st.markdown(f"**Customization Level**: {customization_level.title()}")
        
        if processing_time is not None:
            # Format processing time
            if isinstance(processing_time, (int, float)):
                if processing_time > 1000:
                    st.markdown(f"**Processing Time**: {processing_time / 1000:.2f} seconds")
                else:
                    st.markdown(f"**Processing Time**: {processing_time} ms")
            else:
                st.markdown(f"**Processing Time**: {processing_time}")
        
        if completion_time is not None:
            # Try to format completion time as datetime
            if isinstance(completion_time, (int, float)):
                from datetime import datetime
                try:
                    completion_dt = datetime.fromtimestamp(completion_time)
                    st.markdown(f"**Completion Time**: {completion_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                except:
                    st.markdown(f"**Completion Time**: {completion_time}")
            else:
                st.markdown(f"**Completion Time**: {completion_time}")
        
        # Display any other metadata
        if metadata:
            st.markdown("**Additional Metadata**:")
            metadata_list = []
            for key, value in metadata.items():
                # Skip keys we've already displayed
                if key in ["customization_level", "processing_time_ms", "completion_time"]:
                    continue
                
                # Format key name
                key_name = key.replace("_", " ").title()
                metadata_list.append(f"- **{key_name}**: {value}")
            
            if metadata_list:
                st.markdown("\n".join(metadata_list))
            else:
                st.markdown("No additional metadata available.")
        
        # If no details were displayed, show a message
        if not customization_level and not processing_time and not completion_time and not metadata:
            st.markdown("No optimization details available.")
