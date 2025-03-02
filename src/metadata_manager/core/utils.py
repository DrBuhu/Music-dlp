def string_similarity(s1: str, s2: str) -> float:
    """Calculate similarity between two strings."""
    # Normalize strings
    s1 = s1.lower().strip()
    s2 = s2.lower().strip()
    
    # Direct comparison
    if s1 == s2:
        return 100.0
    
    # Substring match
    if s1 in s2 or s2 in s1:
        return 75.0
        
    # Word comparison
    words1 = set(s1.split())
    words2 = set(s2.split())
    common_words = words1.intersection(words2)
    
    if not words1 or not words2:
        return 0.0
        
    # Calculate Jaccard similarity
    similarity = len(common_words) / len(words1.union(words2))
    return similarity * 100.0
