# --- START OF FILE src/retrieval/vector_search.py ---

import numpy as np
import logging
from src.retrieval.embedding_engine import get_query_embedding

# ======================================================================
# DEFINE THE COSINE SIMILARITY FUNCTION *FIRST*
# ======================================================================
def cosine_similarity(vec1, vec2):
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1 (np.ndarray): First vector
        vec2 (np.ndarray): Second vector

    Returns:
        float: Cosine similarity score
    """
    # Ensure inputs are numpy arrays
    vec1 = np.asarray(vec1, dtype=np.float32)
    vec2 = np.asarray(vec2, dtype=np.float32)

    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    # Check for zero vectors
    if norm1 == 0 or norm2 == 0:
        # logging.debug("Zero vector encountered in cosine similarity calculation.") # Optional debug log
        return 0.0  # Return float

    similarity = dot_product / (norm1 * norm2)

    # Clamp similarity to range [-1, 1] due to potential floating point inaccuracies
    # Although cosine similarity is mathematically [-1, 1], floats can sometimes slightly exceed this.
    similarity = np.clip(similarity, -1.0, 1.0)

    return similarity

# ======================================================================
# DEFINE THE SEARCH FUNCTION *AFTER* COSINE SIMILARITY
# ======================================================================
def search_similar_chunks(query, chunks, chunk_embeddings, top_k=5, similarity_threshold=0.2):
    """
    Search for chunks similar to the query using vector similarity.

    Args:
        query (str): The query text
        chunks (list): List of document chunks
        chunk_embeddings (list): List of embedding vectors for chunks
        top_k (int): Number of top results to return
        similarity_threshold (float): Minimum similarity score threshold

    Returns:
        list: List of relevant chunks with similarity scores
    """
    logging.info(f"Searching top {top_k} chunks with threshold > {similarity_threshold}")

    # Initialize results list - THIS IS IMPORTANT
    results = []

    # Get embedding for the query
    try:
        query_embedding = get_query_embedding(query)
        if query_embedding is None or query_embedding.size == 0:
            logging.error("Failed to generate query embedding.")
            return results # Return empty list
    except Exception as e:
        logging.error(f"Error getting query embedding: {e}", exc_info=True)
        return results # Return empty list

    # Check if chunk embeddings are available
    if not chunk_embeddings:
        logging.error("Chunk embeddings list is empty.")
        return results # Return empty list

    # Calculate similarity scores
    similarities = []
    for i, chunk_embedding in enumerate(chunk_embeddings):
        # Ensure chunk_embedding is valid
        if not isinstance(chunk_embedding, np.ndarray) or chunk_embedding.size == 0:
             logging.warning(f"Skipping invalid or empty embedding at index {i}")
             similarities.append((i, 0.0)) # Assign 0 similarity for invalid embedding
             continue

        try:
             # Make the call to the function defined above
             similarity = cosine_similarity(query_embedding, chunk_embedding)
             similarities.append((i, similarity))
        except Exception as e:
             # Log the specific exception
             logging.error(f"Error calculating similarity for chunk {i}: {e}", exc_info=True)
             similarities.append((i, 0.0)) # Assign 0 similarity on error

    # Sort by similarity score (descending)
    similarities.sort(key=lambda x: x[1], reverse=True)

    # Debug log: Show top scores before filtering
    logging.debug("Top similarity scores before threshold:")
    for idx, sim in similarities[:max(top_k, 10)]:
        logging.debug(f"  Index {idx}: {sim:.4f}")

    # Filter results by threshold and take top_k
    for i, similarity in similarities:
        # Stop if we already have enough results
        if len(results) >= top_k:
             logging.debug(f"Reached top_k limit ({top_k}). Stopping search.")
             break

        # Check if similarity meets threshold
        if similarity >= similarity_threshold:
            # Ensure index is valid before accessing chunks list
            if i < len(chunks):
                try:
                    chunk = chunks[i].copy() # Use copy to avoid modifying original data
                    chunk["similarity"] = similarity # Add similarity score to the chunk dict
                    results.append(chunk)
                except IndexError:
                     logging.warning(f"IndexError: Attempted to access chunk at invalid index {i} (list length {len(chunks)}).")
                except Exception as e:
                     logging.error(f"Error processing chunk {i} after meeting threshold: {e}", exc_info=True)
            else:
                 logging.warning(f"Similarity score found for invalid chunk index {i} (list length {len(chunks)}).")
        # Optional: Log if a chunk is skipped due to threshold
        # else:
        #    logging.debug(f"Chunk {i} similarity {similarity:.4f} below threshold {similarity_threshold}. Skipping.")

    logging.info(f"Found {len(results)} relevant chunks meeting threshold {similarity_threshold} for query: {query[:50]}...")
    return results

# --- END OF FILE src/retrieval/vector_search.py ---