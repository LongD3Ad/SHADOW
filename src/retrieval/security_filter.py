# --- security_filter.py (with added logging) ---
import logging # Add import
logger = logging.getLogger(__name__) # Get logger

def filter_by_clearance(chunks, user_clearance_level):
    """
    Filter chunks based on user's clearance level.

    Args:
        chunks (list): List of document chunks with metadata
        user_clearance_level (int): User's clearance level (1, 2, or 3+)

    Returns:
        tuple: (accessible_chunks, is_access_denied)
            - accessible_chunks (list): Chunks the user can access
            - is_access_denied (bool): True if any chunks were filtered due to insufficient clearance
    """
    accessible_chunks = []
    is_access_denied = False
    filtered_count = 0 # Counter for logging

    if not chunks:
         logger.debug("filter_by_clearance received empty chunk list.")
         return [], False

    logger.debug(f"Filtering {len(chunks)} chunks for user level {user_clearance_level}...")

    for i, chunk in enumerate(chunks):
        # Get chunk security level, default to 1 if not specified
        # Make default 0 for safety if type isn't classified? No, default 1 is safer.
        chunk_security_level = chunk.get("metadata", {}).get("security_level", 1) # Safer get

        # Log the comparison being made for THIS chunk
        logger.debug(f"  Chunk {i}: Assigned Level={chunk_security_level}, User Level={user_clearance_level}. Accessible: {chunk_security_level <= user_clearance_level}")

        # Only include chunks with security level <= user's clearance level
        if chunk_security_level <= user_clearance_level:
            accessible_chunks.append(chunk)
        else:
            # This chunk is being filtered out
            is_access_denied = True
            filtered_count += 1
            logger.debug(f"    -> Filtering chunk {i} (Level {chunk_security_level} > {user_clearance_level})")

    # Use logger instead of print
    logger.info(f"Filtered {filtered_count} out of {len(chunks)} chunks due to security level.")

    return accessible_chunks, is_access_denied