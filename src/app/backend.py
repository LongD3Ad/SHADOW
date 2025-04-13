# import os
# from src.data_processing.ingest_documents import load_documents
# from src.data_processing.chunk_and_annotate import create_chunks
# from src.retrieval.embedding_engine import get_embeddings
# from src.retrieval.vector_search import search_similar_chunks
# from src.retrieval.security_filter import filter_by_clearance
# from src.retrieval.response_handler import generate_response

# # Global variables to store processed data
# document_chunks = []
# chunk_embeddings = []
# initialized = False

# def initialize_system():
#     """
#     Initialize the system by loading documents, creating chunks, and generating embeddings.
#     This is done once and cached for subsequent queries.
#     """
#     global document_chunks, chunk_embeddings, initialized
    
#     if not initialized:
#         # Ensure data directories exist
#         data_dir = os.path.join(os.getcwd(), "data")
#         if not os.path.exists(data_dir):
#             # Just create the directory if it doesn't exist
#             os.makedirs(data_dir, exist_ok=True)
#             return False
        
#         # Check if document files exist
#         secret_manual_path = os.path.join(data_dir, "Secret_Info_Manual.txt")
#         response_framework_path = os.path.join(data_dir, "Response_Framework.txt")
        
#         if not os.path.exists(secret_manual_path) or not os.path.exists(response_framework_path):
#             print(f"Warning: Required documents not found at {secret_manual_path} or {response_framework_path}")
#             return False
        
#         try:
#             # Load documents
#             documents = load_documents(
#                 secret_manual_path=secret_manual_path,
#                 response_framework_path=response_framework_path
#             )
            
#             # Create chunks from documents
#             document_chunks = create_chunks(documents)
            
#             # Generate embeddings for chunks
#             chunk_embeddings = get_embeddings(document_chunks)
            
#             initialized = True
#             return True
#         except Exception as e:
#             print(f"Error during initialization: {str(e)}")
#             return False
    
#     return True

# def process_query(query, agent_level):
#     """
#     Process a user query and return relevant information based on agent level.
    
#     Args:
#         query (str): The user's query text
#         agent_level (str): The selected agent clearance level
        
#     Returns:
#         tuple: (response, explanation, status)
#             - response (str): The formatted response to the query
#             - explanation (str): Explanation of sources and retrieval process
#             - status (str): Status of the query processing ('success', 'access_denied', 'no_results', 'error')
#     """
#     if not query.strip():
#         return "", "Please enter a valid query.", "error"
    
#     try:
#         # Initialize system if not already done
#         if not initialize_system():
#             return "", "System initialization failed. Document files may be missing.", "error"
        
#         # Convert agent level string to numeric value
#         level_mapping = {
#             "Level 1 (Low)": 1,
#             "Level 2 (Medium)": 2,
#             "Level 3 (High)": 3
#         }
#         numeric_level = level_mapping.get(agent_level, 1)
        
#         # Handle the case where documents aren't loaded properly
#         if not document_chunks or not chunk_embeddings:
#             return "", "No document data available. Please check document files.", "error"
        
#         # Search for relevant chunks
#         relevant_chunks = search_similar_chunks(query, document_chunks, chunk_embeddings)
        
#         if not relevant_chunks:
#             return "", "", "no_results"
        
#         # Filter chunks based on clearance level
#         accessible_chunks, is_access_denied = filter_by_clearance(relevant_chunks, numeric_level)
        
#         if is_access_denied:
#             return "", "", "access_denied"
        
#         if not accessible_chunks:
#             return "", "", "no_results"
        
#         # Generate response from accessible chunks
#         response, explanation = generate_response(query, accessible_chunks)
        
#         return response, explanation, "success"
        
#     except Exception as e:
#         import traceback
#         print(f"Error processing query: {str(e)}")
#         print(traceback.format_exc())
#         return "", f"An error occurred: {str(e)}", "error"


# --- START OF FILE backend.py ---

import os
import logging
from src.data_processing.ingest_documents import load_documents
from src.data_processing.chunk_and_annotate import create_chunks
from src.retrieval.embedding_engine import get_embeddings
from src.retrieval.vector_search import search_similar_chunks
from src.retrieval.security_filter import filter_by_clearance
from src.retrieval.response_handler import generate_response

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variables to store processed data
document_chunks = []
chunk_embeddings = []
initialized = False

