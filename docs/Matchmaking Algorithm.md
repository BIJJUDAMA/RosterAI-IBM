# Matchmaking Engine and Algorithm

The matchmaking system is a constrained global optimization engine that leverages semantic reasoning and mathematical linear programming.

## 1. The Scoring Model

We calculate a compatibility score for every member-project pair using a weighted three-term formula.

### A. Semantic Similarity (30% weight)
The system generates 1024-dimensional embeddings for member profiles and project requirements using the IBM watsonx.ai embedding model.
- Logic: We calculate the cosine similarity between the member vector and the project requirement vector.
- Purpose: Captures the "technical vibe" and domain alignment beyond simple keyword matching.

### B. Hard Skill Overlap (55% weight)
The engine performs a literal and fuzzy intersection between the member's extracted skills and the project's required skills.
- Logic: High weight ensures that candidates have the actual tools needed to execute the project.
- Fuzzy Matching: Frontend health scores use bidirectional substring matching to bridge minor naming differences (e.g., "React" and "React Native").

### C. Load Balance and Rarity Bonus (15% weight)
A dynamic bonus is awarded to members who possess "Rare Skills" required by a project.
- Rarity: A skill is considered rare if it is held by 10% or fewer of the total candidate pool.
- Purpose: Incentivizes the solver to place unique specialists where they are most needed.

## 2. Global Optimization (CP-SAT)

The final team assignments are modeled as an Integer Linear Programming (ILP) problem solved using Google OR-Tools.

### Mathematical Constraints
1. Unique Assignment: Every candidate is assigned to exactly one project (or remains on the bench if unassigned).
2. Dynamic Team Balancing: Instead of fixed sizes, the solver uses a range (Average - 1 to Average + 2) to ensure a fair and feasible distribution across all projects.
3. Human Authority: Manual "Pins" or locks created in the UI are treated as fixed constraints that the solver cannot override.

### Seniority Distribution
The engine uses a "soft" objective to spread senior-level members across different teams, preventing technical saturation in one project and skill gaps in others.

## 3. Explanations and Onboarding

### AI Match Reasons
After the solver completes, the system generates a single-sentence technical justification for every assignment, explaining the skill-to-need alignment.

### AI Jumpstart Briefs
For every new team assignment, the system generates a two-sentence onboarding brief:
- Sentence 1: Identifies the specific skill that secured the assignment.
- Sentence 2: Defines the member's primary technical focus for the first 30 days based on project gaps.
