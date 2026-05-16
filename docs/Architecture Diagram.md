# Final Architecture Diagrams

## Diagram 1: Full System Pipeline

```text
 [ DOCUMENTS ]
 (PDF, Resumes, Projects)
      │
      ▼
 ┌───────────────┐
 │   INGESTION   │
 │    SERVICE    │
 └──────┬────────┘
        │
 [TEXT] │ [IMAGES]
        ▼
 ┌───────────────┐           ┌────────────────┐
 │  DOCUMENT     │◄──────────┤ SLIDE ANALYSIS │
 │  EXTRACTOR    │           │ (watsonx.ai)   │
 └──────┬────────┘           └──────┬─────────┘
        [ MARKDOWN ]                │ [REPORT]
               ▼                    │
        ┌───────────────┐◄──────────┘
        │   LANGGRAPH   │ (Reasoning LLM)
        │     AGENT     │◄─────── [ REDIS CACHE ]
        └──────┬────────┘
               │ [WATSONX API REQUEST]
               ▼
        ┌───────────────┐        ┌────────────────┐
        │  LLM CLIENT   │◄───────┤  IBM watsonx.ai│
        │               │        │  (Llama 3.2)   │
        └──────┬────────┘        └────────────────┘
               │ [STRUCTURED JSON]
               ▼
        ┌───────────────┐
        │  POSTGRESQL   │ (pgvector 1024-dim)
        └──────┬────────┘
               │ [VECTORS]
               ▼
 ┌───────────────┐        ┌───────────────┐
 │    GLOBAL     │◄───────┤   CP-SAT      │
 │   OPTIMIZER   │        │   SOLVER      │
 └──────┬────────┘        └───────────────┘
        │ [ALLOCATIONS]
        ▼
 [ MATCH REPORT ]
```

## Diagram 2: LangGraph Agent State Machine

```text
          ► [ START ]
              │
              ▼
      ┌────────────────┐
      │  memory_sync   │ (Load StandardSkills from Postgres)
      └──────┬─────────┘
              │
              ▼
      ┌────────────────┐ ↻ [ RETRY LOOP (max 3) ]
      │   extraction   │◄──────┐
      └──────┬─────────┘       │
              │                │
              ▼                │ (is_valid=False)
      ┌────────────────┐       │
      │   validation   ├───────┤
      └──────┬─────────┘       │
             │                 │ (requires_tools=True)
             │                 ▼
             │         ┌────────────────┐
             │         │ tool_executor  │
             │         └───────┬────────┘
             │                 │
             └─────────────────┘
             │ (is_valid=True)
             ▼
          ■ [ END ]
```

## Diagram 3: FastAPI Request Lifecycle

```text
 [ HTTP REQUEST ]
        │
        ▼
 ┌───────────────┐
 │ MIDDLEWARE    │ (CORS, Logging)
 └──────┬────────┘
        │
        ▼
 ┌───────────────┐
 │    ROUTER     │ (e.g., /api/match)
 └──────┬────────┘
        │
        ▼
 ┌───────────────┐
 │ SERVICE LAYER │ (matching_service.py)
 └──────┬────────┘
        │
        ├─────────────► [ BACKGROUND THREAD ] ──► [ SOLVER ]
        │                                             │
        ▼                                             │ (broadcast)
 ┌───────────────┐                                    ▼
 │   WS MANAGER  │◄─────────────────────────── [ WEBSOCKETS ]
 └───────────────┘
```

## Diagram 4: Local Stack Deployment

```text
   [ LOCAL HOST / DOCKER ]
          │
          ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                      ROSTER AI SYSTEM                       │
 │                                                             │
 │  ┌──────────────┐       ┌──────────────┐      ┌──────────┐  │
 │  │  POSTGRESQL  │◄──────┤    REDIS     │◄─────┤watsonx.ai│  │
 │  │  (pgvector)  │       │ (Cache/Sync) │      │ (Cloud)  │  │
 │  └──────┬───────┘       └──────┬───────┘      └─────┬────┘  │
 │         │                      │                    │       │
 │  ┌──────▼───────┐       ┌──────▼───────┐            │       │
 │  │  FILESYSTEM  │◄──────┤   FASTAPI    │◄───────────┘       │
 │  │  (Local)     │       │   BACKEND    │                    │
 │  └──────────────┘       └──────────────┘                    │
 │                                                             │
 └─────────────────────────────────────────────────────────────┘
```
