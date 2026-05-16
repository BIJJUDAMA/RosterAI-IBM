"""
IBM Cloud Integration Module
Provides watsonx.ai client for AI inference and embeddings
"""

from .config import WATSONX_CONFIG, validate_watsonx_config
from .watsonx_client import WatsonxClient

__all__ = [
    'WATSONX_CONFIG',
    'validate_watsonx_config',
    'WatsonxClient',
]

# Made with Bob
