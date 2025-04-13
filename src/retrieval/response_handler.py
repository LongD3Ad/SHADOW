# from src.data_processing.chunk_and_annotate import get_chunk_context

# def generate_response(query, chunks):
#     """
#     Generate a structured response based on retrieved chunks.
    
#     Args:
#         query (str): The original query
#         chunks (list): List of relevant chunks
        
#     Returns:
#         tuple: (response, explanation)
#             - response (str): Formatted response to the query
#             - explanation (str): Explanation of sources and retrieval process
#     """
#     # Sort chunks by similarity (highest first)
#     chunks.sort(key=lambda x: x.get("similarity", 0), reverse=True)
    
#     # Prepare response sections
#     response_parts = []
    
#     # Extract and organize relevant information
#     for chunk in chunks:
#         # Extract key information from the chunk text
#         text = chunk["text"]
#         metadata = chunk["metadata"]
#         similarity = chunk.get("similarity", 0)
        
#         # Add this information to the response
#         if similarity > 0.7:  # High relevance
#             response_parts.append(text)
    
#     # Combine response parts into a coherent response
#     if response_parts:
#         full_response = "\n\n".join(response_parts)
#     else:
#         # Fallback if no high-relevance parts
#         full_response = "Based on the available information, I cannot provide a specific answer to your query."
    
#     # Generate explanation of sources
#     explanation = "Information was retrieved from the following sources:\n\n"
#     for i, chunk in enumerate(chunks[:3], 1):  # Show top 3 sources
#         context = get_chunk_context(chunk)
#         similarity = chunk.get("similarity", 0)
#         similarity_percent = f"{similarity * 100:.1f}%"
#         explanation += f"{i}. {context} (Relevance: {similarity_percent})\n"
    
#     return full_response, explanation


# --- START OF FILE response_handler.py ---

import logging
from src.data_processing.chunk_and_annotate import get_chunk_context

# Define the response generation similarity threshold
RESPONSE_SIMILARITY_THRESHOLD = 0.5 # Lowered threshold

def generate_response(query, chunks):
    """
    Generate a structured response based on retrieved chunks.
    """
    logging.info(f"Generating response from {len(chunks)} accessible chunks. Response threshold: {RESPONSE_SIMILARITY_THRESHOLD}")

    if not chunks:
         logging.warning("generate_response called with zero chunks.")
         return "No relevant information could be accessed or retrieved.", "No sources."


    # Sort chunks by similarity (highest first) - assuming they come sorted from search, but doesn't hurt to re-sort
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
            logging.debug(f"Adding chunk {i} (Similarity: {similarity_percent}) to response.")
            # Maybe add context to the response part itself?
            # response_parts.append(f"From {metadata.get('source', 'N/A')} (Section: {metadata.get('section', 'N/A')}):\n{text}")
            response_parts.append(text) # Keep it simple for now

    # Combine response parts into a coherent response
    if response_parts:
        full_response = "\n\n---\n\n".join(response_parts) # Use separator
    else:
        logging.warning(f"No chunks met the response similarity threshold of {RESPONSE_SIMILARITY_THRESHOLD}. Highest similarity was {chunks[0].get('similarity', 0):.4f} if chunks exist.")
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