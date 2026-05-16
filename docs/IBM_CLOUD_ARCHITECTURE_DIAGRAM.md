# IBM Cloud Architecture Diagram for Roster AI System

## System Architecture Overview

This document provides visual representations of the current local architecture and the proposed IBM Cloud architecture.

---

## Current Local Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        FE[React Frontend<br/>Vite + TypeScript]
    end
    
    subgraph "API Layer"
        API[FastAPI Backend<br/>Port 8000]
        WS[WebSocket Manager<br/>Real-time Updates]
    end
    
    subgraph "Intelligence Layer - LOCAL"
        PROXY[Intelligence Proxy<br/>VRAM Guard<br/>Port 5000]
        OLLAMA[Ollama Engine<br/>Port 11434<br/>GPU Required]
        AGENT[LangGraph Agent<br/>Multi-node Workflow]
    end
    
    subgraph "AI Models - LOCAL"
        LLM[qwen2.5-vl:3b<br/>Vision + Text]
        EMB[jina-code-embeddings<br/>768-dim vectors]
    end
    
    subgraph "Processing Layer"
        DOC[Docling Converter<br/>PDF → Markdown<br/>CPU Only]
        PARSE[Document Parsers<br/>Resume + Project]
    end
    
    subgraph "Storage Layer - LOCAL"
        PG[(PostgreSQL<br/>+ pgvector<br/>Port 5432)]
        REDIS[(Redis Cache<br/>Port 6379)]
        FS[Local Filesystem<br/>PDFs + Images]
    end
    
    subgraph "Optimization Layer"
        CPSAT[OR-Tools CP-SAT<br/>Constraint Solver]
        MATCH[Matching Service<br/>Global Optimizer]
    end
    
    FE <-->|HTTP/WS| API
    API <--> WS
    API --> AGENT
    AGENT <--> PROXY
    PROXY <--> OLLAMA
    OLLAMA --> LLM
    OLLAMA --> EMB
    AGENT --> DOC
    AGENT --> PARSE
    API <--> PG
    API <--> REDIS
    PARSE <--> FS
    API --> MATCH
    MATCH --> CPSAT
    MATCH <--> PG
    
    style OLLAMA fill:#ff6b6b
    style LLM fill:#ff6b6b
    style EMB fill:#ff6b6b
    style PG fill:#ff6b6b
    style FS fill:#ff6b6b
    style PROXY fill:#ff6b6b
```

**Legend:**

- 🔴 Red boxes = Components to be migrated to IBM Cloud
- ⚪ White boxes = Components that remain unchanged

---

## Proposed IBM Cloud Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        FE[React Frontend<br/>Vite + TypeScript]
    end
    
    subgraph "API Layer"
        API[FastAPI Backend<br/>Port 8000]
        WS[WebSocket Manager<br/>Real-time Updates]
    end
    
    subgraph "IBM Cloud - AI Services"
        WX[IBM watsonx.ai<br/>Dallas Region]
        WML[Watson Machine Learning<br/>Runtime Service]
        NLU[Watson NLU<br/>Sentiment Analysis]
    end
    
    subgraph "IBM Cloud - Foundation Models"
        GRANITE[Granite 3-8B Instruct<br/>LLM Inference]
        SLATE[Slate 125M Embeddings<br/>768-dim vectors]
        GUARD[Granite Guardian<br/>Safety Layer]
    end
    
    subgraph "Intelligence Layer - HYBRID"
        AGENT[LangGraph Agent<br/>Multi-node Workflow]
        CLOUD_CLIENT[IBM Cloud Client<br/>API Wrapper]
        FALLBACK[Fallback Handler<br/>Local → Cloud]
    end
    
    subgraph "Processing Layer"
        DOC[Docling Converter<br/>PDF → Markdown<br/>CPU Only]
        PARSE[Document Parsers<br/>Resume + Project]
    end
    
    subgraph "IBM Cloud - Storage"
        CLOUDANT[(IBM Cloudant<br/>NoSQL Database<br/>Dallas)]
        COS[IBM Cloud Object Storage<br/>Document Repository<br/>Global]
    end
    
    subgraph "Local Cache Layer"
        REDIS[(Redis Cache<br/>Port 6379<br/>Embeddings + Status)]
    end
    
    subgraph "Optimization Layer"
        CPSAT[OR-Tools CP-SAT<br/>Constraint Solver]
        MATCH[Matching Service<br/>Global Optimizer]
    end
    
    FE <-->|HTTP/WS| API
    API <--> WS
    API --> AGENT
    AGENT <--> CLOUD_CLIENT
    CLOUD_CLIENT <--> WX
    WX --> WML
    WX --> GRANITE
    WX --> SLATE
    WX --> GUARD
    AGENT --> NLU
    AGENT --> DOC
    AGENT --> PARSE
    API <--> CLOUDANT
    API <--> REDIS
    PARSE <--> COS
    API --> MATCH
    MATCH --> CPSAT
    MATCH <--> CLOUDANT
    CLOUD_CLIENT -.->|Fallback| FALLBACK
    
    style WX fill:#4A90E2
    style WML fill:#4A90E2
    style NLU fill:#4A90E2
    style GRANITE fill:#4A90E2
    style SLATE fill:#4A90E2
    style GUARD fill:#4A90E2
    style CLOUDANT fill:#4A90E2
    style COS fill:#4A90E2
    style CLOUD_CLIENT fill:#50C878
    style FALLBACK fill:#FFD700
```

