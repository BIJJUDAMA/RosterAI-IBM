import logging
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from ..database.connection import SessionLocal
from ..database.models import Candidate, Project, Allocation
from ..matching.global_optimizer import run_global_optimization, generate_visual_graph
from ..intelligence.match_explainer import MatchIntelligence
from ..core.status import status_tracker
from ..core.websocket import manager
from ..logging_config import logger, console

match_intel = MatchIntelligence()

def run_matching_thread():
    db = SessionLocal()
    try:
        candidates = db.query(Candidate).all()
        projects = db.query(Project).all()
        current_allocations = db.query(Allocation).all()
        
        if not candidates or not projects:
            raise ValueError("Insufficient data to run matching. Ensure members and projects are ingested.")

        status_tracker.set_status(is_matching=True, progress=0.1, current_task="Running Solver Optimization")
        manager.thread_safe_broadcast(status_tracker.get_status())

        results = run_global_optimization(candidates, projects, current_allocations)

        if not results:
            raise ValueError("Solver failed to find a feasible solution. Check constraints and team sizes.")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress_bar:
            task = progress_bar.add_task("[yellow]Explaining matches...", total=len(results))
            
            for idx, res in enumerate(results):
                try:
                    progress = (idx / len(results)) * 0.8 + 0.1 # Normalize progress
                    status_tracker.set_status(progress=progress, current_task=f"Explaining Result {idx+1}/{len(results)}")
                    manager.thread_safe_broadcast(status_tracker.get_status())
                    
                    c = next(cand for cand in candidates if cand.id == res["candidate_id"])
                    p = next(proj for proj in projects if proj.id == res["project_id"])
                    
                    explanation = match_intel.explain_match(c, p, res["score"])
                    res["reasons"].insert(0, explanation)

                    # Generate Onboarding Brief (Jumpstart Document)
                    try:
                        # What gaps remain for this specific project?
                        p_reqs = set(s.lower() for s in (p.required_skills or []))
                        assigned_to_p = [r["candidate_id"] for r in results if r["project_id"] == p.id]
                        team_skills_so_far = []
                        for mid in assigned_to_p:
                            tm = next((cand for cand in candidates if cand.id == mid), None)
                            if tm: team_skills_so_far.extend(tm.skills or [])
                        
                        filled_skills = set(s.lower() for s in team_skills_so_far)
                        gaps = p_reqs.difference(filled_skills)
                        
                        brief = match_intel.generate_onboarding_brief(c, p, required_skills=list(gaps))
                        res["reasons"].append(f"ONBOARDING_BRIEF: {brief}")
                    except Exception as e:
                        logger.warning(f"Onboarding brief failed for {c.name}: {e}")

                    # Send incremental update to frontend
                    manager.thread_safe_broadcast({
                        "type": "assignment_update",
                        "data": res
                    })
                    progress_bar.advance(task)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to generate explanation for {res['candidate_id']}: {e}")
                    res["reasons"].insert(0, "Matched based on technical alignment.")

        # Atomic update of allocations
        db.query(Allocation).delete()
        for res in results:
            db.add(Allocation(candidate_id=res["candidate_id"], project_id=res["project_id"], fit_score=res["score"], reasons=res["reasons"]))
        db.commit()

        # Update Visual Map
        status_tracker.set_status(progress=0.95, current_task="Generating Topology Map")
        generate_visual_graph(candidates, projects, results)

        status_tracker.set_status(is_matching=False, progress=1, current_task="Ready")
        manager.thread_safe_broadcast(status_tracker.get_status())
    except Exception as e:
        db.rollback()
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.exception(f"❌ Fatal matching error: {error_msg}")
        status_tracker.set_status(is_matching=False, current_task=f"Error: {error_msg}")
        manager.thread_safe_broadcast(status_tracker.get_status())
    finally:
        db.close()
