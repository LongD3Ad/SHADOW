# --- COMPLETED and CORRECTED backend.py (Indentation Fixed) ---

import os
import logging
import datetime
import time
import re # Make sure re is imported
from typing import Tuple, List, Dict, Any, Optional

# Import project modules
from src.data_processing.ingest_documents import load_documents
from src.data_processing.chunk_and_annotate import create_chunks, get_chunk_context # Import get_chunk_context
from src.retrieval.embedding_engine import get_embeddings
from src.retrieval.vector_search import search_similar_chunks
from src.retrieval.security_filter import filter_by_clearance
# Use standard response generator only as fallback or if style guide fails
from src.retrieval.response_handler import generate_standard_response
from src.framework.rule_parser import parse_rules, match_rule_to_query

# Setup logging
# Configure logging format ONCE at the application entry point (e.g., app.py) if possible
# For this module, just get the logger
logger = logging.getLogger(__name__) # Use __name__ for logger

# Global variables to store processed data
document_chunks: List[Dict[str, Any]] = []
chunk_embeddings: List[Any] = [] # Typically list of numpy arrays or tensors
parsed_rules: List[Dict[str, Any]] = []
initialized: bool = False
last_initialization_attempt: float = 0
INITIALIZATION_COOLDOWN: int = 300  # 5 minutes in seconds

class SystemNotInitializedError(Exception):
    """Exception raised when the system is not properly initialized."""
    pass

# --- initialize_system function ---
def initialize_system(force: bool = False) -> bool:
    """
    Initialize the system by loading documents, creating chunks, and generating embeddings.
    This is done once and cached for subsequent queries.
    """
    global document_chunks, chunk_embeddings, parsed_rules, initialized, last_initialization_attempt

    current_time = time.time()
    if not force and initialized:
        logger.debug("System already initialized.") # Use debug level for this
        return True
    elif not force and (current_time - last_initialization_attempt < INITIALIZATION_COOLDOWN) and not initialized:
        logger.warning(f"Initialization failed less than {INITIALIZATION_COOLDOWN/60:.1f} minutes ago. Skipping attempt.")
        return False # Explicitly return False, it's not initialized

    last_initialization_attempt = current_time
    logger.info("Attempting system initialization (force=%s)...", force)

    try:
        # Reset globals ONLY if forcing or if not initialized yet
        if force or not initialized:
            logger.info("Resetting global data for initialization.")
            initialized = False # Mark as not initialized until success
            document_chunks = []
            chunk_embeddings = []
            parsed_rules = []

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(project_root, "data")
        logger.info(f"Looking for data directory at: {data_dir}")
        if not os.path.exists(data_dir):
            logger.error(f"Data directory not found at {data_dir}.")
            return False # Cannot initialize

        secret_manual_path = os.path.join(data_dir, "Secret_Info_Manual.txt")
        response_framework_path = os.path.join(data_dir, "Response_Framework.txt")
        logger.info(f"Checking for Secret Manual at: {secret_manual_path}")
        logger.info(f"Checking for Response Framework at: {response_framework_path}")
        if not os.path.exists(secret_manual_path) or not os.path.exists(response_framework_path):
            logger.error("Required document(s) not found.")
            return False

        # Load documents
        logger.info("Loading documents...")
        documents = load_documents(
            secret_manual_path=secret_manual_path,
            response_framework_path=response_framework_path
        )
        logger.info(f"Loaded {len(documents)} documents.")

        # Parse rules
        if force or not parsed_rules: # Check before parsing
            logger.info(f"Parsing response framework rules from: {response_framework_path}")
            try:
                parsed_rules = parse_rules(response_framework_path)
                logger.info(f"Successfully parsed {len(parsed_rules)} rules.")
                if not parsed_rules:
                    logger.warning("No rules parsed. Rule-based responses disabled.")
            except Exception as e:
                logger.error(f"Failed to parse response framework rules: {e}", exc_info=True)
        else:
            logger.info("Rules already parsed, skipping parse.")

        # Create chunks
        if force or not document_chunks: # Check before chunking
             logger.info("Creating chunks...")
             document_chunks = create_chunks(documents)
             if not document_chunks:
                 logger.error("No chunks were created. Cannot proceed.")
                 return False
             # Debug: Print sample chunk metadata
             logger.info("Sample chunks metadata:")
             for i, chunk in enumerate(document_chunks[:3]): logger.info(f"  Chunk {i}: {chunk['metadata']}")
             if len(document_chunks) > 3: logger.info(f"  Chunk {len(document_chunks)-1}: {document_chunks[-1]['metadata']}")
        else:
            logger.info("Chunks already created, skipping.")


        # Generate embeddings
        if force or not chunk_embeddings: # Check before embedding
            logger.info("Generating embeddings...")
            chunk_embeddings = get_embeddings(document_chunks)
            if not chunk_embeddings:
                logger.error("No embeddings were generated. Cannot proceed.")
                return False
        else:
            logger.info("Embeddings already generated, skipping.")

        # Final validation
        if len(document_chunks) != len(chunk_embeddings):
            logger.error(f"CRITICAL: Mismatch between chunk count ({len(document_chunks)}) and embedding count ({len(chunk_embeddings)})")
            return False

        initialized = True
        logger.info("System initialization successful.")
        return True

    except Exception as e:
        logger.exception(f"CRITICAL ERROR during initialization: {e}")
        initialized = False # Ensure state reflects failure
        return False

