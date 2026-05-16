import threading
import io
import pandas as pd
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ...database.connection import get_db_session
from ...database.models import Candidate, Project, Allocation
from ...api.schemas import AllocationSchema, WhatIfRequest, WhatIfResponse, BatchWhatIfRequest, BatchWhatIfResponse
from ...matching.global_optimizer import compute_semantic_score
from ...core.status import status_tracker
from ...services.matching_service import run_matching_thread, match_intel
from ...logging_config import logger

router = APIRouter(tags=["Matching"])

@router.get("/api/assignments", response_model=List[AllocationSchema])
def list_allocations(db: Session = Depends(get_db_session)):
    return db.query(Allocation).all()

@router.get("/api/export")
def export_assignments(db: Session = Depends(get_db_session)):
    """Exports final allocations to an Excel file."""
    logger.info("Exporting assignments to Excel")
    allocations = db.query(Allocation).all()
    candidates = {c.id: c for c in db.query(Candidate).all()}
    projects = {p.id: p for p in db.query(Project).all()}

    data = []
    for a in allocations:
        cand = candidates.get(a.candidate_id)
        proj = projects.get(a.project_id)
        data.append({
            "Member Name": cand.name if cand else "Unknown",
            "Project Title": proj.title if proj else "Unknown",
            "Fit Score": f"{a.fit_score:.2f}",
            "Seniority": "Senior" if cand and cand.is_senior else "Junior",
            "Match Explanation": a.reasons[0] if a.reasons else ""
        })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Allocations')
    
    output.seek(0)
    logger.info(f"Excel export generated successfully with {len(data)} records")
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=project_allocations.xlsx"}
    )

@router.post("/api/match")
async def solve_organization_allocation():
    current = status_tracker.get_status()
    if current["is_matching"] == "True":
        return {"status": "already_matching"}

    status_tracker.set_status(is_matching=True, progress=0, current_task="Initializing Solver")
    thread = threading.Thread(target=run_matching_thread)
    thread.start()
    return {"status": "matching_started"}

@router.post("/api/what-if/batch", response_model=BatchWhatIfResponse)
def analyze_manual_moves_batch(req: BatchWhatIfRequest, db: Session = Depends(get_db_session)):
    """Computes technical impact for multiple target projects in one go."""
    c = db.query(Candidate).filter(Candidate.id == req.candidate_id).first()
    if not c: raise HTTPException(status_code=404, detail="Candidate not found")
    
    p_src = db.query(Project).filter(Project.id == req.source_project_id).first() if req.source_project_id else None
    src_score = 0
    if p_src:
        src_score, _ = compute_semantic_score(c, p_src)
        
    insights = {}
    for pid in req.target_project_ids:
        p_tgt = db.query(Project).filter(Project.id == pid).first()
        if not p_tgt: continue
        
        tgt_score, _ = compute_semantic_score(c, p_tgt)
        # Now returns rich object
        res_obj = match_intel.analyze_what_if(c, p_src, p_tgt)
        
        # Populate scores on the object
        res_obj.source_score_impact = -src_score if p_src else 0
        res_obj.target_score_impact = tgt_score
        
        insights[pid] = res_obj
        
    return BatchWhatIfResponse(insights=insights)

@router.post("/api/what-if", response_model=WhatIfResponse)
def analyze_manual_move(req: WhatIfRequest, db: Session = Depends(get_db_session)):
    """Legacy endpoint for single what-if analysis."""
    c = db.query(Candidate).filter(Candidate.id == req.candidate_id).first()
    p_tgt = db.query(Project).filter(Project.id == req.target_project_id).first()
    p_src = db.query(Project).filter(Project.id == req.source_project_id).first() if req.source_project_id else None
    
    if not c or not p_tgt:
        raise HTTPException(status_code=404, detail="Candidate or target project not found")
        
    tgt_score, _ = compute_semantic_score(c, p_tgt)
    src_score = 0
    if p_src:
        src_score, _ = compute_semantic_score(c, p_src)
        
    res_obj = match_intel.analyze_what_if(c, p_src, p_tgt)
    res_obj.source_score_impact = -src_score if p_src else 0
    res_obj.target_score_impact = tgt_score
    
    return res_obj

@router.post("/api/assignments/{candidate_id}/explain")
def recompute_match_explanation(candidate_id: int, db: Session = Depends(get_db_session)):
    """Generates an LLM explanation for a specific manual assignment."""
    alloc = db.query(Allocation).filter(Allocation.candidate_id == candidate_id).first()
    if not alloc: raise HTTPException(status_code=404, detail="Assignment not found")
        
    c = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    p = db.query(Project).filter(Project.id == alloc.project_id).first()
    
    if not c or not p: raise HTTPException(status_code=404, detail="Candidate or Project not found")
        
    # Gather Context for the Explainer
    # 1. Who else is on this project?
    team_member_ids = [a.candidate_id for a in db.query(Allocation).filter(Allocation.project_id == p.id).all()]
    team_members = db.query(Candidate).filter(Candidate.id.in_(team_member_ids)).all()
    team_skills = []
    for tm in team_members:
        team_skills.extend(tm.skills or [])
    
    # 2. What gaps remain?
    p_reqs = set(s.lower() for s in (p.required_skills or []))
    filled_skills = set(s.lower() for s in team_skills)
    gaps = p_reqs.difference(filled_skills)
    
    explanation = match_intel.explain_match(
        c, p, alloc.fit_score, 
        assignments=list(set(team_skills)), 
        required_skills=list(gaps)
    )
    
    new_reasons = [r for r in alloc.reasons if r != "PENDING_MANUAL_EXPLANATION"]
    new_reasons.insert(0, explanation)
    alloc.reasons = new_reasons
    db.commit()
    return {"status": "explained", "explanation": explanation}
