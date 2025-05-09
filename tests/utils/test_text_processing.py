"""
Tests for text processing utilities.

These tests verify the functionality of the text processing utilities
used for sanitizing job descriptions to prevent JSON parsing errors.
"""

import pytest
import json
import re
from streamlit_app.utils.text_processing.sanitizer import (
    sanitize_text,
    remove_non_printable_chars,
    escape_json_characters,
    test_json_serialization,
    clean_pasted_html
)
from streamlit_app.utils.text_processing.validator import validate_job_description


class TestTextSanitization:
    """Tests for text sanitization functions."""
    
    def test_remove_non_printable_chars(self):
        """Test removing non-printable characters."""
        # Test with control characters
        text_with_control = "Hello\x00World\x1F"
        assert remove_non_printable_chars(text_with_control) == "HelloWorld"
        
        # Test with null bytes
        text_with_null = "Test\x00with\x00null"
        assert remove_non_printable_chars(text_with_null) == "Testwithnull"
        
        # Test with zero-width characters
        text_with_zero_width = "Zero\u200bwidth"
        assert remove_non_printable_chars(text_with_zero_width) == "Zerowidth"
        
        # Test with normal text
        normal_text = "This is normal text."
        assert remove_non_printable_chars(normal_text) == normal_text
    
    def test_sanitize_text(self):
        """Test sanitizing text."""
        # Test with multiple newlines
        text_with_newlines = "Line 1\n\n\n\nLine 2"
        assert sanitize_text(text_with_newlines) == "Line 1\n\nLine 2"
        
        # Test with multiple spaces
        text_with_spaces = "Too    many    spaces"
        assert sanitize_text(text_with_spaces) == "Too many spaces"
        
        # Test with tabs
        text_with_tabs = "Column1\tColumn2\tColumn3"
        assert sanitize_text(text_with_tabs) == "Column1 Column2 Column3"
        
        # Test with carriage returns
        text_with_cr = "Line 1\rLine 2"
        assert sanitize_text(text_with_cr) == "Line 1\nLine 2"
        
        # Test with bullet points
        text_with_bullets = "•Item 1\n•Item 2\n•Item 3"
        assert sanitize_text(text_with_bullets) == "-Item 1\n-Item 2\n-Item 3"
        
        # Test with fancy quotes
        text_with_quotes = ""Quoted text" and 'single quotes'"
        assert sanitize_text(text_with_quotes) == '"Quoted text" and \'single quotes\''
        
        # Test with em dashes
        text_with_em_dash = "Word—word"
        assert sanitize_text(text_with_em_dash) == "Word-word"
        
        # Test preserving/not preserving newlines
        text_with_newlines = "Line 1\nLine 2\nLine 3"
        assert sanitize_text(text_with_newlines, preserve_newlines=True) == text_with_newlines
        assert sanitize_text(text_with_newlines, preserve_newlines=False) == "Line 1 Line 2 Line 3"
    
    def test_escape_json_characters(self):
        """Test escaping JSON special characters."""
        # Test with backslashes
        text_with_backslash = r"Path: C:\Users\username"
        escaped = escape_json_characters(text_with_backslash)
        assert "\\\\" in escaped  # Double backslash in the escaped string
        
        # Test with quotes
        text_with_quotes = 'He said "hello" to everyone'
        escaped = escape_json_characters(text_with_quotes)
        assert '\\"hello\\"' in escaped  # Escaped quotes
        
        # Test with newlines
        text_with_newlines = "Line 1\nLine 2"
        escaped = escape_json_characters(text_with_newlines)
        assert "\\n" in escaped  # Escaped newline
        
        # Test with tabs
        text_with_tabs = "Column1\tColumn2"
        escaped = escape_json_characters(text_with_tabs)
        assert "\\t" not in escaped  # Tab should be converted to space during sanitization
        
        # Test that the escaped text can be serialized to JSON
        for test_text in [
            text_with_backslash,
            text_with_quotes,
            text_with_newlines,
            text_with_tabs
        ]:
            escaped = escape_json_characters(test_text)
            # Verify it can be serialized and deserialized
            obj = {"text": escaped}
            json_str = json.dumps(obj)
            parsed = json.loads(json_str)
            assert "text" in parsed
    
    def test_json_serialization(self):
        """Test JSON serialization test function."""
        # Test with valid text
        valid_text = "This is valid text."
        result = test_json_serialization(valid_text)
        assert result["is_valid"] is True
        assert result["error"] is None
        
        # Test with invalid text (contains control characters)
        invalid_text = "Invalid\x00text"
        result = test_json_serialization(invalid_text)
        assert result["is_valid"] is False
        assert result["error"] is not None
    
    def test_clean_pasted_html(self):
        """Test cleaning pasted HTML content."""
        # Test with HTML tags
        html_text = "<p>This is <strong>bold</strong> text.</p>"
        assert clean_pasted_html(html_text) == "This is bold text."
        
        # Test with HTML entities
        html_with_entities = "This &amp; that &lt; this &gt; that"
        assert clean_pasted_html(html_with_entities) == "This & that < this > that"
        
        # Test with complex HTML
        complex_html = """
        <div class="job-description">
            <h2>Job Requirements</h2>
            <ul>
                <li>5+ years of experience</li>
                <li>Bachelor's degree</li>
                <li>Proficient in Python</li>
            </ul>
        </div>
        """
        cleaned = clean_pasted_html(complex_html)
        assert "<" not in cleaned
        assert ">" not in cleaned
        assert "Job Requirements" in cleaned
        assert "5+ years of experience" in cleaned