# --- check_time_based_rule function ---
def check_time_based_rule(rule: Dict[str, Any]) -> bool:
    """Check if a time-based rule should trigger based on current UTC time."""
    if rule.get("trigger_type") != "time_sensitive_topic": return False
    trigger_value = rule.get("trigger_value", "")
    if not trigger_value or "|" not in trigger_value:
        logger.warning(f"Invalid trigger_value for time_sensitive_topic rule {rule.get('rule_number')}: {trigger_value}")
        return False

    _, time_str = trigger_value.split("|", 1)
    logger.debug(f"Checking time condition: {time_str}")
    time_match = re.search(r"(\d+)\s+(AM|PM)\s+UTC", time_str, re.IGNORECASE)
    if not time_match:
        logger.warning(f"Could not parse time string: {time_str}")
        return False

    hour = int(time_match.group(1))
    period = time_match.group(2).upper()
    if period == "PM" and hour != 12: hour += 12
    elif period == "AM" and hour == 12: hour = 0

    current_utc_hour = datetime.datetime.utcnow().hour
    logger.debug(f"Current UTC hour: {current_utc_hour}, Rule trigger hour (after): {hour}")
    # Trigger AFTER the specified hour
    return current_utc_hour > hour

# --- handle_style_guide_response function ---

def handle_style_guide_response(query: str, rule: Dict[str, Any], accessible_chunks: List[Dict[str, Any]]) -> Tuple[str, str]:
    """Generate a response based on a style guide rule, using retrieved chunks."""
    style_instruction = rule.get("response_value", "").lower() # Use lower for matching
    rule_number = rule.get("rule_number", "N/A")
    trigger_val = rule.get("trigger_value", "N/A")
    response = ""
    explanation_detail = "" # Specific detail about how style was applied

    logger.info(f"Handling style guide rule {rule_number} ('{style_instruction}') for trigger '{trigger_val}'.")
    explanation_prefix = f"Response generated following style guidelines from rule {rule_number}. "

    if not accessible_chunks:
        # ... (no chunks logic remains the same) ...
        logger.warning(f"Style guide rule {rule_number} triggered, but no accessible chunks found.")
        response = f"Framework rule {rule_number} applies, but no specific information could be retrieved or accessed at your clearance level."
        explanation = f"Framework rule {rule_number} ('{trigger_val}') was matched, but retrieval yielded no accessible content chunks."
        return response, explanation

    # --- Apply styling based on keywords ---
    if "step-by-step" in style_instruction:
        # ... (step-by-step logic) ...
        steps = [f"Step {i+1}: {chunk['text']}" for i, chunk in enumerate(accessible_chunks[:3])]
        response = "\n\n".join(steps) if steps else "No specific steps identified in retrieved data."
        explanation_detail = "Formatted as step-by-step instructions using retrieved information."

    # <<< ADD LOGIC FOR RULE 2 HERE >>>
    elif "direct tactical steps" in style_instruction:
        # For this style, simply concatenate the relevant chunk text directly.
        # We might limit the number of chunks or characters later if needed.
        tactical_steps = [chunk['text'] for chunk in accessible_chunks[:2]] # Use top 1 or 2 chunks
        response = "\n\n---\n\n".join(tactical_steps) if tactical_steps else "No specific tactical steps found."
        explanation_detail = "Provided direct tactical steps based on retrieved information."
    # <<< END OF ADDED LOGIC >>>

    elif "scenario-based options" in style_instruction:
        # ... (scenario logic) ...
        options = [f"Option {i+1}:\n{chunk['text']}" for i, chunk in enumerate(accessible_chunks[:3])]
        response = "\n\n---\n\n".join(options) if options else "No specific scenarios identified."
        explanation_detail = "Formatted as scenario-based options using retrieved information."
    # ... (other elif conditions for checklist, analogy, etc.) ...
    elif "structured checklist" in style_instruction:
        items = [f"- [ ] {chunk['text'].split('.')[0].strip()}" for chunk in accessible_chunks[:5]]
        response = "Checklist:\n" + "\n".join(items) if items else "Checklist could not be generated from retrieved data."
        explanation_detail = "Formatted as a checklist based on retrieved information."
    elif "analogy" in style_instruction or "metaphor" in style_instruction:
        analogy_chunks = [c['text'] for c in accessible_chunks if re.search(r'\b(like|similar to|imagine)\b', c['text'].lower())]
        if analogy_chunks: response = "\n\n".join(analogy_chunks[:2]); explanation_detail = "Explained using analogies found in retrieved information."
        else: response = accessible_chunks[0]['text']; explanation_detail = "Attempted to explain using analogies; providing most relevant retrieved information."
    elif "codewords" in style_instruction or "indirect phrasing" in style_instruction:
        response = accessible_chunks[0]['text'][:200] + "..."; explanation_detail = "Used indirect phrasing by providing a relevant snippet."
    elif "cryptic" in style_instruction or "parable" in style_instruction:
        response = accessible_chunks[0]['text']; explanation_detail = "Provided potentially relevant information cryptically (showing most relevant chunk)."
    else:
        # ... (fallback logic remains the same) ...
        logger.warning(f"Unhandled style guide instruction in rule {rule_number}: '{style_instruction}'. Falling back to standard response format.")
        response, standard_explanation = generate_standard_response(query, accessible_chunks)
        explanation = explanation_prefix + f"Used standard response format as style '{style_instruction}' was not recognized. {standard_explanation}"
        return response, explanation

    # ... (Construct final explanation logic remains the same) ...
    source_info = "\n\nSources considered:\n"
    for i, chunk in enumerate(accessible_chunks[:3]):
        context = get_chunk_context(chunk)
        similarity = chunk.get("similarity", 0)
        similarity_percent = f"{similarity * 100:.1f}%"
        source_info += f"{i+1}. {context} (Relevance: {similarity_percent})\n"
    final_explanation = explanation_prefix + explanation_detail + source_info
    return response, final_explanation

    # --- Construct final explanation for handled styles ---
    source_info = "\n\nSources considered:\n"
    for i, chunk in enumerate(accessible_chunks[:3]):
        context = get_chunk_context(chunk)
        similarity = chunk.get("similarity", 0)
        similarity_percent = f"{similarity * 100:.1f}%"
        source_info += f"{i+1}. {context} (Relevance: {similarity_percent})\n"

    final_explanation = explanation_prefix + explanation_detail + source_info
    return response, final_explanation

