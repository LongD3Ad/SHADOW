# --- START OF FILE response_handler.py (Modified) ---

import logging
from src.data_processing.chunk_and_annotate import get_chunk_context

# Define the response generation similarity threshold
RESPONSE_SIMILARITY_THRESHOLD = 0.35 # You might adjust this later based on testing

# RENAME THE FUNCTION HERE
def generate_standard_response(query, chunks):
    """
    Generate a standard structured response based purely on retrieved chunks and similarity.
    Used as a fallback when no specific framework rules apply or style guide fails.
    """
    # Keep the rest of the function logic exactly the same as your active version
    logging.info(f"Generating standard response from {len(chunks)} accessible chunks. Response threshold: {RESPONSE_SIMILARITY_THRESHOLD}")

    if not chunks:
        logging.warning("generate_standard_response called with zero chunks.")
        return "No relevant information could be accessed or retrieved.", "No sources."

    # Sort chunks by similarity (highest first)
    chunks.sort(key=lambda x: x.get("similarity", 0), reverse=True)

    # Prepare response sections
    response_parts = []
    source_explanations = [] # Store explanation parts separately

    # Extract and organize relevant information
    for i, chunk in enumerate(chunks):
        text = chunk.get("text", "Missing text")
        metadata = chunk.get("metadata", {})
        similarity = chunk.get("similarity", 0)
        context = get_chunk_context(chunk) # Generate context string
        similarity_percent = f"{similarity * 100:.1f}%"

        # Add to source explanation regardless of threshold (up to a limit)
        if i < 5: # Explain top 5 sources found & filtered
            source_explanations.append(f"{i+1}. {context} (Retrieved Relevance: {similarity_percent})")

        # Add text to response ONLY if above the specific response threshold
        if similarity >= RESPONSE_SIMILARITY_THRESHOLD:
            logging.debug(f"Adding chunk {i} (Similarity: {similarity_percent}) to standard response.")
            response_parts.append(text) # Keep it simple for now

    # Combine response parts into a coherent response
    if response_parts:
        full_response = "\n\n---\n\n".join(response_parts) # Use separator
    else:
        # Check if chunks exist at all before trying to access index 0
        highest_sim_info = f"Highest similarity was {chunks[0].get('similarity', 0):.4f}." if chunks else "No chunks were provided."
        logging.warning(f"No chunks met the standard response similarity threshold of {RESPONSE_SIMILARITY_THRESHOLD}. {highest_sim_info}")
        full_response = "Based on the available information and relevance thresholds, I cannot provide a specific answer. Relevant sections might exist but require higher relevance scores or clearance."

    # Generate final explanation string
    if source_explanations:
        explanation = "Information retrieval process details:\n" + "\n".join(source_explanations)
        if not response_parts:
            explanation += f"\n\nNote: No retrieved sections met the required response relevance threshold ({RESPONSE_SIMILARITY_THRESHOLD * 100:.0f}%)."
    else:
        explanation = "No information sources could be identified or accessed for this query."


    return full_response, explanation

# --- END OF FILE response_handler.py ---