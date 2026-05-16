from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...database.connection import get_db_session
from ...database.models import Candidate, Project
from ...api.schemas import SkillGapItem

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/skill-gap", response_model=List[SkillGapItem])
def get_skill_gap_report(db: Session = Depends(get_db_session)):
    """Identifies skills requested by projects that are underrepresented in the club."""
    projects = db.query(Project).all()
    candidates = db.query(Candidate).all()
    
    # 1. Aggregate Project Needs
    skill_counts = {} # {skill_name: {"count": int}}
    for p in projects:
        for s in (p.required_skills or []):
            if s not in skill_counts:
                skill_counts[s] = {"required_by": 0, "category": "Requirement"}
            skill_counts[s]["required_by"] += 1

    # 2. Count Member Skills
    member_skills = {} # {skill_name: int}
    for c in candidates:
        for s in (c.skills or []):
            member_skills[s] = member_skills.get(s, 0) + 1

    # 3. Calculate Gaps
    report = []
    for skill, info in skill_counts.items():
        m_count = member_skills.get(skill, 0)
        report.append(SkillGapItem(
            skill=skill,
            category=info["category"],
            required_by_projects=info["required_by"],
            member_count=m_count,
            gap_count=max(0, info["required_by"] - m_count)
        ))
    
    # Sort by gap_count descending
    report.sort(key=lambda x: x.gap_count, reverse=True)
    return report
