import json
import logging
import hashlib
from .llm_client import LLMClient
from .agent_service import agent_brain
from ..api.schemas import UniversalTechnicalProfile

from ..logging_config import logger
from ..exceptions import LLMError, LLMParseError
class ResumeIntelligence(LLMClient):
    def parse_resume(self, text, image_paths=None, db_session=None, file_path=None):
        logger.info(f"Delegating resume parsing to LangGraph Agent Brain (Markdown size: {len(text) if text else 0})")

        # Unique thread ID based on text hash + filename for persistent memory
        import hashlib
        # Rule: Vision resumes (empty text) must be separated by filename to avoid collisions
        unique_seed = f"{file_path}_{text}" if file_path else text
        thread_id = hashlib.md5(unique_seed.encode() if text or file_path else b"empty").hexdigest()

        try:

            parsed = agent_brain.process_document(
                content_type="member", 
                markdown=text,
                image_paths=image_paths or [],
                thread_id=f"resume_{thread_id}",
                file_path=file_path
            )

            if not parsed:
                logger.warning(f"⚠️ Agent failed to extract data from {file_path}. Returning fallback.")
                return {
                    "entity_type": "member",
                    "name": f"DOC_{hashlib.md5(file_path.encode()).hexdigest()[:8]}" if file_path else "UNKNOWN_MEMBER",
                    "skills": [],
                    "seniority": "unknown",
                    "domain_focus": [],
                    "developer_summary": "Auto-ingested document (Extraction failed).",
                    "embedding": self.get_embedding("Unknown member profile")
                }

            
            # Post-processing taxonomy if agent found unresolved terms
            if db_session and parsed.get("unresolved_terms"):
                logger.info(f"Researching {len(parsed['unresolved_terms'])} unresolved terms...")
                for term in parsed["unresolved_terms"]:
                    info = self.search_technical_taxonomy(term, db_session)
                    if info:
                        canonical = info.get("canonical_name", term)
                        if canonical not in parsed["skills"]:
                            parsed["skills"].append(canonical)
                
                parsed["unresolved_terms"] = []

            # Semantic Embedding
            profile_summary = f"{parsed.get('name', '')} {parsed.get('seniority', '')} in {', '.join(parsed.get('domain_focus', []))}. "
            profile_summary += f"Skills: {', '.join(parsed.get('skills', []))}."
            if parsed.get('synergy_insight'):
                profile_summary += f" Club Insight: {parsed['synergy_insight']}"
            
            logger.info("Embedding construction started for profile...")
            parsed["embedding"] = self.get_embedding(profile_summary)
            
            return parsed
        except Exception as e:
            logger.error(f"Agent-based Resume Parsing Failed: {e}")
            raise LLMError(f"Failed to process resume data", str(e))

resume_intel = ResumeIntelligence()
