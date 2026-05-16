import os
import logging
import hashlib
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

from ..database.connection import SessionLocal
from tenacity import retry, stop_after_attempt, wait_exponential
from ..database.models import Candidate, Project, IngestionError
from ..processing.document_extractor import extract_raw_text, pdf_to_images, has_native_text
from ..core.status import status_tracker
from ..core.websocket import manager
from ..logging_config import logger, console
from ..intelligence.resume_parser import resume_intel
from ..intelligence.project_parser import project_intel
from ..cloud.watsonx_client import WatsonxClient

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    before_sleep=lambda retry_state: logger.info(f"Retrying ingestion task (attempt {retry_state.attempt_number})...")
)
def process_resume_task(f, resume_dir, temp_dir, db):
    log = logger.bind(filename=f)
    try:
        log.info(f"Processing resume: {f}")
        path = os.path.join(resume_dir, f)
        embed_model = WatsonxClient().embedding_model_id
        
        with open(path, "rb") as bf:
            file_hash = hashlib.sha256(bf.read()).hexdigest()
            
        existing_candidate = db.query(Candidate).filter(Candidate.filename == f).first()
        if existing_candidate and existing_candidate.raw_source_hash == file_hash and existing_candidate.embedding_model_name == embed_model:
            log.info(f"⏭️ Skipping {f}: Content hash and embedding model identical.")
            return True

        text = ""
        imgs = []
        if f.lower().endswith(".pdf"):
            if has_native_text(path):
                log.info(f"✓ Native text detected. High-fidelity extraction.")
                text = extract_raw_text(path)
            else:
                log.info(f"🚩 No native text. Vision LLM analysis.")
                imgs = pdf_to_images(path, temp_dir)
        else:
            text = extract_raw_text(path)
        
        parsed = resume_intel.parse_resume(text, imgs, db_session=db, file_path=path)
        if not parsed:
            raise ValueError("Extraction produced no data.")
            
        parsed["raw_source_hash"] = file_hash
        embedding = parsed.pop("embedding", None)
        
        if existing_candidate:
            log.info(f"🔄 Updating existing member: {existing_candidate.name}")
            existing_candidate.developer_summary = parsed.get("developer_summary")
            existing_candidate.skills = parsed.get("skills")
            existing_candidate.domain_focus = parsed.get("domain_focus")
            existing_candidate.raw_source_hash = file_hash
            existing_candidate.embedding_model_name = embed_model
            existing_candidate.embedding = embedding
        else:
            db.add(Candidate(
                name=parsed.get("name", f), 
                filename=f, 
                developer_summary=parsed.get("developer_summary"),
                skills=parsed.get("skills"),
                domain_focus=parsed.get("domain_focus"),
                raw_source_hash=file_hash,
                embedding_model_name=embed_model,
                embedding=embedding,
                is_senior=False
            ))
            
        db.query(IngestionError).filter(IngestionError.filename == f).delete()
        db.commit()
        manager.thread_safe_broadcast({"type": "refresh_data"})
        log.success(f"Successfully ingested resume: {f}")
        return True
    except Exception as e:
        db.rollback()
        error_msg = f"{type(e).__name__}: {str(e)}"
        log.error(f"❌ Failed to ingest resume {f}: {error_msg}")
        
        existing_err = db.query(IngestionError).filter(IngestionError.filename == f).first()
        if existing_err:
            existing_err.error_message = error_msg
            existing_err.occurred_at = func.now()
        else:
            db.add(IngestionError(filename=f, file_type="resume", error_message=error_msg))
        db.commit()
        
        manager.thread_safe_broadcast({
            "type": "ingestion_error",
            "filename": f,
            "error": error_msg
        })
        raise 

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    before_sleep=lambda retry_state: logger.info(f"Retrying ingestion task (attempt {retry_state.attempt_number})...")
)
def process_project_task(f, project_dir, temp_dir, db):
    log = logger.bind(filename=f)
    try:
        log.info(f"Processing Project: {f}")
        path = os.path.join(project_dir, f)
        if not f.lower().endswith(".pdf"): return False
        embed_model = WatsonxClient().embedding_model_id

        with open(path, "rb") as bf:
            file_hash = hashlib.sha256(bf.read()).hexdigest()

        existing_project = db.query(Project).filter(Project.filename == f).first()
        if existing_project and existing_project.raw_source_hash == file_hash and existing_project.embedding_model_name == embed_model:
            log.info(f"⏭️ Skipping Project {f}: Content hash identical.")
            return True

        imgs = pdf_to_images(path, temp_dir)
        parsed = project_intel.parse_project(None, imgs, db_session=db, file_path=path)
        if not parsed:
            raise ValueError("Project extraction produced no data.")

        parsed["raw_source_hash"] = file_hash
        embedding = parsed.pop("embedding", None)
        
        if existing_project:
            log.info(f"🔄 Updating existing project: {existing_project.title}")
            existing_project.mission_statement = parsed.get("mission_statement")
            existing_project.technical_intent = parsed.get("technical_intent")
            existing_project.required_skills = parsed.get("skills")
            existing_project.raw_source_hash = file_hash
            existing_project.embedding_model_name = embed_model
            existing_project.embedding = embedding
        else:
            db.add(Project(
                title=parsed.get("name", f), 
                filename=f, 
                mission_statement=parsed.get("mission_statement"),
                technical_intent=parsed.get("technical_intent"),
                required_skills=parsed.get("skills"),
                raw_source_hash=file_hash,
                embedding_model_name=embed_model,
                embedding=embedding
            ))
            
        db.query(IngestionError).filter(IngestionError.filename == f).delete()
        db.commit()
        manager.thread_safe_broadcast({"type": "refresh_data"})
        log.success(f"Successfully ingested project: {f}")

        if imgs:
            for img in imgs:
                try: os.remove(img)
                except: pass
        return True
    except Exception as e:
        db.rollback()
        error_msg = f"{type(e).__name__}: {str(e)}"
        log.error(f"❌ Failed to ingest project {f}: {error_msg}")
        
        existing_err = db.query(IngestionError).filter(IngestionError.filename == f).first()
        if existing_err:
            existing_err.error_message = error_msg
            existing_err.occurred_at = func.now()
        else:
            db.add(IngestionError(filename=f, file_type="project", error_message=error_msg))
        db.commit()

        manager.thread_safe_broadcast({
            "type": "ingestion_error",
            "filename": f,
            "error": error_msg
        })
        raise

