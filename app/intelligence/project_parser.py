import json
import logging
from .llm_client import LLMClient
from .agent_service import agent_brain
from ..api.schemas import UniversalTechnicalProfile

from ..logging_config import logger
from ..exceptions import LLMError, LLMParseError

from ..processing.document_extractor import extract_raw_text

class ProjectIntelligence(LLMClient):
    def parse_project(self, text, image_paths=None, db_session=None, file_path=None):
        logger.info(f"Analyzing project intelligence (Slides: {len(image_paths) if image_paths else 0})")
        
        native_text = extract_raw_text(file_path) if file_path else ""
        
        import hashlib
        file_id = hashlib.md5(file_path.encode()).hexdigest() if file_path else "unknown"
        thread_id = f"project_{file_id}"
        
        try:
            # Delegate Hybrid Loop to LangGraph
            parsed = agent_brain.process_document(
                content_type="project",
                markdown=native_text, 
                image_paths=image_paths or [],
                thread_id=thread_id,
                file_path=file_path
            )
            
            if not parsed:
                logger.warning(f"⚠️ Agent failed to extract data from {file_path}. Returning fallback.")
                return {
                    "entity_type": "project",
                    "name": f"PROJECT_{file_id[:8]}",
                    "skills": [],
                    "domain_focus": [],
                    "mission_statement": "Manual review required.",
                    "technical_intent": "Extraction failed.",
                    "embedding": self.get_embedding("Unknown project")
                }
            
            # Semantic Embedding (Deterministic scoring)
            req_text = f"{parsed.get('name', '')} {', '.join(parsed.get('skills', []))} {', '.join(parsed.get('domain_focus', []))}"
            logger.info("Embedding construction started for project requirement...")
            parsed["embedding"] = self.get_embedding(req_text)
            
            return parsed
        except Exception as e:
            logger.error(f"Agent-based Project Extraction Failed: {e}")
            raise LLMError(f"Failed to process project data", str(e))

project_intel = ProjectIntelligence()
