# import re
# import uuid

# def create_chunks(documents, chunk_size=1000, overlap=100):
#     """
#     Split documents into smaller chunks for processing, with metadata.
    
#     Args:
#         documents (dict): Dictionary of document objects
#         chunk_size (int): Target size of each chunk in characters
#         overlap (int): Overlap between consecutive chunks in characters
        
#     Returns:
#         list: List of chunk objects with text and metadata
#     """
#     all_chunks = []
    
#     for doc_name, document in documents.items():
#         content = document["content"]
#         metadata = document["metadata"]
        
#         # Determine if this is the classified document or framework
#         is_classified = metadata["type"] == "classified"
        
#         # Split content into paragraphs first
#         paragraphs = re.split(r'\n\s*\n', content)
        
#         current_chunk = ""
#         current_chunk_metadata = {
#             "source": doc_name,
#             "doc_type": metadata["type"],
#             "section": "Introduction",  # Default section
#             "security_level": 1 if is_classified else 0  # Default level
#         }
        
#         for paragraph in paragraphs:
#             # Check for section headers to update metadata
#             section_match = re.match(r'^#+\s+(.+)$', paragraph, re.MULTILINE)
#             if section_match:
#                 section_title = section_match.group(1).strip()
#                 current_chunk_metadata["section"] = section_title
                
#                 # Set security level based on section content and keywords
#                 if is_classified:
#                     # Check for explicit level mentions
#                     level_match = re.search(r'level\s+(\d+)', paragraph, re.IGNORECASE)
#                     if level_match:
#                         level = int(level_match.group(1))
#                         current_chunk_metadata["security_level"] = min(level, 3)
#                     # Check for security-related keywords
#                     elif re.search(r'top\s+secret|classified|omega|eclipse|shadow|void|requiem', paragraph, re.IGNORECASE):
#                         current_chunk_metadata["security_level"] = 3
#                     elif re.search(r'confidential|restricted|covert|tactical|protocol', paragraph, re.IGNORECASE):
#                         current_chunk_metadata["security_level"] = 2
#                     else:
#                         current_chunk_metadata["security_level"] = 1
                
#                 continue
            
#             # If adding this paragraph exceeds chunk size, save current chunk and start new one
#             if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
#                 chunk_id = str(uuid.uuid4())
#                 all_chunks.append({
#                     "id": chunk_id,
#                     "text": current_chunk.strip(),
#                     "metadata": current_chunk_metadata.copy()
#                 })
                
#                 # Start new chunk with overlap from previous chunk
#                 words = current_chunk.split()
#                 if len(words) > overlap:
#                     current_chunk = " ".join(words[-overlap:]) + " " + paragraph
#                 else:
#                     current_chunk = paragraph
#             else:
#                 # Add paragraph to current chunk
#                 if current_chunk:
#                     current_chunk += " " + paragraph
#                 else:
#                     current_chunk = paragraph
        
#         # Add the last chunk if it has content
#         if current_chunk:
#             chunk_id = str(uuid.uuid4())
#             all_chunks.append({
#                 "id": chunk_id,
#                 "text": current_chunk.strip(),
#                 "metadata": current_chunk_metadata.copy()
#             })
    
#     print(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
#     return all_chunks

# def get_chunk_context(chunk):
#     """
#     Generate a human-readable context description for a chunk.
    
#     Args:
#         chunk (dict): A document chunk with text and metadata
        
#     Returns:
#         str: A formatted context description
#     """
#     metadata = chunk["metadata"]
#     context = f"Source: {metadata['source']}"
    
#     if "section" in metadata:
#         context += f" | Section: {metadata['section']}"
    
#     if "security_level" in metadata:
#         level_names = {
#             0: "Unrestricted",
#             1: "Level 1 (Low)",
#             2: "Level 2 (Medium)",
#             3: "Level 3 (High)"
#         }
#         level = metadata["security_level"]
#         context += f" | Security: {level_names.get(level, f'Level {level}')}"
    
