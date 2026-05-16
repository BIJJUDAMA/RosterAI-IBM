import threading
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...database.connection import get_db_session
from ...database.models import IngestionError
from ...api.schemas import IngestionErrorSchema
from ...core.status import status_tracker
from ...services.ingestion_service import run_ingestion_thread

router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])

@router.post("")
async def process_local_assets():
    """Triggers ingestion in a separate thread."""
    status_tracker.set_status(is_ingesting=True, progress=0, current_task="Starting Ingestion")
    thread = threading.Thread(target=run_ingestion_thread)
    thread.start()
    return {"status": "ingestion_started"}

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import os
import shutil
from ...database.models import IngestionError, Candidate

@router.post("/update-resume/{candidate_id}")
async def update_member_resume(candidate_id: int, file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    c = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not c: raise HTTPException(status_code=404)
    
    # Save file to resumes/ (Overwrite if name matches, or keep old name)
    resume_dir = "resumes"
    if not os.path.exists(resume_dir): os.makedirs(resume_dir)
    
    file_path = os.path.join(resume_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Trigger re-parse for this file
    status_tracker.set_status(is_ingesting=True, progress=0, current_task=f"Updating {file.filename}")
    thread = threading.Thread(target=run_ingestion_thread, kwargs={"target_filenames": [file.filename]})
    thread.start()
    return {"status": "update_started", "filename": file.filename}

@router.get("/errors", response_model=List[IngestionErrorSchema])
def list_ingestion_errors(db: Session = Depends(get_db_session)):
    return db.query(IngestionError).all()

@router.post("/retry/all")
async def retry_all_failed_ingestions(db: Session = Depends(get_db_session)):
    errors = db.query(IngestionError).all()
    if not errors:
        return {"status": "no_errors_to_retry"}
    
    filenames = [e.filename for e in errors]
    status_tracker.set_status(is_ingesting=True, progress=0, current_task=f"Retrying {len(filenames)} files")
    thread = threading.Thread(target=run_ingestion_thread, kwargs={"target_filenames": filenames})
    thread.start()
    return {"status": "retry_started", "count": len(filenames)}

@router.post("/retry/{error_id}")
async def retry_specific_ingestion(error_id: int, db: Session = Depends(get_db_session)):
    err = db.query(IngestionError).filter(IngestionError.id == error_id).first()
    if not err:
        raise HTTPException(status_code=404, detail="Error record not found")
    
    filename = err.filename
    status_tracker.set_status(is_ingesting=True, progress=0, current_task=f"Retrying {filename}")
    thread = threading.Thread(target=run_ingestion_thread, kwargs={"target_filenames": [filename]})
    thread.start()
    return {"status": "retry_started", "filename": filename}
