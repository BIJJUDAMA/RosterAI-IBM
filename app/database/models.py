from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from .connection import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    filename = Column(String, unique=True)
    
    
    developer_summary = Column(String)
    skills = Column(JSON) # List of canonical skill names
    domain_focus = Column(JSON) # List of domains
    compatibility_insights = Column(JSON) # Map of {Missing: Pool}
    raw_source_hash = Column(String)
    embedding_model_name = Column(String)
    embedding = Column(Vector(1024)) # IBM watsonx.ai (multilingual-e5-large) is 1024 dims
    
    # Overrides and Constraints
    is_senior = Column(Boolean, default=False) 
    must_assign = Column(Boolean, default=False)
    pinned_project_id = Column(Integer, nullable=True) # Locked assignment
    forbidden_project_ids = Column(JSON, default=list) # List of IDs

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    filename = Column(String, unique=True)
    
    # Refactored Fields
    mission_statement = Column(String)
    technical_intent = Column(String) # Fluid technical needs
    required_skills = Column(JSON) # List of skills
    compatibility_insights = Column(JSON)
    raw_source_hash = Column(String)
    embedding_model_name = Column(String)
    embedding = Column(Vector(1024))

class Allocation(Base):
    __tablename__ = "allocations"

    candidate_id = Column(Integer, ForeignKey("candidates.id"), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    fit_score = Column(Integer)
    reasons = Column(JSON)

class IngestionError(Base):
    __tablename__ = "ingestion_errors"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    file_type = Column(String) # "resume" or "project"
    error_message = Column(String)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())

class StandardSkill(Base):
    __tablename__ = "standard_skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # e.g., "ReactJS"
    canonical_name = Column(String) # e.g., "React"
    category = Column(String) # e.g., "Framework", "Language", "Tool"
    description = Column(String, nullable=True) # Context from web search
