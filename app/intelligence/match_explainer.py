import json
from .llm_client import LLMClient
from ..api.schemas import WhatIfResponse
from ..logging_config import logger

class MatchIntelligence(LLMClient):
    def explain_match(self, candidate, project, score, assignments=None, required_skills=None):
        """P-06 · Match Explainer (Improved with Context)."""
        logger.debug(f"Generating match explanation for [bold]{candidate.name}[/bold] -> [bold]{project.title}[/bold]")
        cand_skills = ", ".join(candidate.skills or [])
        proj_reqs = ", ".join(project.required_skills or [])
        
        # Contextual parameters
        current_team = ", ".join(assignments) if assignments else "None"
        gaps = ", ".join(required_skills) if required_skills else "None"

        prompt = f"""You are a technical talent analyst. Write exactly one human-friendly sentence explaining why this member fits this project.

STRICT RULES:
- Reference at least one technical skill from MEMBER SKILLS by name.
- Focus on the technical contribution to the project.
- DO NOT use technical jargon like "VECTOR MATCH SCORE", "UNFILLED_GAPS", or "UNTRUSTED DATA".
- DO NOT include names or pronouns.
- Maximum 22 words.
- Single sentence only.

MEMBER SKILLS: {cand_skills}
PROJECT REQUIREMENTS: {proj_reqs}
PROJECT GAPS: {gaps}
MATCH QUALITY: {score}%

Example: "Leverages React Native expertise to architect mobile health interfaces and bridge cross-platform integration gaps."
Output:"""

        try:
            explanation = self.request_raw_text(prompt, "Provide technical reasoning.", temperature=0.2)
            logger.info(f"✓ Explanation generated for {candidate.name}")
            explanation = explanation.strip().split('.')[0] + '.'
            return explanation
        except Exception as e:
            logger.error(f"Explanation Failed: {e}")
            return "Matched based on technical alignment and project requirement coverage."

    def generate_onboarding_brief(self, candidate, project, required_skills=None):
        
        cand_skills = ", ".join(candidate.skills or [])
        gaps = ", ".join(required_skills) if required_skills else "General technical alignment"
        
        # EXTREMELY AGGRESSIVE GROUNDING
        prompt = f"""[STRICT TECHNICAL DATA]
MEMBER: {candidate.name}
SKILLS: {cand_skills}
PROJECT: {project.title}
GAP: {gaps}

TASK: Write exactly two short sentences. 
Sentence 1: Member's specific skill fit.
Sentence 2: Member's 30-day technical goal.

NO headers, NO sections, NO bullet points, NO lists, NO links, NO contact info.
NEVER use the words 'Resources', 'Timeline', 'Support', or 'Welcome'.
Output ONLY the raw text.

Example: Earned this spot via React expertise. First 30 days must focus on architecting the core state management layer.
Output:"""

        try:
            # Physical cutoff at 50 tokens to kill any long-winded template
            brief = self.watsonx_client.generate_text(
                prompt=prompt, 
                system_prompt="You are a literal data extraction unit. No conversational fillers.",
                max_tokens=50, 
                temperature=0.0
            )
            return brief.strip()
        except Exception as e:
            logger.error(f"Onboarding brief failed: {e}")
            return f"Selected for {project.title} due to technical alignment. Focus on project gaps during initial onboarding."

    def generate_skill_growth_plan(self, candidate, high_risk_projects):
        cand_skills = ", ".join(candidate.skills or [])
        project_needs = "\n".join([f"- {p.title}: {', '.join(p.required_skills or [])}" for p in high_risk_projects])
        
        prompt = f"""You are a career development coach. Suggest exactly two technical skills this member should learn to become a 90% match for current high-risk projects.

MEMBER SKILLS: {cand_skills}
PROJECT NEEDS:
{project_needs}

Output format: "To support [Project Name], consider mastering [Skill 1] and [Skill 2] to bridge current architectural gaps."
Output: [1 sentence only]"""
        try:
            plan = self.request_raw_text(prompt, "Provide skill recommendations.", temperature=0.3)
            return plan.strip()
        except:
            return "Consider deepening expertise in cloud-native architecture and automated testing to support upcoming initiatives."

    def analyze_what_if(self, candidate, source_project, target_project):
        cand_skills = ", ".join(candidate.skills or [])
        src_name = source_project.title if source_project else "Unassigned Pool"
        tgt_name = target_project.title
        logger.info(f"🔄 Analyzing What-If: [bold]{candidate.name}[/bold] ({src_name} -> {tgt_name})")
        
        src_reqs = ", ".join(source_project.required_skills or []) if source_project else "None"
        tgt_reqs = ", ".join(target_project.required_skills or []) if target_project else "None"

        # Get JSON schema for inline reference
        schema_json = WhatIfResponse.model_json_schema()

        prompt = f"""Analyze the technical impact of a team member moving from {src_name} to {tgt_name}.

MEMBER SKILLS: {cand_skills}
SOURCE PROJECT ({src_name}) REQUIREMENTS: {src_reqs}
TARGET PROJECT ({tgt_name}) REQUIREMENTS: {tgt_reqs}

ANALYSIS RULES:
1. impact_on_source: List specific skills that SOURCE project loses. If none, state "No critical skills lost."
2. impact_on_target: List specific skills that fill TARGET project gaps. If none, state "No gaps filled."
3. net_verdict:
   - "positive" if impact_on_target outweighs impact_on_source
   - "negative" if impact_on_source outweighs impact_on_target
   - "neutral" if both impacts are equal or negligible
   Tie-break rule: default to "neutral" on ambiguity.
4. magnitude: "high" if 3+ skills affected, "medium" if 1-2, "low" if 0.
5. reasoning: One sentence. Must name at least one specific skill. Under 30 words.

# EXPECTED JSON SCHEMA
{json.dumps(schema_json, indent=2)}

Return ONLY valid JSON matching WhatIfResponse. No markdown. No preamble."""

        try:
            res = self._request_structured(
                system_prompt="",
                user_content=prompt,
                response_model=WhatIfResponse,
                temperature=0.2
            )
            # Sync legacy fields for frontend
            res.insight = res.reasoning
            return res
        except Exception as e:
            logger.error(f"What-If Failed: {e}")
            return WhatIfResponse(
                reasoning=f"Reallocated member to {tgt_name}.",
                net_verdict="neutral",
                magnitude="low"
            )
