"""
Keyword extraction utilities for job descriptions.

This module provides functions to extract important keywords and phrases
from job descriptions to help with optimization.
"""

import re
from typing import List, Dict, Set, Any, Optional
import logging
from collections import Counter

# Set up logger
logger = logging.getLogger(__name__)

# Common tech skill keywords to look for
COMMON_TECH_SKILLS = {
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "php", "go", "rust",
    "html", "css", "react", "angular", "vue", "node.js", "django", "flask", "spring",
    "aws", "azure", "gcp", "cloud", "docker", "kubernetes", "terraform", "ci/cd",
    "git", "github", "gitlab", "bitbucket", "agile", "scrum", "kanban", "jira",
    "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "firebase", 
    "rest", "graphql", "api", "microservices", "serverless", "linux", "unix", "bash",
    "machine learning", "deep learning", "ai", "artificial intelligence", "data science",
    "data engineering", "etl", "big data", "hadoop", "spark", "tableau", "power bi",
    "excel", "vba", "powerpoint", "word", "project management", "product management"
}

# Common soft skills keywords
COMMON_SOFT_SKILLS = {
    "communication", "teamwork", "collaboration", "leadership", "problem solving",
    "critical thinking", "decision making", "time management", "organization",
    "adaptability", "flexibility", "creativity", "innovation", "initiative",
    "attention to detail", "analytical", "interpersonal", "presentation", "verbal",
    "written", "customer service", "client facing", "negotiation", "conflict resolution",
    "mentoring", "coaching", "self-motivated", "self-starter", "independent", "proactive"
}

# Stop words to filter out
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "when", "where", "how", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "to", "at", "by", "for", "with",
    "about", "against", "between", "into", "through", "during", "before", "after",
    "above", "below", "from", "up", "down", "in", "out", "on", "off", "over", "under",
    "again", "further", "then", "once", "here", "there", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can",
    "will", "just", "should", "now", "i", "we", "our", "ours", "you", "your", "yours",
    "he", "she", "his", "her", "hers", "its", "they", "them", "their", "theirs"
}

def extract_keywords(text: str, max_keywords: int = 20) -> Dict[str, List[str]]:
    """
    Extract important keywords from a job description.
    
    Args:
        text: The job description text
        max_keywords: Maximum number of keywords to extract
        
    Returns:
        dict: Dictionary with categorized keywords
    """
    if not text:
        return {
            "technical_skills": [],
            "soft_skills": [],
            "education": [],
            "experience": [],
            "other": []
        }
    
    # Normalize text
    text_lower = text.lower()
    
    # Find technical skills
    tech_skills = find_matching_keywords(text_lower, COMMON_TECH_SKILLS)
    
    # Find soft skills
    soft_skills = find_matching_keywords(text_lower, COMMON_SOFT_SKILLS)
    
    # Find education requirements
    education = extract_education(text_lower)
    
    # Find experience requirements
    experience = extract_experience(text_lower)
    
    # Find other potentially important n-grams
    other_keywords = extract_ngrams(text_lower, exclude=tech_skills | soft_skills | set(education) | set(experience))
    
    # Limit the number of keywords in each category
    return {
        "technical_skills": list(tech_skills)[:max_keywords // 2],
        "soft_skills": list(soft_skills)[:max_keywords // 4],
        "education": education[:max_keywords // 4],
        "experience": experience[:max_keywords // 4],
        "other": other_keywords[:max_keywords // 4]
    }

def find_matching_keywords(text: str, keyword_set: Set[str]) -> Set[str]:
    """
    Find keywords in text that match a given set of keywords.
    
    Args:
        text: The text to search in
        keyword_set: Set of keywords to search for
        
    Returns:
        set: Matching keywords found in the text
    """
    found_keywords = set()
    
    for keyword in keyword_set:
        # Look for the keyword with word boundaries
        if re.search(r'\b' + re.escape(keyword) + r'\b', text):
            found_keywords.add(keyword)
    
    return found_keywords

def extract_education(text: str) -> List[str]:
    """
    Extract education requirements from job description.
    
    Args:
        text: The job description text
        
    Returns:
        list: Extracted education requirements
    """
    education = []
    
    # Common education pattern matches
    patterns = [
        r'\b(bachelor|master|phd|doctorate|bs|ms|ba|ma|mba)\s+(?:degree|in|of)\s+([a-z\s]+)',
        r'\b([a-z\s]+)\s+degree\b',
        r'\b(high school|associate\'s|bachelor\'s|master\'s|doctoral)\s+degree\b'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                education.append(' '.join(match).strip())
            else:
                education.append(match.strip())
    
    return education

def extract_experience(text: str) -> List[str]:
    """
    Extract experience requirements from job description.
    
    Args:
        text: The job description text
        
    Returns:
        list: Extracted experience requirements
    """
    experience = []
    
    # Common experience pattern matches
    patterns = [
        r'\b(\d+)\+?\s+years?\s+(?:of\s+)?experience\s+(?:in|with)?\s+([a-z\s]+)',
        r'\bexperience\s+(?:in|with)\s+([a-z\s]+)',
        r'\b(\d+)\+?\s+years?\s+(?:of\s+)?([a-z\s]+)\s+experience\b'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                experience.append(' '.join(match).strip())
            else:
                experience.append(match.strip())
    
    return experience

def extract_ngrams(text: str, n: int = 2, min_freq: int = 2, exclude: Set[str] = None) -> List[str]:
    """
    Extract important n-grams from text.
    
    Args:
        text: The text to extract from
        n: The n-gram size
        min_freq: Minimum frequency to consider
        exclude: Set of phrases to exclude
        
    Returns:
        list: Important n-grams
    """
    if exclude is None:
        exclude = set()
    
    # Tokenize the text
    tokens = re.findall(r'\b\w+\b', text)
    tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 1]
    
    # Extract n-grams
    ngrams = []
    for i in range(len(tokens) - n + 1):
        ngram = ' '.join(tokens[i:i+n])
        if ngram not in exclude:
            ngrams.append(ngram)
    
    # Count frequencies
    ngram_counts = Counter(ngrams)
    
    # Filter by minimum frequency
    filtered_ngrams = [ngram for ngram, count in ngram_counts.items() if count >= min_freq]
    
    return filtered_ngrams
