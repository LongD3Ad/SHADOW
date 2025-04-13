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
