# Multimodal Pipeline and Vision Support

Roster AI leverages a multimodal pipeline to process both text-heavy resumes and visually-driven project slide decks.

## 1. Vision Input Handling

The system uses a vision fallback strategy when native text extraction is insufficient or when processing visual media like slides.
- Rasterization: PDFs are converted to JPEG images locally using PyMuPDF at a standard resolution.
- Vision Encoding: Images are encoded into base64 strings and injected directly into the LLM chat messages.
- Model: Llama 3.2 11B Vision Instruct (via IBM watsonx.ai) is the primary engine for analyzing visual components.

## 2. Extraction Strategy

- Slide-by-Slide Analysis: Every page of a slide deck is analyzed independently to identify architecture components, technology logos, and explicit technical requirements.
- Consensus Building: A multi-node agent (LangGraph) synthesizes the individual slide reports with the overall document text to build a unified profile.
- Truth-Anchoring: The agent is strictly instructed to only report what is visually present or explicitly written, preventing hallucinations of non-existent project details.

## 3. Multimodal Scaling and Performance

- Concurrent Processing: Ingestion is parallelized but throttled to respect IBM watsonx.ai API rate limits.
- VRAM Optimization: Vision-intensive tasks are offloaded to IBM Cloud, keeping the local environment efficient and responsive.
- Caching: Extracted technical profiles are stored in PostgreSQL, and their corresponding semantic embeddings are cached in Redis to avoid redundant cloud calls.

## 4. Ingestion Resilience

- Failed Extraction: If the vision engine fails to identify a project or member name, the system fallbacks to a "DOC_filename" identifier to ensure the record is still saved and can be manually corrected.
- Repair Loop: Any malformed JSON responses from the vision model are automatically caught and repaired by a secondary AI pass before being sent to the database.
