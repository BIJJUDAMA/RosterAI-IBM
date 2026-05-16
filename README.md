# Roster AI: Mathematical Workforce Optimization Engine

Roster AI is a **Truth-Anchored** organizational intelligence platform powered by **IBM watsonx.ai**. It replaces manual guesswork in team formation with a mathematically rigorous optimization model, ensuring provable technical alignment between member expertise and project requirements.

## Technical Pillars

### 1. Vision-Aware Ingestion (The "Eyes")
Unlike traditional parsers, Roster AI utilizes **Llama 3.2 Vision** via watsonx.ai to "see" architectural diagrams, technology logos, and complex layouts in project slide decks and resumes. 
- **Structural Precision:** Combines **IBM Docling** for high-fidelity text extraction with vision fallback for scanned or visually-dense media.
- **Truth-Anchored Protocol:** A strict extraction logic with built-in **JSON Repair Loops** that eliminates hallucinations, ensuring every technical fact is verbatim from the source.

### 2. The "Grumpy" Matchmaking Engine (The "Brain")
The platform employs a balanced compatibility formula that prioritizes literal technical capability over generic semantic alignment:
- **Semantic Vibe (30%):** Uses 1024-dimensional embeddings to capture high-level domain alignment.
- **Hard-Skill Guardrail (55%):** A "grumpy" literal check ensuring members possess the exact tools (e.g., Python, AWS, React) required for the mission.
- **Specialist Prioritization (15%):** Dynamically identifies the "Rare 10%" of the talent pool and optimizes their placement for maximum organizational utility.

### 3. CP-SAT Global Optimization (The "Enforcer")
Roster AI solves for the **Global Optimum**, not just local matches.
- **Organization-to-Mission:** Uses the **Google OR-Tools CP-SAT solver** to find the single best configuration for every project simultaneously.
- **Mathematical Fairness:** Dynamically balances team sizes and seniority distribution, ensuring no project is left with technical gaps while others are overstaffed.

### 4. Actionable Intelligence (The "Heart")
- **AI Jumpstart Briefs:** Generates personalized, 2-sentence technical onboarding documents for every assignment, defining immediate 30-day focus areas.
- **Risk Transparency:** A real-time dashboard using **Fuzzy Skill Matching** to visualize project health and identify critical bottlenecks.

## System Stack

- **Backend:** FastAPI, LangGraph, SQLAlchemy.
- **AI Layer:** IBM watsonx.ai (Llama 3.2 11B Vision + multilingual-e5-large).
- **Database:** PostgreSQL 16 with pgvector (1024-dim local storage).
- **Cache:** Redis.
- **Optimization:** Google OR-Tools (Integer Linear Programming).
- **Document Processing:** IBM Docling + PyMuPDF.

## Project Structure

```text
├── app/
│   ├── api/             # FastAPI Routers and Pydantic Schemas
│   ├── cloud/           # IBM watsonx.ai Client Integration
│   ├── database/        # PostgreSQL Models and Connections
│   ├── intelligence/    # LangGraph Agents and LLM Logic
│   ├── matching/        # CP-SAT Solver and Scoring Formula
│   └── services/        # Ingestion and Assignment Logic
├── docs/                # System Documentation
├── frontend/            # React + Vite (Tailwind CSS)
├── projects/            # Inbound Project Documents
├── resumes/             # Inbound Member Resumes
└── scripts/             # Database Init and Audit Tools
```

## Setup and Quick Start

### 1. Prerequisites
- IBM Cloud Account (watsonx.ai access).
- Docker and Docker Compose.
- Bun (for frontend) and Python 3.12 (for backend).

### 2. Configure Environment
Create a `.env` file from `.env.example` and populate your `IBM_WATSONX_API_KEY` and `PROJECT_ID`.

### 3. Start Services
```bash
# Start Database and Cache
docker-compose up -d

# Initialize Database Schema
python scripts/initialize_db.py
```

### 4. Run Application
```bash
# Start Backend
python -m app.main

# Start Frontend (in separate terminal)
cd frontend
bun run dev
```

## Documentation Reference

Detailed technical guides and architectural deep-dives are available in the `/docs` directory:

- [Architecture Diagram](docs/Architecture%20Diagram.md): Visual representation of the system pipeline and agent state machine.
- [System Architecture](docs/System%20Architecture.md): Detailed breakdown of backend, AI, and data components.
- [Matchmaking Algorithm](docs/Matchmaking%20Algorithm.md): Deep dive into the scoring formula and CP-SAT optimization constraints.
- [Multimodal System](docs/Multimodal%20System.md): Overview of the vision-supported document ingestion and extraction strategy.
- [Algorithmic Advisory](docs/Algorithmic%20Advisory.md): Strategic findings regarding ML scaling, reliability, and technical debt.
- [Glossary](docs/Glossary.md): Definitions of key technical terms used across the Roster AI ecosystem.
- [IBM Cloud Credentials Setup](docs/IBM_CLOUD_CREDENTIALS_SETUP.md): Step-by-step guide for configuring required IBM watsonx.ai services.

---
**Roster AI** · High-Fidelity Organizational Intelligence · Powered by IBM watsonx.ai