def initialize_system():
    """
    Initialize the system by loading documents, creating chunks, and generating embeddings.
    This is done once and cached for subsequent queries.
    """
    global document_chunks, chunk_embeddings, initialized

    if not initialized:
        logging.info("Attempting system initialization...")
        try:
            # Determine base directory relative to this script file
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(project_root, "data") # Construct path relative to project root

            logging.info(f"Looking for data directory at: {data_dir}")
            if not os.path.exists(data_dir):
                logging.error(f"Data directory not found at {data_dir}. Cannot initialize.")
                # You might want to create it if running for the first time locally,
                # but in deployment, it should exist.
                # os.makedirs(data_dir, exist_ok=True) # Uncomment carefully if needed
                return False

            # Define full paths to documents
            secret_manual_path = os.path.join(data_dir, "Secret_Info_Manual.txt")
            response_framework_path = os.path.join(data_dir, "Response_Framework.txt")

            logging.info(f"Checking for Secret Manual at: {secret_manual_path}")
            logging.info(f"Checking for Response Framework at: {response_framework_path}")

            if not os.path.exists(secret_manual_path) or not os.path.exists(response_framework_path):
                logging.error(f"Required documents not found. Checked paths:\n- {secret_manual_path}\n- {response_framework_path}")
                return False

            # Load documents
            logging.info("Loading documents...")
            documents = load_documents(
                secret_manual_path=secret_manual_path,
                response_framework_path=response_framework_path
            )
            logging.info(f"Loaded {len(documents)} documents.")

            # Create chunks from documents
            logging.info("Creating chunks...")
            document_chunks = create_chunks(documents) # Assuming chunk_and_annotate prints its own count
            if not document_chunks:
                 logging.warning("No chunks were created from the documents.")
                 # return False # Decide if this is a fatal error

            # --- Debug: Print sample chunk metadata ---
            if document_chunks:
                logging.info("Sample chunks metadata:")
                for i, chunk in enumerate(document_chunks[:5]): # Print first 5
                    logging.info(f"  Chunk {i}: {chunk['metadata']}")
                if len(document_chunks) > 5:
                   logging.info(f"  Chunk {len(document_chunks)-1}: {document_chunks[-1]['metadata']}") # Print last one


            # Generate embeddings for chunks
            logging.info("Generating embeddings...")
            chunk_embeddings = get_embeddings(document_chunks) # Assuming embedding_engine prints its own count
            if not chunk_embeddings:
                 logging.warning("No embeddings were generated.")
                 # return False # Decide if this is a fatal error

            if len(document_chunks) != len(chunk_embeddings):
                 logging.error(f"Mismatch between chunk count ({len(document_chunks)}) and embedding count ({len(chunk_embeddings)})")
                 return False

            initialized = True
            logging.info("System initialization successful.")
            return True
        except Exception as e:
            logging.exception(f"CRITICAL ERROR during initialization: {str(e)}") # Use logging.exception to include traceback
            return False

    return True # Already initialized

def process_query(query, agent_level):
    """
    Process a user query and return relevant information based on agent level.
    """
    if not query.strip():
        logging.warning("Received empty query.")
        return "", "Please enter a valid query.", "error"

    logging.info(f"Processing query: '{query[:50]}...' for agent level: {agent_level}")

    try:
        # Initialize system if not already done
        if not initialized:
            logging.info("Initializing system on first query...")
            if not initialize_system():
                logging.error("System initialization failed. Cannot process query.")
                return "", "System initialization failed. Check logs or document files.", "error"

        # Convert agent level string to numeric value
        level_mapping = {
            "Level 1 (Low)": 1,
            "Level 2 (Medium)": 2,
            "Level 3 (High)": 3
        }
        numeric_level = level_mapping.get(agent_level, 1) # Default to 1 if mapping fails
        logging.info(f"Mapped agent level to numeric: {numeric_level}")

        # Handle the case where documents aren't loaded properly (double check)
        if not document_chunks or not chunk_embeddings:
            logging.error("Document chunks or embeddings are empty after initialization check.")
            return "", "No document data available. Please check logs or document files.", "error"

        # Search for relevant chunks
        logging.info("Searching for similar chunks...")
        relevant_chunks = search_similar_chunks(query, document_chunks, chunk_embeddings)
        # --- Debug: Print raw search results ---
        logging.info(f"Found {len(relevant_chunks)} potentially relevant chunks before filtering.")
        for i, chunk in enumerate(relevant_chunks):
             logging.info(f"  Raw Chunk {i}: Similarity={chunk.get('similarity', 'N/A'):.4f}, Level={chunk['metadata'].get('security_level', 'N/A')}, Source='{chunk['metadata'].get('source', 'N/A')}', Text='{chunk['text'][:50]}...'")


        if not relevant_chunks:
            logging.info("No relevant chunks found by vector search.")
            return "", "", "no_results"

        # Filter chunks based on clearance level
        logging.info(f"Filtering chunks based on user clearance level: {numeric_level}")
        accessible_chunks, is_access_denied = filter_by_clearance(relevant_chunks, numeric_level)
        # --- Debug: Print filtered results ---
        logging.info(f"Found {len(accessible_chunks)} accessible chunks after filtering. Access denied flag: {is_access_denied}")
        for i, chunk in enumerate(accessible_chunks):
             logging.info(f"  Accessible Chunk {i}: Similarity={chunk.get('similarity', 'N/A'):.4f}, Level={chunk['metadata'].get('security_level', 'N/A')}, Source='{chunk['metadata'].get('source', 'N/A')}', Text='{chunk['text'][:50]}...'")


        # Important: Check *why* access might be denied or no results
        if is_access_denied and not accessible_chunks:
             logging.warning("Access denied because all relevant chunks were above the user's clearance level.")
             return "", "", "access_denied" # Return access denied only if *all* results were filtered out

        if not accessible_chunks:
             # This happens if vector search found results, but they were *all* filtered out by security
             # OR if vector search found results, but none survived filtering (even if is_access_denied is False - implies a logic bug?)
             logging.warning("No accessible chunks remaining after security filtering.")
             return "", "", "no_results" # Or maybe 'access_denied' is more appropriate if is_access_denied was True? Decide based on desired behavior.

        # Generate response from accessible chunks
        logging.info("Generating response from accessible chunks...")
        response, explanation = generate_response(query, accessible_chunks)
        # --- Debug: Log the final response components ---
        logging.info(f"Generated Response length: {len(response)}")
        logging.info(f"Generated Explanation: {explanation}")

        if not response.strip() or response.startswith("Based on the available information"):
            logging.warning("Generated response is empty or generic, likely due to response handler threshold or logic.")
            # Consider returning "no_results" or a more specific message if the explanation is also weak.
            # For now, let it pass through.

        return response, explanation, "success"

    except Exception as e:
        logging.exception(f"Error processing query '{query[:50]}...': {str(e)}") # Use logging.exception
        return "", f"An error occurred during processing. Check server logs.", "error" # More generic UI error

# --- END OF FILE backend.py ---