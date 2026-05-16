"""
IBM watsonx.ai Client
Handles LLM inference and embeddings generation using IBM watsonx.ai foundation models
- LLM: Llama 3.2 11B Vision Instruct
- Embeddings: multilingual-e5-large (1024 dimensions)
"""
import os
import time
import re
import json
from typing import List, Optional, Dict, Any
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference, Embeddings
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import WATSONX_CONFIG
from ..logging_config import logger
from ..exceptions import LLMError, LLMTimeoutError, LLMConnectionError

class WatsonxClient:
    """Client for IBM watsonx.ai foundation models"""
    
    def __init__(self):
        """Initialize watsonx.ai client with credentials"""
        try:
            credentials = Credentials(
                api_key=WATSONX_CONFIG["api_key"],
                url=WATSONX_CONFIG["url"]
            )
            self.client = APIClient(credentials)
            self.project_id = WATSONX_CONFIG["project_id"]
            self.model_id = WATSONX_CONFIG["model_id"]
            self.embedding_model_id = WATSONX_CONFIG["embedding_model"]
            
            # Initialize model instances
            self._init_models()
            
            logger.info(f"✅ [bold green]watsonx.ai client initialized[/bold green]")
            logger.info(f"   LLM Model: {self.model_id}")
            logger.info(f"   Embedding Model: {self.embedding_model_id} (1024-dim)")
        except Exception as e:
            logger.error(f"❌ [bold red]Failed to initialize watsonx.ai client[/bold red]: {e}")
            raise LLMConnectionError("Could not connect to watsonx.ai", str(e))
    
    def _init_models(self):
        """Initialize LLM and embedding models"""
        try:
            # LLM for text generation
            self.llm = ModelInference(
                model_id=self.model_id,
                api_client=self.client,
                project_id=self.project_id,
                params={
                    GenParams.DECODING_METHOD: "greedy",
                    GenParams.MAX_NEW_TOKENS: 2048,
                    GenParams.TEMPERATURE: 0.0,
                    GenParams.STOP_SEQUENCES: ["</think>", "<|endoftext|>"],
                    GenParams.REPETITION_PENALTY: 1.1,
                }
            )
            
            # Embeddings model
            self.embeddings = Embeddings(
                model_id=self.embedding_model_id,
                api_client=self.client,
                project_id=self.project_id
            )
            
            logger.debug("watsonx.ai models initialized successfully")
        except Exception as e:
            logger.error(f"Model initialization failed: {e}")
            raise
    
    def check_connectivity(self) -> bool:
        """Test connection to watsonx.ai"""
        try:
            # Simple test generation
            response = self.llm.generate_text(prompt="Hello", params={
                GenParams.MAX_NEW_TOKENS: 10
            })
            logger.info("✅ [bold green]watsonx.ai connectivity check passed[/bold green]")
            return bool(response)
        except Exception as e:
            logger.error(f"❌ Connectivity check failed: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def generate_text(
        self, 
        prompt: Any, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.0
    ) -> str:
        """
        Generate text using Granite/Llama LLM.
        ALWAYS uses the chat interface for reliability and to avoid deprecation.
        """
        try:
            start_time = time.time()
            
            params = {
                GenParams.MAX_NEW_TOKENS: max_tokens,
                GenParams.TEMPERATURE: temperature,
                GenParams.DECODING_METHOD: "greedy" if temperature == 0 else "sample",
            }

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": [{"type": "text", "text": system_prompt}]})
            
            if isinstance(prompt, list):
                # Multimodal or complex content
                user_content = []
                for item in prompt:
                    if item.get("type") == "text":
                        user_content.append({"type": "text", "text": item["text"]})
                    elif item.get("type") == "image_url":
                        img_url = item.get("image_url", {}).get("url", "")
                        user_content.append({
                            "type": "image_url",
                            "image_url": {"url": img_url}
                        })
                messages.append({"role": "user", "content": user_content})
            else:
                # Standard text string
                messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})

            response = self.llm.chat(messages=messages, params=params)
            result = response['choices'][0]['message']['content']

            latency = time.time() - start_time
            logger.debug(f"LLM generation completed in {latency:.2f}s")
            
            # Clean response
            result = result.strip()
            # Remove any thinking tags that might appear
            result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL).strip()
            
            return result
            
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise LLMError("watsonx.ai text generation failed", str(e))
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for text using multilingual-e5-large
        
        Args:
            text: Input text to embed
        
        Returns:
            Embedding vector (1024 dimensions)
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return None
            
            start_time = time.time()
            
            # Generate embedding
            vector = self.embeddings.embed_query(text)
            
            latency = time.time() - start_time
            logger.debug(f"Embedding generated in {latency:.2f}s (dim: {len(vector)})")
            
            return vector
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise LLMError("watsonx.ai embedding generation failed", str(e))
    
    def generate_structured(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output
        
        Args:
            prompt: User prompt
            response_schema: JSON schema for response
            system_prompt: Optional system instruction
        
        Returns:
            Parsed JSON object
        """
        try:
            # Add schema to prompt
            schema_prompt = f"{system_prompt or ''}\n\nReturn ONLY a valid JSON object matching this schema:\n{response_schema}\n\n{prompt}"
            
            response_text = self.generate_text(
                prompt=prompt,
                system_prompt=schema_prompt,
                temperature=0.0
            )
            
            # Extract JSON from response
            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # Try parsing entire response
                return json.loads(response_text)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response_text}")
            raise LLMError("Failed to parse structured response", str(e))
        except Exception as e:
            logger.error(f"Structured generation failed: {e}")
            raise LLMError("watsonx.ai structured generation failed", str(e))
    
    def request_raw_text(self, system_prompt: str, user_content: str, temperature: float = 0.0) -> str:
        """
        Compatibility method for existing codebase
        Sends a request to the LLM and returns the raw string response
        """
        return self.generate_text(prompt=user_content, system_prompt=system_prompt, temperature=temperature)

# Made with Bob
