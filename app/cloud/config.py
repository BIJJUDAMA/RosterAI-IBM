"""
IBM Cloud Configuration Management
Centralizes IBM watsonx.ai configuration for AI inference and embeddings
"""
import os
from dotenv import load_dotenv

load_dotenv()

# IBM watsonx.ai Configuration 
WATSONX_CONFIG = {
    "api_key": os.getenv("IBM_WATSONX_API_KEY"),
    "project_id": os.getenv("IBM_WATSONX_PROJECT_ID"),
    "url": os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
    "model_id": os.getenv("IBM_WATSONX_MODEL_ID", "meta-llama/llama-3-2-11b-vision-instruct"),
    "embedding_model": os.getenv("IBM_WATSONX_EMBEDDING_MODEL", "intfloat/multilingual-e5-large"),
    "embedding_dimensions": 1024,  # multilingual-e5-large produces 1024-dim vectors
}

def validate_watsonx_config() -> dict:
    """Validates that all required watsonx.ai credentials are present"""
    errors = []
    
    # Validate watsonx.ai 
    if not WATSONX_CONFIG["api_key"]:
        errors.append("IBM_WATSONX_API_KEY is required")
    if not WATSONX_CONFIG["project_id"]:
        errors.append("IBM_WATSONX_PROJECT_ID is required")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "config": {
            "model": WATSONX_CONFIG["model_id"],
            "embedding_model": WATSONX_CONFIG["embedding_model"],
            "embedding_dimensions": WATSONX_CONFIG["embedding_dimensions"],
            "url": WATSONX_CONFIG["url"],
        }
    }

# Made with Bob