**Legend:**

- 🔵 Blue boxes = IBM Cloud services
- 🟢 Green boxes = New cloud integration components
- 🟡 Yellow boxes = Fallback/hybrid components
- ⚪ White boxes = Unchanged components

---

## Data Flow Diagrams

### Document Ingestion Flow (Cloud Architecture)

```mermaid
sequenceDiagram
    participant User
    participant API as FastAPI
    participant COS as Cloud Object Storage
    participant Agent as LangGraph Agent
    participant Docling
    participant WX as watsonx.ai
    participant Cloudant
    
    User->>API: Upload Resume PDF
    API->>COS: Store original PDF
    COS-->>API: Return object URL
    API->>Agent: Process document
    Agent->>COS: Download PDF
    Agent->>Docling: Extract text/images
    Docling-->>Agent: Markdown + images
    Agent->>WX: Analyze with Granite LLM
    WX-->>Agent: Structured profile
    Agent->>WX: Generate embeddings
    WX-->>Agent: 768-dim vector
    Agent->>Cloudant: Store profile + vector
    Cloudant-->>Agent: Document ID
    Agent-->>API: Processing complete
    API-->>User: Success response
```

### Matching Algorithm Flow (Cloud Architecture)

```mermaid
sequenceDiagram
    participant User
    participant API as FastAPI
    participant Cloudant
    participant WX as watsonx.ai
    participant CPSAT as OR-Tools Solver
    participant Redis
    
    User->>API: Request team matching
    API->>Cloudant: Fetch all candidates
    Cloudant-->>API: Candidate documents
    API->>Cloudant: Fetch all projects
    Cloudant-->>API: Project documents
    API->>Redis: Check cached embeddings
    Redis-->>API: Cached vectors
    
    alt Embeddings not cached
        API->>WX: Generate missing embeddings
        WX-->>API: New vectors
        API->>Redis: Cache embeddings
    end
    
    API->>CPSAT: Run optimization
    Note over CPSAT: Compute similarity scores<br/>Apply constraints<br/>Maximize utility
    CPSAT-->>API: Optimal assignments
    API->>Cloudant: Store allocations
    Cloudant-->>API: Confirmation
    API-->>User: Matching results
```

---

## Component Interaction Matrix

| Component | Interacts With | Protocol | Purpose |
|-----------|---------------|----------|---------|
| FastAPI | React Frontend | HTTP/WebSocket | API endpoints + real-time updates |
| FastAPI | IBM Cloudant | HTTPS (REST) | CRUD operations on documents |
| FastAPI | IBM COS | HTTPS (S3 API) | Document upload/download |
| LangGraph Agent | watsonx.ai | HTTPS (REST) | LLM inference + embeddings |
| LangGraph Agent | Watson NLU | HTTPS (REST) | Sentiment/emotion analysis |
| LangGraph Agent | Docling | In-process | PDF parsing |
| Matching Service | OR-Tools | In-process | Constraint optimization |
| Matching Service | IBM Cloudant | HTTPS (REST) | Fetch candidates/projects |
| All Components | Redis | TCP (Redis Protocol) | Caching layer |