#     return context


# --- START OF FILE chunk_and_annotate.py ---

import re
import uuid
import logging # Use logging

def create_chunks(documents, chunk_size=1000, overlap=100):
    """
    Split documents into smaller chunks for processing, with metadata.
    """
    all_chunks = []
    logging.info(f"Starting chunking process for {len(documents)} documents. Chunk size={chunk_size}, Overlap={overlap}")

    for doc_name, document in documents.items():
        content = document["content"]
        metadata = document["metadata"]
        logging.info(f"Processing document: {doc_name} (Type: {metadata['type']})")

        is_classified = metadata["type"] == "classified"

        # Split content into paragraphs more robustly
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n+', content) if p.strip()]
        logging.info(f"Document '{doc_name}' split into {len(paragraphs)} paragraphs.")

        if not paragraphs:
            logging.warning(f"Document '{doc_name}' resulted in zero paragraphs after splitting.")
            continue

        current_chunk_text = ""
        # Initialize metadata carefully
        current_chunk_metadata = {
            "source": doc_name,
            "doc_type": metadata["type"],
            "section": "Unknown", # Default section if no header found initially
             # CRITICAL: Default security level. Let's default classified to 1, framework to 0.
            "security_level": 1 if is_classified else 0
        }

        for i, paragraph in enumerate(paragraphs):
            # Check for section headers FIRST to apply to subsequent paragraphs
            header_match = re.match(r'^#+\s+(.+)$', paragraph)
            if header_match:
                section_title = header_match.group(1).strip()
                logging.debug(f"Found header: '{section_title}' in doc '{doc_name}'")
                current_chunk_metadata["section"] = section_title

                # Reset/re-evaluate security level based *only* on the header initially for classified docs
                if is_classified:
                    level_match = re.search(r'level\s+(\d+)', section_title, re.IGNORECASE)
                    if level_match:
                        level = int(level_match.group(1))
                        # Clamp level between 1 and 3
                        current_chunk_metadata["security_level"] = max(1, min(level, 3))
                        logging.debug(f"Header '{section_title}' implies security level {current_chunk_metadata['security_level']}")
                    # Add more header-based rules if needed, e.g., if header contains "Termination Protocols" -> level 3
                    elif re.search(r'classified|black site|termination|omega|eclipse|shadow|void|requiem|protocol zeta', section_title, re.IGNORECASE):
                         current_chunk_metadata["security_level"] = 3
                         logging.debug(f"Header '{section_title}' implies security level 3 based on keywords.")
                    elif re.search(r'covert|safehouse|counter-surveillance|protocol', section_title, re.IGNORECASE):
                         # Avoid downgrading if already set higher
                         if current_chunk_metadata["security_level"] < 2:
                              current_chunk_metadata["security_level"] = 2
                              logging.debug(f"Header '{section_title}' implies security level 2 based on keywords.")
                    else:
                         # Avoid downgrading if already set higher
                         if current_chunk_metadata["security_level"] < 1:
                              current_chunk_metadata["security_level"] = 1 # Default for classified sections if no keywords hit
                              logging.debug(f"Header '{section_title}' implies security level 1 (default classified).")

                # Don't add the header itself as chunk text, continue to next paragraph
                continue

            # --- Security level check WITHIN the paragraph (can potentially elevate level) ---
            if is_classified:
                 paragraph_level = current_chunk_metadata["security_level"] # Start with section level
                 level_match = re.search(r'level\s+(\d+)', paragraph, re.IGNORECASE)
                 if level_match:
                      level = int(level_match.group(1))
                      paragraph_level = max(paragraph_level, max(1, min(level, 3))) # Elevate if higher
                 elif re.search(r'top\s+secret|classified|omega|eclipse|shadow|void|requiem|protocol zeta|kx-purge|facility x-17', paragraph, re.IGNORECASE):
                      paragraph_level = max(paragraph_level, 3)
                 elif re.search(r'confidential|restricted|covert|tactical|protocol|safehouse|cipher|handshake protocol|shadow step|vault-17', paragraph, re.IGNORECASE):
                      paragraph_level = max(paragraph_level, 2)

                 # Update the chunk's level if the paragraph elevated it
                 if paragraph_level > current_chunk_metadata["security_level"]:
                      logging.debug(f"Paragraph content elevated security level to {paragraph_level} in section '{current_chunk_metadata['section']}'")
                      current_chunk_metadata["security_level"] = paragraph_level


            # Chunking logic (simplified for clarity, your overlap logic seems okay)
            # This simple version chunks paragraph by paragraph if they are too long
            # Or combines them if they fit. A more sophisticated approach might use sentence splitting.
            paragraph_len = len(paragraph)
            current_len = len(current_chunk_text)

            if current_len > 0 and current_len + paragraph_len + 1 > chunk_size:
                # Finalize the current chunk
                chunk_id = str(uuid.uuid4())
                all_chunks.append({
                    "id": chunk_id,
                    "text": current_chunk_text,
                    "metadata": current_chunk_metadata.copy() # Use copy!
                })
                logging.debug(f"Created chunk {chunk_id} from '{doc_name}', section '{current_chunk_metadata['section']}', level {current_chunk_metadata['security_level']}, len {current_len}")

                # Start new chunk with the current paragraph
                current_chunk_text = paragraph
                # Metadata carries over (section/level might have updated)

            elif current_len == 0 and paragraph_len > chunk_size:
                 # Handle paragraph larger than chunk size (split or truncate)
                 # Simple truncation for now:
                 logging.warning(f"Paragraph {i} in {doc_name} exceeds chunk size ({paragraph_len} > {chunk_size}). Truncating.")
                 current_chunk_text = paragraph[:chunk_size]
                 # Finalize this truncated chunk immediately
                 chunk_id = str(uuid.uuid4())
                 all_chunks.append({
                     "id": chunk_id,
                     "text": current_chunk_text,
                     "metadata": current_chunk_metadata.copy()
                 })
                 logging.debug(f"Created chunk {chunk_id} (truncated) from '{doc_name}', section '{current_chunk_metadata['section']}', level {current_chunk_metadata['security_level']}, len {len(current_chunk_text)}")
                 current_chunk_text = "" # Reset for next iteration

            else:
                # Add paragraph to current chunk
                if current_chunk_text:
                    current_chunk_text += "\n\n" + paragraph # Use double newline like original split
                else:
                    current_chunk_text = paragraph

        # Add the last remaining chunk if it has content
        if current_chunk_text:
            chunk_id = str(uuid.uuid4())
            all_chunks.append({
                "id": chunk_id,
                "text": current_chunk_text,
                "metadata": current_chunk_metadata.copy()
            })
            logging.debug(f"Created final chunk {chunk_id} from '{doc_name}', section '{current_chunk_metadata['section']}', level {current_chunk_metadata['security_level']}, len {len(current_chunk_text)}")


    logging.info(f"Chunking complete. Created {len(all_chunks)} chunks total.")
    if not all_chunks:
        logging.error("CRITICAL: No chunks were generated from any document!")
    return all_chunks

# Keep get_chunk_context as is, but ensure it handles potential missing keys gracefully
def get_chunk_context(chunk):
    metadata = chunk.get("metadata", {}) # Use .get for safety
    context = f"Source: {metadata.get('source', 'N/A')}"

    if "section" in metadata:
        context += f" | Section: {metadata.get('section', 'N/A')}"

    if "security_level" in metadata:
        level_names = {
            0: "Unrestricted",
            1: "Level 1 (Low)",
            2: "Level 2 (Medium)",
            3: "Level 3 (High)"
        }
        level = metadata.get("security_level", 0) # Default to 0 if missing
        context += f" | Security: {level_names.get(level, f'Level {level}')}"

    return context

# --- END OF FILE chunk_and_annotate.py ---