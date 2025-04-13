import numpy as np
from sentence_transformers import SentenceTransformer

# Global model instance
_model = None

def get_model():
    """
    Initialize and return the embedding model (lazy loading).
    
    Returns:
        SentenceTransformer: The embedding model
    """
    global _model
    if _model is None:
        # Using a smaller model suitable for deployment
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def get_embeddings(chunks):
    """
    Generate embeddings for document chunks.
    
    Args:
        chunks (list): List of document chunks
        
    Returns:
        list: List of embedding vectors corresponding to chunks
    """
    model = get_model()
    texts = [chunk["text"] for chunk in chunks]
    
    # Generate embeddings in batches to avoid memory issues
    embeddings = []
    batch_size = 16
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        batch_embeddings = model.encode(batch_texts)
        embeddings.extend(batch_embeddings)
    
    print(f"Generated {len(embeddings)} embeddings")
    return embeddings

def get_query_embedding(query):
    """
    Generate embedding for a query.
    
    Args:
        query (str): The query text
        
    Returns:
        np.ndarray: The embedding vector
    """
    model = get_model()
    return model.encode(query)