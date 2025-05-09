"""
Text difference highlighting utilities.

This module provides functions for highlighting differences between original
and customized resume text, supporting different visualization formats.
"""

import difflib
import re
from typing import List, Dict, Any, Tuple, Optional
import html
import streamlit as st

def split_resume_into_sections(text: Optional[str]) -> Dict[str, str]:
    """
    Split a resume text into logical sections for better comparison.
    
    Args:
        text: The resume text
    
    Returns:
        Dict[str, str]: A dictionary of section names to section content
    """
    # Handle None or empty text
    if not text:
        return {"Main Content": ""}
    
    # Common section headers in resumes
    section_patterns = [
        r'^.*SUMMARY.*$',
        r'^.*EXPERIENCE.*$',
        r'^.*EDUCATION.*$',
        r'^.*SKILLS.*$',
        r'^.*CERTIFICATIONS.*$',
        r'^.*PROJECTS.*$',
        r'^.*PUBLICATIONS.*$',
        r'^.*AWARDS.*$',
        r'^.*LANGUAGES.*$',
        r'^.*INTERESTS.*$',
        r'^.*VOLUNTEER.*$',
        r'^.*REFERENCES.*$'
    ]
    
    # Initialize sections dictionary with a "Header" section for content before the first section
    sections = {"Header": ""}
    
    # Join patterns with OR operator and make them case-insensitive
    pattern = '|'.join(section_patterns)
    
    # Split the text into lines
    lines = text.splitlines()
    
    # Start with the header section
    current_section = "Header"
    
    for line in lines:
        # Check if this line could be a section header
        if re.search(pattern, line, re.IGNORECASE) and line.strip():
            # Found a new section
            current_section = line.strip()
            sections[current_section] = ""
        else:
            # Add content to the current section
            if sections[current_section]:
                sections[current_section] += "\n" + line
            else:
                sections[current_section] = line
    
    # If header is empty, remove it
    if not sections["Header"].strip():
        sections.pop("Header")
    
    # If no sections were found, use the entire text as a single section
    if not sections:
        sections["Main Content"] = text
        
    return sections

def generate_diff_for_sections(original_sections: Dict[str, str], 
                               customized_sections: Dict[str, str]) -> Dict[str, Any]:
    """
    Generate section-by-section diff information.
    
    Args:
        original_sections: Dictionary of original resume sections
        customized_sections: Dictionary of customized resume sections
    
    Returns:
        Dict[str, Any]: A dictionary with diff information for each section
    """
    diff_data = {}
    
    # Handle empty inputs
    if not original_sections and not customized_sections:
        return {"Main Content": {
            "original": "",
            "customized": "",
            "similarity": 1.0,
            "status": "unchanged",
            "change_percentage": 0
        }}
    
    # Get all section names from both dictionaries
    all_sections = set(list(original_sections.keys()) + list(customized_sections.keys()))
    
    for section in all_sections:
        original_content = original_sections.get(section, "")
        customized_content = customized_sections.get(section, "")
        
        # Calculate similarity ratio
        similarity = difflib.SequenceMatcher(None, original_content, customized_content).ratio()
        
        # Determine section status
        if section not in original_sections:
            status = "added"
        elif section not in customized_sections:
            status = "removed"
        elif similarity == 1.0:
            status = "unchanged"
        else:
            status = "modified"
        
        # Store diff information for this section
        diff_data[section] = {
            "original": original_content,
            "customized": customized_content,
            "similarity": similarity,
            "status": status,
            "change_percentage": 0 if similarity == 1.0 else round((1 - similarity) * 100)
        }
    
    return diff_data

