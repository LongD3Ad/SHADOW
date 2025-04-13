# --- START OF FILE chunk_and_annotate.py (Simplified Level Logic) ---

import re
import uuid
import logging

logger = logging.getLogger(__name__)

# --- Define Keyword Sets ONLY for HEADERS ---
LEVEL3_KEYWORDS_HEADER = re.compile(r'\b(classified|black site|termination|omega|eclipse|shadow|void|requiem|protocol zeta|level [7-9]|level-[7-9])\b', re.IGNORECASE)
LEVEL2_KEYWORDS_HEADER = re.compile(r'\b(covert|safehouse|counter-surveillance|protocol|verification|level [2-6]|level-[2-6])\b', re.IGNORECASE) # Added 'verification'
# No paragraph keyword sets needed for this simplified logic

def create_chunks(documents, chunk_size=1000, overlap=100):
    """Split documents using header-focused level assignment."""
    all_chunks = []
    logger.info(f"Starting chunking (Header-Focused Level): ChunkSize={chunk_size}, Overlap={overlap}")

    for doc_name, document in documents.items():
        content = document["content"]; metadata = document["metadata"]
        logger.info(f"Processing document: {doc_name} (Type: {metadata['type']})")
        is_classified = metadata["type"] == "classified"
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n+', content) if p.strip()]
        logger.info(f"'{doc_name}' split into {len(paragraphs)} paragraphs.")
        if not paragraphs: continue

        current_chunk_text = ""
        # Metadata now primarily holds the level determined by the LAST SEEN HEADER
        current_section_metadata = { # Renamed for clarity
            "source": doc_name, "doc_type": metadata["type"], "section": "Unknown",
            "security_level": 1 if is_classified else 0 # Default level before first header
        }
        logger.debug(f"Initial metadata for '{doc_name}': {current_section_metadata}")

        for i, paragraph in enumerate(paragraphs):
            # --- 1. Check for Headers & SET SECTION LEVEL ---
            header_match = re.match(r'^#+\s+(.+)$', paragraph)
            if header_match:
                section_title = header_match.group(1).strip()
                current_section_metadata["section"] = section_title # Update section name
                logger.debug(f"Paragraph {i}: Found header: '{section_title}'")

                # Determine and SET level based *only* on this header (for classified)
                if is_classified:
                    new_level = 1 # Default classified level
                    explicit_level_match = re.search(r'level\s+(\d+)', section_title, re.IGNORECASE)
                    if explicit_level_match:
                        level = int(explicit_level_match.group(1)); new_level = max(1, min(level, 3))
                        logger.debug(f"  Header '{section_title}' explicit Level {level}. Setting section level to {new_level}.")
                    elif LEVEL3_KEYWORDS_HEADER.search(section_title):
                        new_level = 3
                        logger.debug(f"  Header '{section_title}' L3 keyword. Setting section level to 3.")
                    elif LEVEL2_KEYWORDS_HEADER.search(section_title):
                        new_level = 2
                        logger.debug(f"  Header '{section_title}' L2 keyword. Setting section level to 2.")
                    else:
                        logger.debug(f"  Header '{section_title}' no keywords. Setting section level to 1.")

                    # *** Update the section metadata level ***
                    current_section_metadata["security_level"] = new_level

                continue # Skip header paragraph from chunk text

            # --- 2. Paragraph Content Analysis (REMOVED for level setting) ---
            # We are IGNORING paragraph keywords for setting levels in this version

            # --- 3. Chunking Logic ---
            paragraph_len = len(paragraph) + 2
            current_len = len(current_chunk_text)

            # Case 1: Chunk full -> finalize old, start new
            if current_len > 0 and current_len + paragraph_len > chunk_size:
                chunk_id = str(uuid.uuid4())
                # *** Use the current_section_metadata directly ***
                # The level is determined by the last header encountered before this chunk was finalized
                chunk_metadata_final = current_section_metadata.copy()

                text_snippet = current_chunk_text[:80].strip() + "..."
                logger.info(f"--> Creating Chunk {chunk_id[-6:]}: Level={chunk_metadata_final['security_level']}, Section='{chunk_metadata_final['section']}', Text='{text_snippet}'")
                all_chunks.append({"id": chunk_id, "text": current_chunk_text.strip(), "metadata": chunk_metadata_final})
                current_chunk_text = paragraph # Start new chunk text

            # Case 2: Paragraph too big -> create truncated chunk
            elif current_len == 0 and paragraph_len > chunk_size:
                chunk_id = str(uuid.uuid4())
                # *** Use the current_section_metadata directly ***
                chunk_metadata_final = current_section_metadata.copy()

                text_snippet = paragraph[:80].strip() + "..."
                logger.warning(f"Paragraph {i} exceeds chunk size. Truncating.")
                logger.info(f"--> Creating Chunk {chunk_id[-6:]} (Truncated): Level={chunk_metadata_final['security_level']}, Section='{chunk_metadata_final['section']}', Text='{text_snippet}'")
                all_chunks.append({"id": chunk_id, "text": paragraph[:chunk_size], "metadata": chunk_metadata_final})
                current_chunk_text = "" # Reset

            # Case 3: Add paragraph to current chunk
            else:
                if current_chunk_text: current_chunk_text += "\n\n" + paragraph
                else: current_chunk_text = paragraph
                # NO level update needed here based on paragraph

        # Add the very last chunk
        if current_chunk_text:
            chunk_id = str(uuid.uuid4())
            # *** Use the final state of current_section_metadata ***
            text_snippet = current_chunk_text[:80].strip() + "..."
            logger.info(f"--> Creating Final Chunk {chunk_id[-6:]}: Level={current_section_metadata['security_level']}, Section='{current_section_metadata['section']}', Text='{text_snippet}'")
            all_chunks.append({"id": chunk_id, "text": current_chunk_text.strip(), "metadata": current_section_metadata.copy()})

    logger.info(f"Chunking complete. Created {len(all_chunks)} chunks total.")
    if not all_chunks: logger.error("CRITICAL: No chunks generated!")
    return all_chunks

# get_chunk_context remains the same...
def get_chunk_context(chunk):
    metadata = chunk.get("metadata", {})
    context = f"Source: {metadata.get('source', 'N/A')}"
    if "section" in metadata: context += f" | Section: {metadata.get('section', 'N/A')}"
    if "security_level" in metadata:
        level_val = metadata.get("security_level", 0); display_level = min(level_val, 3)
        level_names = { 0: "Unrestricted", 1: "Level 1 (Low)", 2: "Level 2 (Medium)", 3: "Level 3 (High)"}
        context += f" | Security: {level_names.get(display_level, f'Level {display_level}')}"
    return context

# --- END OF FILE chunk_and_annotate.py ---