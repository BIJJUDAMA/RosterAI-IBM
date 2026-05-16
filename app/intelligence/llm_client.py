import os
import base64
import re
import json
import hashlib
import redis
import instructor
from ddgs import DDGS
from PIL import Image
import io
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

load_dotenv()

from ..logging_config import logger
from ..exceptions import LLMConnectionError, LLMTimeoutError, LLMParseError, LLMError
from ..cloud.watsonx_client import WatsonxClient

# Redis Configuration for Embedding Cache
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=2, decode_responses=True)

class LLMClient:
    """Client for interacting with IBM watsonx.ai"""
    def clean_json_response(self, text: str) -> str:
        if not text: return ""
        start_idx = text.find('{')
        if start_idx == -1: return text
        
        depth = 0
        for i in range(start_idx, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    return text[start_idx:i+1]
        return text[start_idx:]

    def __init__(self, model_name=None):
        # Initialize IBM watsonx.ai client
        try:
            self.watsonx_client = WatsonxClient()
            self.model_name = self.watsonx_client.model_id
            
            # Initialize Instructor for structured data extraction
            # We create a shim to bridge the OpenAI-style call to Watsonx
            from types import SimpleNamespace
            
            def watsonx_create(**kwargs):
                messages = kwargs.get("messages", [])
                system_prompt = ""
                user_content = ""
                
                for msg in messages:
                    if msg["role"] == "system":
                        system_prompt = msg["content"]
                    elif msg["role"] == "user":
                        user_content = msg["content"]
                
                # Handle potential list content (multimodal) from the agent
                if isinstance(user_content, list):
                    text_parts = [item["text"] for item in user_content if item["type"] == "text"]
                    user_content = " ".join(text_parts)

                response_text = self.watsonx_client.request_raw_text(system_prompt, user_content)
                logger.debug(f"📡 [LLM] Context size: {len(system_prompt) + len(user_content)} chars")
                
                # ROBUST JSON EXTRACTION
                response_text = self.clean_json_response(response_text)

                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(
                                content=response_text,
                                role="assistant"
                            ),
                            finish_reason="stop"
                        )
                    ]
                )

            # Patch the shim with Instructor
            patched_create = instructor.patch(
                create=watsonx_create,
                mode=instructor.Mode.JSON
            )
            
            # Build the nested structure: client.chat.completions.create
            self.client = SimpleNamespace(
                chat=SimpleNamespace(
                    completions=SimpleNamespace(
                        create=patched_create
                    )
                )
            )
            
            logger.info(f"✅ [bold green]LLMClient initialized with IBM watsonx.ai[/bold green]: {self.model_name}")
        except Exception as e:
            logger.error(f"❌ [bold red]Failed to initialize watsonx.ai client[/bold red]: {e}")
            raise LLMConnectionError("Could not initialize watsonx.ai", str(e))

    def check_connectivity(self):
        """Heartbeat to verify watsonx.ai is ready."""
        try:
            logger.info(f"📡 [bold blue]Checking IBM watsonx.ai connectivity[/bold blue]...")
            result = self.watsonx_client.check_connectivity()
            if result:
                logger.info(f"✅ [bold green]IBM watsonx.ai is active and ready[/bold green]")
            return result
        except Exception as e:
            logger.error(f"❌ [bold red]watsonx.ai Unreachable[/bold red]: {e}")
            return False

    @staticmethod
    def encode_image_to_base64(image_path):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image path not found: {image_path}")
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def request_raw_text(self, system_prompt, user_content, temperature=0.0):
        try:
            # Use watsonx.ai client
            response = self.watsonx_client.request_raw_text(system_prompt, user_content, temperature=temperature)
            return response
        except Exception as e:
            logger.error(f"LLM Request Failed: {str(e)}")
            raise LLMError(f"Unexpected LLM error occurred", str(e))

    def _request_structured(self, system_prompt: str, user_content: str, response_model, temperature: float = 0.0):
        """Utility for structured requests with a built-in JSON repair retry loop."""
        max_retries = 2
        last_response = ""

        current_system = system_prompt
        current_user = user_content

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    # Repair prompt as requested in HANDOFF.md
                    current_system = "" 
                    current_user = f"""The following JSON is malformed. Fix ONLY the syntax errors. Do not change any values.
Return only the corrected JSON object.

MALFORMED INPUT:
{last_response}"""
                    logger.warning(f"🔄 JSON Repair Attempt {attempt}/{max_retries}...")

                # 1. Get raw text
                last_response = self.request_raw_text(current_system, current_user, temperature=temperature)

                # 2. Extract and Clean JSON block
                cleaned_json = self.clean_json_response(last_response)

                # 3. Validate with Pydantic
                return response_model.model_validate_json(cleaned_json)
            except Exception as e:
                logger.warning(f"⚠️ Structured request failed (Attempt {attempt+1}): {e}")
                if attempt == max_retries:
                    logger.error(f"❌ Final validation failure. JSON was:\n{cleaned_json}")
                    raise e
        return None

    def get_embedding(self, text):
        """Generates an embedding vector with Redis caching using IBM watsonx.ai"""
        if not text: return None
        
        # Use watsonx.ai embedding model
        embed_model = self.watsonx_client.embedding_model_id
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        cache_key = f"embed:{embed_model}:{text_hash}"

        if cache:
            try:
                cached_vec = cache.get(cache_key)
                if cached_vec:
                    logger.debug(f"⚡ [bold green]Embedding Cache Hit[/bold green] for model: {embed_model}")
                    return json.loads(cached_vec)
            except: pass

        try:
            logger.info(f"📡 [bold blue]Generating Embedding[/bold blue] using IBM watsonx.ai: {embed_model}")
            # Use watsonx.ai client
            vector = self.watsonx_client.get_embedding(text)
            
            if cache and vector:
                cache.setex(cache_key, 3600 * 24 * 30, json.dumps(vector))
            return vector
        except Exception as e:
            logger.error(f"❌ [bold red]Embedding Failed[/bold red]: {e}")
            return None

    def get_standard_skills(self, db_session):
        """Retrieves a unique set of canonical skill names from the database."""
        from ..database.models import StandardSkill
        skills = db_session.query(StandardSkill.canonical_name).all()
        return list(set(s[0] for s in skills))

    def search_technical_taxonomy(self, query: str, db_session):
        """P-05 · Tech Taxonomy Researcher using IBM watsonx.ai"""
        from ..database.models import StandardSkill
        from ..api.schemas import StandardSkillSchema
        
        # 1. Check Cache
        existing = db_session.query(StandardSkill).filter(StandardSkill.name == query).first()
        if existing:
            return {"canonical_name": existing.canonical_name, "category": existing.category}

        # 2. Internet Search
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(f"{query} software development category tech stack", max_results=3))
            
            context = "\n".join([r['body'] for r in results])
            
            # P-05 · Tech Taxonomy Researcher (Improved)
            system_prompt = """You are a technical taxonomy classification engine. Classify an unrecognized technology term using the provided web search results.

CLASSIFICATION RULES:
1. Derive the canonical name from search result titles or descriptions — not assumed knowledge.
2. Assign exactly one category: Language | Framework | Library | Tool | Database | Cloud_Service | Concept
3. If multiple categories apply, pick the primary usage context from the search results.
4. Set confident: false if search results are ambiguous, unrelated, or insufficient.
5. If confident: false, set canonical_name to the input term verbatim and category to "Concept" as a safe fallback.

Return ONLY valid JSON, no markdown:
{ "canonical_name": string, "category": string, "aliases": [string], "confident": boolean }"""

            user_prompt = f"""UNRECOGNIZED TERM: "{query}"
WEB SEARCH RESULTS: {context}"""

            # Use watsonx.ai for structured generation
            response_text = self.watsonx_client.request_raw_text(system_prompt, user_prompt)
            
            # ROBUST JSON EXTRACTION
            response_text = self.clean_json_response(response_text)
            res_dict = json.loads(response_text)
            
            # Apply safe fallback if confidence is low
            if not res_dict.get("confident", True):
                res_dict["canonical_name"] = query
                res_dict["category"] = "Concept"

            # 3. Cache Result
            new_skill = StandardSkill(
                name=query,
                canonical_name=res_dict.get("canonical_name", query),
                category=res_dict.get("category", "Tool"),
                description=f"Aliases: {', '.join(res_dict.get('aliases', []))}"
            )
            db_session.add(new_skill)
            db_session.commit()
            
            return res_dict
        except Exception as e:
            logger.error(f"Taxonomy Failed for {query}: {e}")
            return None

    def analyze_image_region(self, image_path: str, box: List[int]):
        try:
            with Image.open(image_path) as img:
                cropped = img.crop(box)
                buffered = io.BytesIO()
                cropped.save(buffered, format="PNG")
                return base64.b64encode(buffered.getvalue()).decode('utf-8')
        except Exception as e:
            logger.error(f"Zoom Failed: {e}")
            return None

    def docling_parse(self, file_path: str):
        """Dynamic tool call for high-precision Markdown extraction from PDF/Images."""
        from ..processing.document_extractor import docling_converter
        try:
            logger.info(f"Agent requested high-precision parse for: [bold]{file_path}[/bold]")
            result = docling_converter.convert(file_path)
            return result.document.export_to_markdown()
        except Exception as e:
            logger.error(f"Docling Tool Parse Failed: {e}")
            return f"Error parsing document with Docling: {str(e)}"