def generate_html_diff(original_text: Optional[str], customized_text: Optional[str], context_lines: int = 2) -> str:
    """
    Generate HTML diff between original and customized text with custom styling.
    
    Args:
        original_text: The original text
        customized_text: The customized text
        context_lines: Number of context lines (default: 2)
    
    Returns:
        str: HTML with highlighted differences
    """
    # Handle None values
    original_text = original_text or ""
    customized_text = customized_text or ""
    
    # Check if both texts are empty or identical
    if not original_text and not customized_text:
        return "<p>No content available for comparison.</p>"
    elif original_text == customized_text:
        return f"<p>Both texts are identical.<br><br><pre>{html.escape(original_text)}</pre></p>"
    
    # Split text into lines
    original_lines = original_text.splitlines()
    customized_lines = customized_text.splitlines()
    
    # Create HTML diff
    differ = difflib.HtmlDiff(tabsize=4, wrapcolumn=80)
    diff_html = differ.make_file(original_lines, customized_lines, context=True, numlines=context_lines)
    
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
            font-size: 0.85rem;
        }}
        .diff td {{
            padding: 4px 8px;
            border: 1px solid #ddd;
            vertical-align: top;
            white-space: pre-wrap;
            line-height: 1.4;
        }}
        .diff th {{
            background-color: #f1f5f9;
            padding: 4px 8px;
            border: 1px solid #ddd;
            font-weight: bold;
        }}
        .diff_add {{
            background-color: #d1fae5 !important;
        }}
        .diff_sub {{
            background-color: #fee2e2 !important;
        }}
        .diff_chg {{
            background-color: #fef3c7 !important;
        }}
        </style>
        
        <div style="overflow-x: auto;">
        {table_html}
        </div>
        """
        
        return styled_html
    else:
        # If table extraction fails, return a simple message
        return "<p>Diff generation failed. Please use the side-by-side comparison.</p>"

def get_diff_highlights(original_text: Optional[str], customized_text: Optional[str]) -> Tuple[List[str], List[str]]:
    """
    Get highlighted versions of original and customized text with differences marked.
    
    Args:
        original_text: The original text
        customized_text: The customized text
    
    Returns:
        Tuple[List[str], List[str]]: Tuple of (original_highlighted, customized_highlighted)
        where each is a list of lines with differences highlighted
    """
    # Handle None values
    original_text = original_text or ""
    customized_text = customized_text or ""
    
    # If either text is empty, create a placeholder
    if not original_text:
        return ["<span style='font-style: italic; color: #94a3b8;'>No original content available</span>"], \
               [html.escape(line) for line in customized_text.splitlines()] if customized_text else [""]
    
    if not customized_text:
        return [html.escape(line) for line in original_text.splitlines()], \
               ["<span style='font-style: italic; color: #94a3b8;'>No customized content available</span>"]
    
    # Split text into lines
    original_lines = original_text.splitlines()
    customized_lines = customized_text.splitlines()
    
    # Handle empty lines
    if not original_lines:
        original_lines = [""]
    if not customized_lines:
        customized_lines = [""]
    
    # Use difflib to find differences
    d = difflib.Differ()
    diff = list(d.compare(original_lines, customized_lines))
    
    original_highlighted = []
    customized_highlighted = []
    
    for line in diff:
        if line.startswith('- '):
            # Line in original that's not in customized
            original_highlighted.append(f"<span style='background-color:#fee2e2;'>{html.escape(line[2:])}</span>")
        elif line.startswith('+ '):
            # Line in customized that's not in original
            customized_highlighted.append(f"<span style='background-color:#d1fae5;'>{html.escape(line[2:])}</span>")
        elif line.startswith('  '):
            # Line in both
            original_highlighted.append(html.escape(line[2:]))
            customized_highlighted.append(html.escape(line[2:]))
    
    # Ensure we have at least one item in each list
    if not original_highlighted:
        original_highlighted = ["<span style='font-style: italic; color: #94a3b8;'>No matching content</span>"]
    if not customized_highlighted:
        customized_highlighted = ["<span style='font-style: italic; color: #94a3b8;'>No matching content</span>"]
    
    return original_highlighted, customized_highlighted

def highlight_added_removed_content(original_text: Optional[str], customized_text: Optional[str]) -> Tuple[str, str]:
    """
    Generate inline highlighted versions showing added/removed content.
    
    Args:
        original_text: The original text
        customized_text: The customized text
    
    Returns:
        Tuple[str, str]: (highlighted_original, highlighted_customized)
    """
    # Get highlighted lines
    original_highlighted, customized_highlighted = get_diff_highlights(original_text, customized_text)
    
    # Join lines back into text
    highlighted_original = "<br>".join(original_highlighted)
    highlighted_customized = "<br>".join(customized_highlighted)
    
    return highlighted_original, highlighted_customized

def extract_key_changes(diff_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Extract key changes from diff data in a user-friendly format.
    
    Args:
        diff_data: The diff data generated by generate_diff_for_sections
    
    Returns:
        Dict[str, List[str]]: Dictionary of change categories and descriptions
    """
    # Handle empty diff_data
    if not diff_data:
        return {
            "sections_added": [],
            "sections_modified": [],
            "sections_removed": [],
            "content_changes": ["No changes detected"]
        }
    
    changes = {
        "sections_added": [],
        "sections_modified": [],
        "sections_removed": [],
        "content_changes": []
    }
    
    for section, data in diff_data.items():
        # Skip processing if required keys are missing
        if not all(key in data for key in ["status", "original", "customized", "change_percentage"]):
            continue
            
        # Track section additions/removals/modifications
        if data["status"] == "added":
            changes["sections_added"].append(section)
        elif data["status"] == "removed":
            changes["sections_removed"].append(section)
        elif data["status"] == "modified":
            # Only include significantly modified sections (> 5% change)
            if data["change_percentage"] > 5:
                changes["sections_modified"].append(
                    f"{section} ({data['change_percentage']}% change)"
                )
                
                # Attempt to identify specific content changes
                if len(data["original"]) > 0 and len(data["customized"]) > 0:
                    # Use difflib to identify specific additions
                    s = difflib.SequenceMatcher(None, data["original"], data["customized"])
                    for tag, i1, i2, j1, j2 in s.get_opcodes():
                        if tag == 'insert' or tag == 'replace':
                            # Extract added content
                            added_text = data["customized"][j1:j2].strip()
                            # Only include non-trivial additions (longer than 10 chars)
                            if len(added_text) > 10:
                                # Truncate long additions
                                if len(added_text) > 100:
                                    added_text = added_text[:100] + "..."
                                changes["content_changes"].append(
                                    f"Added to {section}: \"{added_text}\""
                                )
    
    return changes
