# Algorithmic Advisory and ML Findings

## 1. Technical Ingestion and Scale

### Scaling Retrieval
- Issue: The current system fetches embeddings into memory for scoring. While sufficient for small batches, datasets exceeding 1,000 members may require clustered retrieval.
- Suggestion: Pre-categorize members by "Domain Focus" in PostgreSQL and fetch relevant clusters during matching runs.

### Extraction Reliability
- Strategy: The system uses a "Truth-Anchored" extraction protocol. This prevents the LLM from hallucinating names or skills by requiring verbatim evidence from the source document.
- Safety: A final name polish stage fallbacks to the document filename if no valid identity is found in the header, preventing placeholder data ("John Doe") from entering the database.

## 2. Intelligence and Reasoning

### Consensus Architecture
- Strategy: The LangGraph agent uses a multi-node consensus engine. Text extraction is validated against visual slide reports to ensure that diagrams and explicit text carry equal weight in the final technical profile.
- Repair Loop: A built-in 2-attempt JSON repair loop handles malformed LLM responses by attempting syntax-only fixes, ensuring pipeline continuity without manual intervention.

### Normalization Gaps
- Observation: The system currently relies on fuzzy substring matching to bridge terminology gaps (e.g., "Django" matching "Django/Flask").
- Suggestion: Future iterations should populate the `StandardSkill` table via a specialized taxonomy agent to enable canonical mapping for all technical terms.

## 3. Optimization and Utility

### Fairness vs. Fit
- Strategy: The solver targets a dynamic range for team sizes. This balances the mathematical need for even distribution with the technical need for high-quality skill alignment.
- Seniority Distribution: Senior members are distributed via a "soft" objective. This prevents teams from becoming technically "top-heavy" while ensuring that every project has access to senior expertise where it provides the most value.

### Tension Alerts
- Indicator: The system identifies and logs "Tensions" where a member was assigned to a project to balance seniority or team size despite having a low technical fit score (<70%). These alerts are surfaced to provide transparency into the solver's trade-offs.
