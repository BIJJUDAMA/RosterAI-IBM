from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...database.connection import get_db_session
from ...database.models import Candidate, Project, Allocation
from ...api.schemas import CandidateSchema
from ...matching.global_optimizer import compute_semantic_score
from ...logging_config import logger

router = APIRouter(prefix="/api/members", tags=["Members"])

@router.get("", response_model=List[CandidateSchema])
def list_candidates(db: Session = Depends(get_db_session)):
    return db.query(Candidate).all()

@router.put("/{id}")
def update_candidate_overrides(id: int, data: dict, db: Session = Depends(get_db_session)):
    c = db.query(Candidate).filter(Candidate.id == id).first()
    if not c: raise HTTPException(status_code=404)
    
    logger.info(f"Updating candidate data for {c.name} (ID: {id})")
    if "name" in data: c.name = data["name"]
    if "is_senior" in data: c.is_senior = data["is_senior"]
    if "must_assign" in data: c.must_assign = data["must_assign"]
    if "forbidden_project_ids" in data: c.forbidden_project_ids = data["forbidden_project_ids"]
    
    if "pinned_project_id" in data:
        new_project_id = data["pinned_project_id"]
        c.pinned_project_id = new_project_id
        
        if new_project_id:
            p = db.query(Project).filter(Project.id == new_project_id).first()
            if p:
                logger.info(f"Pinning candidate {c.name} to project {p.title}")
                score, reasons = compute_semantic_score(c, p)
                alloc = db.query(Allocation).filter(Allocation.candidate_id == c.id).first()
                if alloc:
                    alloc.project_id = p.id
                    alloc.fit_score = score
                    alloc.reasons = ["PENDING_MANUAL_EXPLANATION"] + reasons
                else:
                    db.add(Allocation(candidate_id=c.id, project_id=p.id, fit_score=score, reasons=["PENDING_MANUAL_EXPLANATION"] + reasons))
        else:
            logger.info(f"Unpinning candidate {c.name}")
            db.query(Allocation).filter(Allocation.candidate_id == c.id).delete()

    db.commit()
    return {"status": "updated"}

@router.delete("/{id}")
def delete_candidate(id: int, db: Session = Depends(get_db_session)):
    c = db.query(Candidate).filter(Candidate.id == id).first()
    if not c: raise HTTPException(status_code=404)
    
    logger.info(f"🗑️ Manual Delete: Removing member {c.name}")
    # Remove assignments first
    db.query(Allocation).filter(Allocation.candidate_id == id).delete()
    db.delete(c)
    db.commit()
    return {"status": "deleted"}
