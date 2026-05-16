
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.connection import DATABASE_URL

def generate_report():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("=== DATABASE REPORT ===")
    
    # Candidates
    print("\n--- CANDIDATES ---")
    result = session.execute(text("SELECT COUNT(*) FROM candidates"))
    total_candidates = result.scalar()
    result = session.execute(text("SELECT COUNT(*) FROM candidates WHERE is_senior = True"))
    total_seniors = result.scalar()
    print(f"Total Candidates: {total_candidates}")
    print(f"Total Seniors: {total_seniors}")
    
    result = session.execute(text("SELECT id, name, filename, is_senior, must_assign, skills, developer_summary FROM candidates LIMIT 10"))
    candidates = result.fetchall()
    print(f"Sample Candidates:")
    for c in candidates:
        print(f"ID: {c.id} | Name: {c.name} | Senior: {c.is_senior}")
        skills_str = ", ".join(c.skills or [])
        print(f"  Skills: {skills_str[:100]}...")
        summary_str = c.developer_summary or "No summary available"
        print(f"  Summary: {summary_str[:100]}...")

    # Projects
    print("\n--- PROJECTS ---")
    result = session.execute(text("SELECT COUNT(*) FROM projects"))
    total_projects = result.scalar()
    result = session.execute(text("SELECT COUNT(*) FROM projects WHERE title = 'N/A' OR title = ''"))
    unnamed_projects = result.scalar()
    print(f"Total Projects: {total_projects}")
    print(f"Projects with Missing Titles: {unnamed_projects}")
    
    result = session.execute(text("SELECT id, title, filename, mission_statement, required_skills FROM projects LIMIT 3"))
    projects = result.fetchall()
    print(f"Sample Projects:")
    for p in projects:
        print(f"ID: {p.id} | Title: {p.title}")
        print(f"  Mission: {p.mission_statement[:100]}...")
        print(f"  Skills: {', '.join(p.required_skills or [])[:100]}...")

    # Allocations
    print("\n--- ALLOCATIONS ---")
    result = session.execute(text("SELECT candidate_id, project_id, fit_score FROM allocations"))
    allocations = result.fetchall()
    print(f"Total Allocations: {len(allocations)}")
    for a in allocations:
        print(f"Candidate ID: {a.candidate_id} -> Project ID: {a.project_id} (Score: {a.fit_score})")

    # Ingestion Errors
    print("\n--- INGESTION ERRORS ---")
    result = session.execute(text("SELECT id, filename, file_type, error_message FROM ingestion_errors"))
    errors = result.fetchall()
    print(f"Total Ingestion Errors: {len(errors)}")
    for e in errors:
        print(f"ID: {e.id} | File: {e.filename} ({e.file_type}) | Error: {e.error_message[:100]}...")

    # Standard Skills
    print("\n--- STANDARD SKILLS (Top 10) ---")
    result = session.execute(text("SELECT id, name, canonical_name, category FROM standard_skills LIMIT 10"))
    skills = result.fetchall()
    for s in skills:
        print(f"ID: {s.id} | Name: {s.name} | Canonical: {s.canonical_name} | Category: {s.category}")

    session.close()

if __name__ == "__main__":
    generate_report()
