def filter_by_clearance(chunks, user_clearance_level):
    """
    Filter chunks based on user's clearance level.
    
    Args:
        chunks (list): List of document chunks with metadata
        user_clearance_level (int): User's clearance level (1, 2, or 3)
        
    Returns:
        tuple: (accessible_chunks, is_access_denied)
            - accessible_chunks (list): Chunks the user can access
            - is_access_denied (bool): True if any chunks were filtered due to insufficient clearance
    """
    accessible_chunks = []
    is_access_denied = False
    
    for chunk in chunks:
        # Get chunk security level, default to 1 if not specified
        chunk_security_level = chunk["metadata"].get("security_level", 1)
        
        # Only include chunks with security level <= user's clearance level
        if chunk_security_level <= user_clearance_level:
            accessible_chunks.append(chunk)
        else:
            is_access_denied = True
    
    print(f"Filtered {len(chunks) - len(accessible_chunks)} chunks due to security level")
    
    return accessible_chunks, is_access_denied