# --- process_query function - The Core Logic ---
def process_query(query: str, agent_level_str: str) -> Tuple[str, str, str]:
    """Process a user query, applying framework rules and falling back to RAG."""
    if not query.strip():
        logger.warning("Received empty query.")
        return "", "Please enter a valid query.", "error"

    logger.info(f"Processing query: '{query[:50]}...' for agent level: {agent_level_str}")

    # --- Initialization Check ---
    if not initialized:
        logger.info("System not initialized. Attempting initialization...")
        if not initialize_system():
            logger.error("System initialization failed. Cannot process query.")
            time_since_last = time.time() - last_initialization_attempt
            err_msg = "System initialization failed. Check logs or document files."
            if time_since_last < INITIALIZATION_COOLDOWN:
                err_msg = f"System initialization failed recently. Please wait a few minutes and try again."
            return "", err_msg, "error"

    # --- Agent Level Mapping ---
    level_mapping = {"Level 1 (Low)": 1, "Level 2 (Medium)": 2, "Level 3 (High)": 3, "Level 4 (Very High)": 4, "Level 5 (Top Secret)": 5}
    numeric_level = level_mapping.get(agent_level_str, 1)
    logger.info(f"Mapped agent level string '{agent_level_str}' to numeric: {numeric_level}")

    # --- Data Availability Check ---
    if not document_chunks or not chunk_embeddings:
         logger.error("Core data (chunks/embeddings) missing after initialization check.")
         return "", "System data is unavailable. Please contact support.", "error"
    if not parsed_rules:
        logger.warning("Parsed rules are missing, proceeding with RAG only.")

    # --- Stage 1: Rule Matching ---
    matched_rule: Optional[Dict[str, Any]] = None
    apply_style_guide: bool = False

    if parsed_rules: # Only attempt matching if rules were parsed
        matched_rule = match_rule_to_query(parsed_rules, query, numeric_level)

    if matched_rule:
        rule_number = matched_rule.get('rule_number', 'N/A')
        trigger_type = matched_rule.get('trigger_type', 'N/A')
        trigger_value = matched_rule.get('trigger_value', 'N/A')
        response_type = matched_rule.get('response_type', 'N/A')
        response_value = matched_rule.get('response_value', '')

        logger.info(f"Framework rule {rule_number} matched: Type={trigger_type}, Trigger='{trigger_value}', RespType={response_type}")

        # Handle rules providing immediate, direct responses
        if response_type in ["direct_quote", "access_denied"]:
            explanation = f"Response generated based on framework rule {rule_number} ('{trigger_value}')."
            logger.info(f"Returning direct response from rule {rule_number}.")
            return response_value, explanation, "success"
        elif response_type == "time_based":
            if check_time_based_rule(matched_rule):
                logger.info(f"Time-based rule {rule_number} triggered by time condition.")
                current_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                weather_response = f"As per time-sensitive protocols (Rule {rule_number}): Weather Report for {current_date}: Conditions variable. Proceed with caution."
                explanation = f"Response generated based on time-sensitive framework rule {rule_number} for trigger '{trigger_value.split('|')[0]}'."
                return weather_response, explanation, "success"
            else:
                logger.info(f"Time-based rule {rule_number} matched trigger, but time condition not met. Proceeding to RAG.")
                matched_rule = None # Ignore rule, proceed as if no match
        elif response_type == "style_guide":
            logger.info(f"Style guide rule {rule_number} matched. Will apply style after RAG.")
            apply_style_guide = True # Flag to apply style later
        else:
            logger.warning(f"Rule {rule_number} matched but has unhandled response type: '{response_type}'. Proceeding to RAG.")
            matched_rule = None # Ignore rule

    # --- Stage 2: RAG Pipeline (Vector Search, Source Filter, Security Filter) ---
    # This stage runs if no direct response was returned by a rule above.
    logger.info("Proceeding to RAG pipeline...")
    try:
        # Step 2a: Initial Search
        logger.debug("Performing initial vector search across all documents...")
        relevant_chunks = search_similar_chunks(query, document_chunks, chunk_embeddings)
        if not relevant_chunks:
            logger.info("Initial vector search returned no relevant chunks.")
            if apply_style_guide and matched_rule:
                 no_rag_response, no_rag_explanation = handle_style_guide_response(query, matched_rule, [])
                 return no_rag_response, no_rag_explanation, "success"
            else:
                 return "", "No information found matching your query.", "no_results" # Clearer explanation

        # Step 2b: Source Filtering (Prioritize Secret Info Manual)
        logger.debug(f"Filtering {len(relevant_chunks)} retrieved chunks for 'Secret Info Manual' source...")
        content_focused_chunks = [
            chunk for chunk in relevant_chunks
            if chunk.get('metadata', {}).get('source') == 'Secret Info Manual'
        ]
        logger.info(f"{len(content_focused_chunks)} content chunks relevant after source filtering.")
        if not content_focused_chunks:
             logger.warning("No relevant chunks found originating from 'Secret Info Manual'.")
             rag_explanation = "No specific information found in the Secret Information Manual matching your query."
             if apply_style_guide and matched_rule:
                  no_content_response, no_content_explanation = handle_style_guide_response(query, matched_rule, [])
                  return no_content_response, no_content_explanation, "success"
             return "", rag_explanation, "no_results"

        # Step 2c: Security Filtering
        logger.debug(f"Filtering {len(content_focused_chunks)} content chunks by clearance level {numeric_level}...")
        accessible_chunks, is_access_denied = filter_by_clearance(content_focused_chunks, numeric_level)
        logger.info(f"{len(accessible_chunks)} accessible content chunks after security filtering. Access denied flag: {is_access_denied}")
        if not accessible_chunks:
            reason_explanation = ""
            status = "no_results"
            if is_access_denied:
                logger.warning("Access Denied: Relevant content chunks required higher clearance.")
                reason_explanation = "Access Denied: Required clearance level not met for retrieved information."
                status = "access_denied"
            else:
                logger.warning("No accessible content chunks remaining after security filtering (and not denied).")
                reason_explanation = "No information accessible at your clearance level was found for this query."
            if apply_style_guide and matched_rule:
                no_access_response, no_access_explanation = handle_style_guide_response(query, matched_rule, [])
                return no_access_response, no_access_explanation, "success"
            else:
                return "", reason_explanation, status

        # --- Stage 3: Generate Final Response using RAG Results ---
        if apply_style_guide and matched_rule:
            logger.info(f"Applying style guide from rule {matched_rule.get('rule_number')} using {len(accessible_chunks)} chunks.")
            response, explanation = handle_style_guide_response(query, matched_rule, accessible_chunks)
            return response, explanation, "success"
        else:
            logger.info(f"Generating standard response using {len(accessible_chunks)} accessible chunks.")
            response, explanation = generate_standard_response(query, accessible_chunks)
            # Check if the standard response indicates low relevance and potentially adjust status
            if response.startswith("Based on the available information"):
                 logger.warning("Standard response generator indicated low relevance/threshold not met.")
                 # Consider if returning 'no_results' status is more appropriate here
                 # return response, explanation, "no_results" # Optional change
            return response, explanation, "success"

    except Exception as e:
        logger.exception(f"Error during RAG pipeline execution: {e}")
        return "", f"An error occurred during information retrieval.", "error" # Keep UI error generic

    # --- Fallback catch --- This should only be reached if there's a logic flaw above
    logger.error("Reached end of process_query function unexpectedly.")
    return "", "An unexpected internal error occurred.", "error"


