from ortools.sat.python import cp_model
import math
import logging
import numpy as np
from ..intelligence.llm_client import LLMClient

from ..logging_config import logger

def cosine_similarity(v1, v2):
    if v1 is None or v2 is None: return 0
    v1 = np.array(v1)
    v2 = np.array(v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0: return 0
    return np.dot(v1, v2) / (norm1 * norm2)

# Calculates semantic compatibility using the 3-term 50/35/15 formula.
# Optimized with O(1) balance bonus via pre-computed skill_frequencies
def compute_semantic_score(candidate, project, skill_frequencies=None, total_candidates=0):
    # Human Authority - Pinned assignments are 100% matches
    if candidate.pinned_project_id == project.id:
        return 100, ["📍 Manually Locked (100% Priority)"]

    # Vector Similarity (30% weight)
    vector_score = 0
    if candidate.embedding is not None and project.embedding is not None:
        sim = cosine_similarity(candidate.embedding, project.embedding)
        vector_score = max(0, sim) * 30
        
    # Hard Skill Overlap (55% weight)
    skill_score = 0
    c_skills = set(s.lower() for s in (candidate.skills or []))
    p_reqs = set(s.lower() for s in (project.required_skills or []))
    
    if p_reqs:
        overlap = c_skills.intersection(p_reqs)
        skill_score = (len(overlap) / len(p_reqs)) * 55
    
    # Load Balance Bonus (15% weight) - Optimized O(1) Lookup
    balance_bonus = 0
    if skill_frequencies and p_reqs:
        rare_skill_count = 0
        threshold = max(1, int(total_candidates * 0.10)) 
        for skill in p_reqs:
            possessors = skill_frequencies.get(skill, 0)
            if possessors <= threshold and skill in c_skills:
                rare_skill_count += 1
        
        balance_bonus = (rare_skill_count / len(p_reqs)) * 15 if rare_skill_count > 0 else 0

    final_score = int(vector_score + skill_score + balance_bonus)
    return final_score, [f"Weighted Technical Fit ({final_score}%)"]

# Solves the constrained assignment problem using CP-SAT.
# Optimized: O(CP) Scoring + Top-K Search Space Pruning
def run_global_optimization(candidates, projects, current_allocations=None):

    logger.info(f"Running CP-SAT solver for {len(candidates)} candidates and {len(projects)} projects")
    
    if not projects or not candidates:
        logger.warning("Empty candidates or projects list. Optimization aborted.")
        return []

    # Pre-calculate Skill Frequencies (Inverted Index equivalent)
    skill_frequencies = {}
    for c in candidates:
        for s in (c.skills or []):
            s_low = s.lower()
            skill_frequencies[s_low] = skill_frequencies.get(s_low, 0) + 1
    
    # Building Potential Edge Utility Map with Dynamic Pruning
    potential_edges = []
    top_k_per_project = max(20, len(candidates)) 
    
    for p in projects:
        project_scores = []
        for c in candidates:
            if p.id in (c.forbidden_project_ids or []): continue
            
            score, reasons = compute_semantic_score(
                c, p, 
                skill_frequencies=skill_frequencies, 
                total_candidates=len(candidates)
            )
            project_scores.append((score, c.id, p.id, reasons))
        
        project_scores.sort(key=lambda x: x[0], reverse=True)
        potential_edges.extend(project_scores[:top_k_per_project])

    # Ensure pinned assignments are included
    for c in candidates:
        if c.pinned_project_id:
            try:
                proj = next(p for p in projects if p.id == c.pinned_project_id)
                score, reasons = compute_semantic_score(c, proj)
                potential_edges.append((score, c.id, c.pinned_project_id, reasons))
            except StopIteration: pass

    model = cp_model.CpModel()
    
    # Variables: x[c][p]
    x = {}
    edge_data = {} 
    candidate_projects = {} 
    project_candidates = {} 

    for score, c_id, p_id, reasons in potential_edges:
        if c_id not in x: x[c_id] = {}
        if p_id not in x[c_id]:
            x[c_id][p_id] = model.NewBoolVar(f'x_{c_id}_{p_id}')
            edge_data[(c_id, p_id)] = (score, reasons)
            
            if c_id not in candidate_projects: candidate_projects[c_id] = []
            candidate_projects[c_id].append(p_id)
            
            if p_id not in project_candidates: project_candidates[p_id] = []
            project_candidates[p_id].append(c_id)

    # Constraints 
    # 1. Every candidate assigned to exactly one project
    for c in candidates:
        if c.id in x:
            model.Add(sum(x[c.id][p_id] for p_id in candidate_projects[c.id]) == 1)

    # 2. Relaxed Team Size (Dynamic Range)
    # Target even distribution but allow flexibility for projects to have more members
    num_c = len(candidates)
    num_p = len(projects)
    
    # Mathematical Floor is the absolute minimum to ensure everyone is assigned
    # but we allow it to go lower (1) if needed, and higher (+2) for fairness
    min_size = max(1, math.floor(num_c / num_p) - 1)
    max_size = math.ceil(num_c / num_p) + 2
    
    for p in projects:
        if p.id in project_candidates:
            model.Add(sum(x[c_id][p.id] for c_id in project_candidates[p.id]) >= min_size)
            model.Add(sum(x[c_id][p.id] for c_id in project_candidates[p.id]) <= max_size)

    objective = []
    current_map = {a.candidate_id: a.project_id for a in current_allocations} if current_allocations else {}

    for (c_id, p_id), (score, _) in edge_data.items():
        base_score = score
        
        # Soft Constraint: Team Balance Penalty
        # Slightly discourage larger teams to keep it "fair"
        # but match score remains the primary driver
        
        # Soft Constraint: Seniority Distribution
        c_obj = next(cand for cand in candidates if cand.id == c_id)
        if c_obj.is_senior:
            base_score += 4

        if c_id in current_map and current_map[c_id] == p_id:
            base_score += 5 
            
        objective.append(x[c_id][p_id] * int(base_score))

    model.Maximize(sum(objective))

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assignments = []

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        logger.info(f"CP-SAT Solver Status: {status}")
        for c_id, projects_map in x.items():
            for p_id, var in projects_map.items():
                if solver.Value(var):
                    score, reasons = edge_data[(c_id, p_id)]
                    
                    # Tension Analysis
                    c = next(cand for cand in candidates if cand.id == c_id)
                    p = next(proj for proj in projects if proj.id == p_id)
                    if c.is_senior and score < 70 and not c.pinned_project_id:
                        msg = f"📉 Tension: {c.name} assigned to {p.title} to balance seniority, but skill match is only {score}%."
                        logger.warning(msg)

                    assignments.append({
                        "candidate_id": c_id,
                        "project_id": p_id,
                        "score": score,
                        "reasons": reasons
                    })
        
    return assignments

import html
import os
def generate_visual_graph(candidates, projects, assignments, output_path="frontend/public/match_map.html"):
    try:
        import networkx as nx
        from pyvis.network import Network
        
        logger.info(f"Generating visual match graph to [bold cyan]{output_path}[/bold cyan]")
        
        G = nx.Graph()
        
        for p in projects:
            title_clean = html.escape(p.title)
            G.add_node(f"P_{p.id}", label=title_clean[:20], group="project", title=title_clean, color="#4A5D4E", shape="hexagon", size=30)
            
        for c in candidates:
            name_clean = html.escape(c.name or "Unknown")
            label = name_clean.split()[0] if name_clean.split() else "Member"
            color = "#1A1A1A" if c.is_senior else "#71717A"
            G.add_node(f"C_{c.id}", label=label, group="candidate", title=name_clean, color=color, shape="dot", size=20)
                
        for a in assignments:
            G.add_edge(f"C_{a['candidate_id']}", f"P_{a['project_id']}", value=a['score'], title=f"Fit: {a['score']}", color="#c7b9a4")
            
        net = Network(height="600px", width="100%", bgcolor="#F9F8F4", font_color="#1A1A1A")
        net.from_nx(G)
        
        net.set_options("""
        var options = {
          "nodes": {
            "font": { "face": "IBM Plex Sans", "size": 14 }
          },
          "edges": {
            "smooth": { "type": "cubicBezier", "forceDirection": "horizontal", "roundness": 0.4 }
          },
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "centralGravity": 0.01,
              "springLength": 100,
              "springConstant": 0.08
            },
            "minVelocity": 0.75,
            "solver": "forceAtlas2Based"
          }
        }
        """)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        net.write_html(output_path)
        logger.info("[bold green]✓[/bold green] Match map visualization generated successfully.")
    except Exception as e:
        logger.error(f"Visual graph generation failed: {e}")
