"""
Utility functions for Legal AI
"""

import json
from typing import List, Dict, Any
from pathlib import Path


def load_json_file(filepath: str) -> List[Dict[str, Any]]:
    """
    Load JSON file and return contents
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        List of dictionaries from JSON file
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: List[Dict[str, Any]], filepath: str):
    """
    Save data to JSON file
    
    Args:
        data: List of dictionaries to save
        filepath: Path to save JSON file
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        
    return chunks


def format_legal_section(section_data: Dict[str, Any], act_name: str = "") -> str:
    """
    Format a legal section for display or embedding
    
    Args:
        section_data: Dictionary containing section information
        act_name: Name of the act (IPC, CrPC, etc.)
        
    Returns:
        Formatted string representation
    """
    parts = []
    
    if act_name:
        parts.append(f"Act: {act_name}")
    
    if 'Section' in section_data:
        parts.append(f"Section: {section_data['Section']}")
    elif 'article' in section_data:
        parts.append(f"Article: {section_data['article']}")
    
    if 'section_title' in section_data:
        parts.append(f"Title: {section_data['section_title']}")
    elif 'title' in section_data:
        parts.append(f"Title: {section_data['title']}")
    
    if 'Offense' in section_data:
        parts.append(f"Offense: {section_data['Offense']}")
    
    if 'Punishment' in section_data:
        parts.append(f"Punishment: {section_data['Punishment']}")
    
    if 'section_desc' in section_data:
        parts.append(f"Description: {section_data['section_desc']}")
    elif 'Description' in section_data:
        parts.append(f"Description: {section_data['Description']}")
    elif 'description' in section_data:
        parts.append(f"Description: {section_data['description']}")
    
    return "\n".join(parts)


def extract_section_number(section_string: str) -> str:
    """
    Extract section number from various formats
    
    Args:
        section_string: Section identifier string
        
    Returns:
        Cleaned section number
    """
    section_string = section_string.replace("IPC_", "").replace("Section ", "")
    return section_string.strip()


def merge_duplicate_sections(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate sections based on section number
    
    Args:
        sections: List of section dictionaries
        
    Returns:
        List with duplicates removed
    """
    seen = set()
    unique_sections = []
    
    for section in sections:
        section_id = section.get('Section') or section.get('article')
        if section_id and section_id not in seen:
            seen.add(section_id)
            unique_sections.append(section)
    
    return unique_sections