# --- Example __main__ block for testing ---
# if __name__ == '__main__':
#     # Configure logging for testing if run directly
#     logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

#     if initialize_system(force=True): # Force re-init for testing
#         print("\n--- System Initialized ---")
#         print(f"Parsed Rules: {len(parsed_rules)}")
#         print(f"Document Chunks: {len(document_chunks)}")
#         print(f"Chunk Embeddings: {len(chunk_embeddings)}")

#         print("\n--- Testing Queries ---")
#         test_queries = [
#             ("Omega Echo", "Level 1 (Low)"), # Rule 6 Direct Quote
#             ("Tell me about Operation Hollow Stone", "Level 2 (Medium)"), # Rule 14 Direct Quote
#             ("Who controls RAW?", "Level 5 (Top Secret)"), # Rule 17 Direct Quote
#             ("The bridge is burning", "Level 3 (High)"), # Rule 21 Starts With Quote
#             ("What about level 5 data?", "Level 3 (High)"), # Rule 10 Access Denied
#             ("Tell me about Facility X-17", "Level 3 (High)"), # Rule 31 Time Rule
#             # --- Test Style Guides ---
#             ("What is the emergency extraction protocol?", "Level 1 (Low)"), # Rule 1 Style Guide (step-by-step)
#             ("How do I handle compromised assets?", "Level 3 (High)"), # Rule 8 Style Guide (scenario)
#             ("How to verify a false identity?", "Level 2 (Medium)"), # Rule 9 Style Guide (checklist)
#             ("Tell me about neural signature scanners", "Level 1 (Low)"), # Rule 25 Style Guide (analogy)
#             # --- Test RAG Fallback ---
#             ("What is the S-29 Protocol?", "Level 3 (High)"), # Should use RAG from Secret Manual
#             ("Describe the Handshake Protocol", "Level 2 (Medium)"), # Should use RAG
#             ("Some random query with no match", "Level 2 (Medium)"), # Should likely return "no_results"
#             # --- Test Security ---
#             ("What is Project Eclipse?", "Level 1 (Low)") # Should hit RAG, find content, but be denied access
#         ]

#         for q, level_str in test_queries:
#             print(f"\n--- Query: '{q}' (Level: {level_str}) ---")
#             response, explanation, status = process_query(q, level_str)
#             print(f"Status: {status}")
#             print(f"Response:\n{response}")
#             print(f"\nExplanation:\n{explanation}")
#             print("-" * 30)
#     else:
#         print("\n--- System Initialization Failed ---")