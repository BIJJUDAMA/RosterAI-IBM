from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...database.connection import get_db_session
from ...database.models import Project
from ...api.schemas import ProjectSchema
from ...logging_config import logger

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.get("", response_model=List[ProjectSchema])
def list_projects(db: Session = Depends(get_db_session)):
    return db.query(Project).all()

@router.put("/{id}")
def update_project_overrides(id: int, data: dict, db: Session = Depends(get_db_session)):
    p = db.query(Project).filter(Project.id == id).first()
    if not p: raise HTTPException(status_code=404)
    logger.info(f"Updating project overrides for {p.title} (ID: {id})")
    if "complexity" in data: p.complexity = data["complexity"]
    db.commit()
    return {"status": "updated"}

@router.patch("/{id}")
def update_project_title(id: int, data: dict, db: Session = Depends(get_db_session)):
    p = db.query(Project).filter(Project.id == id).first()
    if not p: raise HTTPException(status_code=404)
    if "title" in data:
        old_title = p.title
        p.title = data["title"]
        logger.info(f"✏️ Project renamed: {old_title} -> {p.title}")
        db.commit()
    return {"status": "updated", "title": p.title}

@router.delete("/{id}")
def delete_project(id: int, db: Session = Depends(get_db_session)):
    p = db.query(Project).filter(Project.id == id).first()
    if not p: raise HTTPException(status_code=404)
    
    logger.info(f"🗑️ Manual Delete: Removing project {p.title}")
    # Remove assignments and project
    from ...database.models import Allocation
    db.query(Allocation).filter(Allocation.project_id == id).delete()
    db.delete(p)
    db.commit()
    return {"status": "deleted"}

@router.delete("")
def delete_all_projects(db: Session = Depends(get_db_session)):
    logger.info("🧨 Batch Delete: Purging ALL projects")
    from ...database.models import Allocation
    db.query(Allocation).delete()
    db.query(Project).delete()
    db.commit()
    return {"status": "all projects deleted"}