---

## Network Architecture

```mermaid
graph LR
    subgraph "Public Internet"
        USER[End Users]
    end
    
    subgraph "Application Server"
        APP[Roster Backend<br/>FastAPI + Docker]
        REDIS_LOCAL[Redis Cache]
    end
    
    subgraph "IBM Cloud - Dallas Region"
        WX[watsonx.ai]
        NLU[Watson NLU]
        CLOUDANT[Cloudant]
    end
    
    subgraph "IBM Cloud - Global"
        COS[Cloud Object Storage]
    end
    
    USER -->|HTTPS| APP
    APP -->|HTTPS<br/>IAM Auth| WX
    APP -->|HTTPS<br/>IAM Auth| NLU
    APP -->|HTTPS<br/>IAM Auth| CLOUDANT
    APP -->|HTTPS<br/>S3 API| COS
    APP <-->|TCP| REDIS_LOCAL
    
    style USER fill:#E8E8E8
    style APP fill:#50C878
    style WX fill:#4A90E2
    style NLU fill:#4A90E2
    style CLOUDANT fill:#4A90E2
    style COS fill:#4A90E2
```

---

## Deployment Architecture

### Development Environment

```mermaid
graph TB
    subgraph "Developer Machine"
        CODE[Source Code]
        DOCKER[Docker Compose]
        LOCAL_REDIS[Redis Container]
        LOCAL_PG[PostgreSQL Container<br/>Fallback Only]
    end
    
    subgraph "IBM Cloud - Dev Account"
        WX_DEV[watsonx.ai Dev Project]
        CLOUDANT_DEV[Cloudant Dev Instance]
        COS_DEV[COS Dev Bucket]
    end
    
    CODE --> DOCKER
    DOCKER --> LOCAL_REDIS
    DOCKER --> LOCAL_PG
    DOCKER -->|API Calls| WX_DEV
    DOCKER -->|API Calls| CLOUDANT_DEV
    DOCKER -->|API Calls| COS_DEV
```

### Production Environment

```mermaid
graph TB
    subgraph "Cloud Platform (AWS/Azure/GCP)"
        LB[Load Balancer]
        APP1[App Instance 1]
        APP2[App Instance 2]
        APP3[App Instance 3]
        REDIS_CLUSTER[Redis Cluster]
    end
    
    subgraph "IBM Cloud - Production"
        WX_PROD[watsonx.ai Prod Project]
        CLOUDANT_PROD[Cloudant Prod Instance<br/>Multi-region]
        COS_PROD[COS Prod Bucket<br/>Cross-region]
    end
    
    subgraph "Monitoring"
        LOGS[Log Aggregation]
        METRICS[Metrics Dashboard]
        ALERTS[Alert Manager]
    end
    
    LB --> APP1
    LB --> APP2
    LB --> APP3
    APP1 --> REDIS_CLUSTER
    APP2 --> REDIS_CLUSTER
    APP3 --> REDIS_CLUSTER
    APP1 -->|API Calls| WX_PROD
    APP2 -->|API Calls| WX_PROD
    APP3 -->|API Calls| WX_PROD
    APP1 -->|API Calls| CLOUDANT_PROD
    APP2 -->|API Calls| CLOUDANT_PROD
    APP3 -->|API Calls| CLOUDANT_PROD
    APP1 -->|API Calls| COS_PROD
    APP2 -->|API Calls| COS_PROD
    APP3 -->|API Calls| COS_PROD
    
    APP1 --> LOGS
    APP2 --> LOGS
    APP3 --> LOGS
    LOGS --> METRICS
    METRICS --> ALERTS
```

---

## Security Architecture

