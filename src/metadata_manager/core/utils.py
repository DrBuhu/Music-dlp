"""Utility functions."""
from difflib import SequenceMatcher

def string_similarity(str1: str, str2: str) -> float:
    """Calculate similarity ratio between two strings."""
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio() * 100
