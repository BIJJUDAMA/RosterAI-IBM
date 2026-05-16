from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime

class IngestionErrorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_type: str
    error_message: str
    occurred_at: datetime

class StandardSkillSchema(BaseModel):
    canonical_name: str
    category: str
    aliases: List[str] = []
    confident: bool = True
    description: Optional[str] = None

class UniversalTechnicalProfile(BaseModel):
    entity_type: Literal["member", "project"]
    name: str
    developer_summary: Optional[str] = None # For members
    mission_statement: Optional[str] = None # For projects
    technical_intent: Optional[str] = None # For projects
    skills: List[str]
    seniority: Literal["junior", "mid", "senior", "unknown"] = "junior"
    domain_focus: List[str]
    synergy_insight: Optional[str] = None
    compatibility_insights: Optional[Dict[str, str]] = {}
    confidence_score: float = 1.0
    consistency_warnings: List[str] = []
    raw_source_hash: Optional[str] = None
    unresolved_terms: Optional[List[str]] = []
    tool_calls: Optional[List[Dict[str, Any]]] = []

class CandidateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    filename: str
    
    # Flat Fields
    developer_summary: Optional[str] = None
    skills: List[str] = []
    domain_focus: List[str] = []
    compatibility_insights: Dict[str, str] = {}
    
    is_senior: bool
    must_assign: bool
    pinned_project_id: Optional[int] = None
    forbidden_project_ids: Optional[List[int]] = []

class ProjectSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    filename: str
    
    # Flat Fields
    mission_statement: Optional[str] = None
    technical_intent: Optional[str] = None
    required_skills: List[str] = []
    compatibility_insights: Dict[str, str] = {}

class AllocationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: int
    project_id: int
    fit_score: int
    reasons: Optional[List[str]] = []

class WhatIfRequest(BaseModel):
    candidate_id: int
    source_project_id: Optional[int] = None
    target_project_id: int

class WhatIfResponse(BaseModel):
    impact_on_source: List[str] = []
    impact_on_target: List[str] = []
    net_verdict: Literal["positive", "neutral", "negative"]
    magnitude: Optional[Literal["high", "medium", "low"]] = "medium"
    reasoning: str
    insight: Optional[str] = None # Legacy support
    reversible: bool = True
    confidence: float = 1.0
    source_score_impact: Optional[int] = 0
    target_score_impact: Optional[int] = 0

# Note: Global WhatIf Response uses the specialized WhatIfResponse above

class BatchWhatIfRequest(BaseModel):
    candidate_id: int
    source_project_id: Optional[int] = None
    target_project_ids: List[int]

class BatchWhatIfResponse(BaseModel):
    insights: Dict[int, WhatIfResponse]

class SkillGapItem(BaseModel):
    skill: str
    category: str # Language, Framework, Tool, Concept
    required_by_projects: int
    member_count: int
    gap_count: int

class RawTechnicalFacts(BaseModel):
    """Internal schema for intermediate analysis phases."""
    name: Optional[str] = Field(None, description="Extracted name or title")
    detected_skills: List[str] = Field(default_factory=list, description="Raw technical keywords found")
    seniority_signals: List[str] = Field(default_factory=list, description="Mentions of years of experience or levels")
    domain_keywords: List[str] = Field(default_factory=list, description="Industry or technical domains identified")
    summary_snippet: Optional[str] = Field(None, description="A 1-sentence technical summary")
    confidence: float = 0.5