class TestJobDescriptionValidation:
    """Tests for job description validation."""
    
    def test_validation_length_checks(self):
        """Test validation of job description length."""
        # Test with empty text
        empty_text = ""
        result = validate_job_description(empty_text)
        assert result["is_valid"] is False
        assert any("empty" in error.lower() for error in result["errors"])
        
        # Test with text that's too short
        short_text = "Too short."
        result = validate_job_description(short_text)
        assert result["is_valid"] is False
        assert any("too short" in error.lower() for error in result["errors"])
        
        # Test with text that's the minimum length but below recommended
        min_text = "A" * 50
        result = validate_job_description(min_text)
        assert result["is_valid"] is True
        assert any("quite short" in warning.lower() for warning in result["warnings"])
        
        # Test with text that's good length
        good_text = "A" * 500
        result = validate_job_description(good_text)
        assert result["is_valid"] is True
        assert not any("short" in warning.lower() for warning in result["warnings"])
        
        # Test with text that's too long
        long_text = "A" * 11000
        result = validate_job_description(long_text)
        assert result["is_valid"] is False
        assert any("too long" in error.lower() for error in result["errors"])
    
    def test_validation_character_distribution(self):
        """Test validation of character distribution."""
        # Test with unusual character distribution (too many special chars)
        special_chars_text = "$#@!*&^%$" * 50
        result = validate_job_description(special_chars_text)
        assert result["is_valid"] is True  # Still valid but has warnings
        assert any("unusual distribution" in warning.lower() for warning in result["warnings"])
        
        # Test with unusual character distribution (too much uppercase)
        uppercase_text = "UPPERCASE TEXT " * 50
        result = validate_job_description(uppercase_text)
        assert result["is_valid"] is True  # Still valid but has warnings
        assert any("unusual distribution" in warning.lower() for warning in result["warnings"])
    
    def test_validation_section_detection(self):
        """Test detection of required sections."""
        # Test job description with all required sections
        complete_job_desc = """
        About Us:
        Our company is great.
        
        Responsibilities:
        Do great work.
        
        Requirements:
        Be great.
        
        Benefits:
        Great perks.
        """
        result = validate_job_description(complete_job_desc)
        assert result["is_valid"] is True
        sections = [section for section in ["responsibilities", "requirements", "company_info", "benefits"]
                   if section not in result.get("missing_sections", [])]
        assert len(sections) == 4
        
        # Test job description missing sections
        incomplete_job_desc = """
        About Us:
        Our company is great.
        
        Requirements:
        Be great.
        """
        result = validate_job_description(incomplete_job_desc)
        assert result["is_valid"] is True  # Still valid but has warnings
        assert any("missing" in warning.lower() for warning in result["warnings"])


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