```mermaid
graph TB
    subgraph "Authentication Layer"
        IAM[IBM Cloud IAM]
        API_KEYS[API Key Management]
        SECRETS[Secrets Manager]
    end
    
    subgraph "Application Layer"
        APP[Roster Backend]
        ENV[Environment Variables]
    end
    
    subgraph "IBM Cloud Services"
        WX[watsonx.ai]
        CLOUDANT[Cloudant]
        COS[Cloud Object Storage]
        NLU[Watson NLU]
    end
    
    subgraph "Security Controls"
        TLS[TLS 1.3 Encryption]
        RBAC[Role-Based Access Control]
        AUDIT[Audit Logging]
    end
    
    API_KEYS --> SECRETS
    SECRETS --> ENV
    ENV --> APP
    APP -->|Bearer Token| IAM
    IAM -->|Authorized| WX
    IAM -->|Authorized| CLOUDANT
    IAM -->|Authorized| COS
    IAM -->|Authorized| NLU
    
    TLS -.->|Encrypts| APP
    RBAC -.->|Controls| IAM
    AUDIT -.->|Monitors| IAM
    
    style IAM fill:#FF6B6B
    style SECRETS fill:#FF6B6B
    style TLS fill:#50C878
    style RBAC fill:#50C878
    style AUDIT fill:#50C878
```

---

## Scalability Architecture

### Horizontal Scaling Strategy

```mermaid
graph LR
    subgraph "Load Distribution"
        LB[Load Balancer]
    end
    
    subgraph "Application Tier - Auto-scaling"
        APP1[Instance 1]
        APP2[Instance 2]
        APP3[Instance 3]
        APPN[Instance N]
    end
    
    subgraph "IBM Cloud - Managed Services"
        WX[watsonx.ai<br/>Auto-scales]
        CLOUDANT[Cloudant<br/>Distributed]
        COS[COS<br/>Global CDN]
    end
    
    LB --> APP1
    LB --> APP2
    LB --> APP3
    LB --> APPN
    
    APP1 --> WX
    APP2 --> WX
    APP3 --> WX
    APPN --> WX
    
    APP1 --> CLOUDANT
    APP2 --> CLOUDANT
    APP3 --> CLOUDANT
    APPN --> CLOUDANT
    
    APP1 --> COS
    APP2 --> COS
    APP3 --> COS
    APPN --> COS
```

---

## Disaster Recovery Architecture

```mermaid
graph TB
    subgraph "Primary Region - Dallas"
        WX_PRIMARY[watsonx.ai Primary]
        CLOUDANT_PRIMARY[Cloudant Primary]
        COS_PRIMARY[COS Primary]
    end
    
    subgraph "Secondary Region - Frankfurt"
        WX_SECONDARY[watsonx.ai Secondary]
        CLOUDANT_SECONDARY[Cloudant Replica]
        COS_SECONDARY[COS Replica]
    end
    
    subgraph "Backup Strategy"
        DAILY[Daily Snapshots]
        WEEKLY[Weekly Archives]
        MONTHLY[Monthly Cold Storage]
    end
    
    WX_PRIMARY -.->|Failover| WX_SECONDARY
    CLOUDANT_PRIMARY -->|Continuous Replication| CLOUDANT_SECONDARY
    COS_PRIMARY -->|Cross-region Replication| COS_SECONDARY
    
    CLOUDANT_PRIMARY --> DAILY
    DAILY --> WEEKLY
    WEEKLY --> MONTHLY
    
    style WX_PRIMARY fill:#4A90E2
    style CLOUDANT_PRIMARY fill:#4A90E2
    style COS_PRIMARY fill:#4A90E2
    style WX_SECONDARY fill:#FFD700
    style CLOUDANT_SECONDARY fill:#FFD700
    style COS_SECONDARY fill:#FFD700
```

---

## Cost Optimization Architecture