from concurrent.futures import ThreadPoolExecutor, as_completed

def run_ingestion_thread(target_filenames: Optional[List[str]] = None):
    db = SessionLocal()
    try:
        import psutil
        available_ram_gb = psutil.virtual_memory().available / (1024 ** 3)
        if available_ram_gb < 1.0:
            logger.error(f"❌ Low Memory: {available_ram_gb:.2f}GB available. Ingestion aborted.")
            status_tracker.set_status(is_ingesting=False, current_task=f"Error: Low RAM ({available_ram_gb:.2f}GB)")
            manager.thread_safe_broadcast(status_tracker.get_status())
            return

        resume_dir, project_dir = "resumes", "projects"
        temp_dir = "temp_processing"
        
        resume_files = []
        if os.path.exists(resume_dir):
            resume_files = [f for f in os.listdir(resume_dir)]
            if target_filenames:
                resume_files = [f for f in resume_files if f in target_filenames]
                
        project_files = []
        if os.path.exists(project_dir):
            project_files = [f for f in os.listdir(project_dir) if f.lower().endswith(".pdf")]
            if target_filenames:
                project_files = [f for f in project_files if f in target_filenames]

        total_tasks = len(resume_files) + len(project_files)
        if total_tasks == 0:
            status_tracker.set_status(is_ingesting=False, progress=1, current_task="No files found")
            return

        status_tracker.set_status(is_ingesting=True, progress=0, current_task="Starting Parallel Ingestion")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress_bar:
            task_id = progress_bar.add_task("[bold cyan]Processing Batch...", total=total_tasks)
            
            with ThreadPoolExecutor(max_workers=1) as executor:
                futures = []
                for f in resume_files:
                    futures.append(executor.submit(process_resume_task, f, resume_dir, temp_dir, db))
                for f in project_files:
                    futures.append(executor.submit(process_project_task, f, project_dir, temp_dir, db))
                
                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    progress = completed / total_tasks
                    status_tracker.set_status(progress=progress, current_task=f"Completed {completed}/{total_tasks}")
                    manager.thread_safe_broadcast(status_tracker.get_status())
                    progress_bar.advance(task_id)
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Task failed in parallel batch: {e}")

        status_tracker.set_status(is_ingesting=False, progress=1, current_task="Ready")
        manager.thread_safe_broadcast(status_tracker.get_status())
    except Exception as e:
        logger.exception(f"Fatal ingestion error: {e}")
        status_tracker.set_status(is_ingesting=False, current_task=f"Error: {str(e)}")
        manager.thread_safe_broadcast(status_tracker.get_status())
    finally:
        db.close()
