import os
import json

def load_documents(secret_manual_path, response_framework_path):
    """
    Load and parse the Secret Info Manual and Response Framework documents.
    
    Args:
        secret_manual_path (str): Path to the Secret Info Manual document
        response_framework_path (str): Path to the Response Framework document
        
    Returns:
        dict: Dictionary containing the loaded documents
    """
    documents = {}
    
    # Check if files exist
    for path, doc_name in [
        (secret_manual_path, "Secret Info Manual"),
        (response_framework_path, "Response Framework")
    ]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Document not found: {path}")
    
    # Load Secret Info Manual
    try:
        with open(secret_manual_path, 'r', encoding='utf-8') as file:
            content = file.read()
            documents["Secret Info Manual"] = {
                "content": content,
                "metadata": {
                    "source": "Secret Info Manual",
                    "path": secret_manual_path,
                    "type": "classified"
                }
            }
    except Exception as e:
        raise IOError(f"Error loading Secret Info Manual: {str(e)}")
    
    # Load Response Framework
    try:
        with open(response_framework_path, 'r', encoding='utf-8') as file:
            content = file.read()
            documents["Response Framework"] = {
                "content": content,
                "metadata": {
                    "source": "Response Framework",
                    "path": response_framework_path,
                    "type": "framework"
                }
            }
    except Exception as e:
        raise IOError(f"Error loading Response Framework: {str(e)}")
    
    print(f"Successfully loaded {len(documents)} documents")
    return documents

def parse_document_structure(content, doc_type):
    """
    Parse document content into structured sections.
    This is a simplistic implementation and would need to be enhanced
    based on the actual document structure.
    
    Args:
        content (str): The document content
        doc_type (str): Type of document (e.g., "classified", "framework")
        
    Returns:
        dict: Structured document with sections
    """
    # Simple section detection based on headers (starting with # or ## in markdown)
    sections = []
    current_section = {"title": "Introduction", "content": "", "level": 0}
    
    for line in content.split('\n'):
        if line.startswith('# '):
            # Save previous section if it has content
            if current_section["content"].strip():
                sections.append(current_section)
            
            # Start new section
            current_section = {
                "title": line.replace('# ', '').strip(),
                "content": "",
                "level": 1
            }
        elif line.startswith('## '):
            # Save previous section if it has content
            if current_section["content"].strip():
                sections.append(current_section)
            
            # Start new subsection
            current_section = {
                "title": line.replace('## ', '').strip(),
                "content": "",
                "level": 2
            }
        else:
            # Add line to current section
            current_section["content"] += line + "\n"
    
    # Add the last section
    if current_section["content"].strip():
        sections.append(current_section)
    
    # Determine security levels for sections if it's the Secret Info Manual
    if doc_type == "classified":
        for section in sections:
            # Assign security level based on content analysis (simplified example)
            if "top secret" in section["content"].lower():
                section["security_level"] = 3
            elif "confidential" in section["content"].lower():
                section["security_level"] = 2
            else:
                section["security_level"] = 1
    
    return sections