```mermaid
graph TB
    subgraph "Request Layer"
        REQ[Incoming Request]
    end
    
    subgraph "Caching Strategy"
        L1[L1: In-Memory Cache<br/>Hot Data]
        L2[L2: Redis Cache<br/>Warm Data]
        L3[L3: Cloudant Cache<br/>Cold Data]
    end
    
    subgraph "IBM Cloud Services"
        WX[watsonx.ai<br/>Pay per token]
        CLOUDANT[Cloudant<br/>Pay per operation]
        COS[COS<br/>Pay per GB]
    end
    
    REQ --> L1
    L1 -->|Cache Miss| L2
    L2 -->|Cache Miss| L3
    L3 -->|Cache Miss| WX
    L3 -->|Cache Miss| CLOUDANT
    L3 -->|Cache Miss| COS
    
    style L1 fill:#50C878
    style L2 fill:#50C878
    style L3 fill:#50C878
```

**Cost Optimization Strategies:**

1. **Aggressive Caching**: 3-tier cache reduces API calls by 80%
2. **Batch Processing**: Group LLM requests to reduce overhead
3. **Lazy Loading**: Only generate embeddings when needed
4. **Connection Pooling**: Reuse HTTP connections
5. **Regional Deployment**: All services in Dallas to minimize data transfer costs

---

## Migration Phases Visualization

```mermaid
gantt
    title IBM Cloud Migration Timeline
    dateFormat  YYYY-MM-DD
    section Phase 1: Setup
    Provision IBM Services           :a1, 2026-05-16, 3d
    Create Cloud Modules            :a2, after a1, 4d
    Implement Feature Flags         :a3, after a2, 2d
    
    section Phase 2: Core Migration
    Migrate LLM to watsonx.ai       :b1, after a3, 5d
    Migrate Embeddings              :b2, after b1, 3d
    Testing & Benchmarking          :b3, after b2, 4d
    
    section Phase 3: Storage
    Implement COS Integration       :c1, after b3, 4d
    Implement Cloudant Integration  :c2, after c1, 5d
    Data Migration                  :c3, after c2, 3d
    
    section Phase 4: Optimization
    Performance Tuning              :d1, after c3, 4d
    Cost Optimization               :d2, after d1, 3d
    Documentation                   :d3, after d2, 2d
    
    section Phase 5: Cutover
    Gradual Traffic Migration       :e1, after d3, 7d
    Monitoring & Validation         :e2, after e1, 7d
    Decommission Local              :e3, after e2, 3d
```

---

## Technology Stack Comparison

| Layer | Current (Local) | Future (IBM Cloud) | Change Impact |
|-------|----------------|-------------------|---------------|
| **LLM Inference** | Ollama + qwen2.5-vl:3b | watsonx.ai + Granite 3-8B | 🟡 Medium - API changes |
| **Embeddings** | jina-code-embeddings | watsonx.ai + Slate 125M | 🟢 Low - Similar API |
| **Database** | PostgreSQL + pgvector | Cloudant + in-memory search | 🔴 High - Schema redesign |
| **Storage** | Local filesystem | Cloud Object Storage | 🟡 Medium - S3 API |
| **Cache** | Redis | Redis (unchanged) | 🟢 None |
| **NLU** | Not implemented | Watson NLU | 🟢 Low - New feature |
| **Optimization** | OR-Tools CP-SAT | OR-Tools (unchanged) | 🟢 None |

**Legend:**

- 🟢 Low Impact - Minor changes
- 🟡 Medium Impact - Moderate refactoring
- 🔴 High Impact - Significant redesign

---

## Performance Benchmarks (Estimated)

| Metric | Local (Ollama) | IBM Cloud | Improvement |
|--------|---------------|-----------|-------------|
| LLM Latency | 2-5s | 1-3s | ⬆️ 40% faster |
| Embedding Latency | 0.5-1s | 0.3-0.8s | ⬆️ 30% faster |
| Vector Search | 10-50ms | 50-200ms | ⬇️ 4x slower |
| Document Upload | <10ms | 100-300ms | ⬇️ 20x slower |
| Cold Start | 30-60s | 0s | ⬆️ Instant |
| Concurrent Users | 5-10 | 100+ | ⬆️ 10x more |
| Availability | 95% | 99.9% | ⬆️ 5% better |

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-15  
**Author:** Bob (Planning Mode)  
**Status:** Ready for Review
