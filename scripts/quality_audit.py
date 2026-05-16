
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database.connection import DATABASE_URL

def quality_check():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("=== RESUME PARSING QUALITY AUDIT ===")

    # 1. Identity Health
    print("\n--- Identity Extraction ---")
    res = session.execute(text("SELECT name, filename FROM candidates WHERE name IN ('N/A', 'AI Assistant', 'Unknown', '') OR name IS NULL"))
    bad_names = res.fetchall()
    print(f"Poor Identity Extractions: {len(bad_names)}")
    for n in bad_names[:5]:
        print(f"  - File: {n.filename} | Extracted Name: {n.name}")

    # 2. Skill Density
    print("\n--- Skill Density ---")
    res = session.execute(text("SELECT id, name, json_array_length(skills) as skill_count FROM candidates ORDER BY skill_count ASC"))
    densities = res.fetchall()
    
    empty_skills = [d for d in densities if (d.skill_count or 0) == 0]
    low_skills = [d for d in densities if 0 < (d.skill_count or 0) <= 3]
    high_skills = [d for d in densities if (d.skill_count or 0) > 10]
    
    print(f"Empty Skills: {len(empty_skills)}")
    print(f"Low Skill Count (1-3): {len(low_skills)}")
    print(f"High Skill Count (>10): {len(high_skills)}")
    
    # 3. Content Depth (Summary Length)
    print("\n--- Content Depth (Developer Summaries) ---")
    res = session.execute(text("SELECT id, name, LENGTH(developer_summary) as len FROM candidates WHERE developer_summary IS NOT NULL ORDER BY len ASC"))
    lengths = res.fetchall()
    
    short_summaries = [l for l in lengths if l.len < 100]
    print(f"Short/Generic Summaries (<100 chars): {len(short_summaries)}")
    
    # 4. Qualitative Samples
    print("\n--- Qualitative Samples (Top Performers) ---")
    res = session.execute(text("SELECT name, skills, developer_summary FROM candidates WHERE developer_summary IS NOT NULL AND json_array_length(skills) > 5 LIMIT 3"))
    samples = res.fetchall()
    for s in samples:
        print(f"NAME: {s.name}")
        print(f"SUMMARY: {s.developer_summary[:200]}...")
        print(f"SKILLS: {', '.join(s.skills)}")
        print("-" * 30)

    session.close()

if __name__ == "__main__":
    quality_check()
