# IBM Cloud Migration Plan for Roster AI System

## Executive Summary

This document outlines the comprehensive migration strategy for transitioning the Roster AI system from local Ollama-based models to IBM Cloud services. The migration leverages IBM watsonx.ai, Watson NLU, Cloudant, and Cloud Object Storage to create a scalable, production-ready architecture.

---

## Current Architecture Analysis

### Local Components to Migrate

| Component | Current Technology | IBM Cloud Replacement | Priority |
|-----------|-------------------|----------------------|----------|
| LLM Inference | Ollama (qwen2.5-vl:3b) | IBM watsonx.ai (Granite models) | **CRITICAL** |
| Embeddings | Ollama (jina-code-embeddings-cpu) | IBM watsonx.ai Embeddings | **CRITICAL** |
| Database | PostgreSQL + pgvector | IBM Cloudant + watsonx.ai embeddings | **HIGH** |
| Document Storage | Local filesystem | IBM Cloud Object Storage (COS) | **MEDIUM** |
| NLU/Sentiment | Not implemented | IBM Watson NLU | **LOW** |
| Speech Services | Not implemented | IBM STT/TTS | **FUTURE** |

### Current System Metrics

- **LLM Calls per Ingestion**: ~5-10 (resume parsing, project analysis)
- **Embedding Calls**: 2 per document (profile + mission statement)
- **Vision Model Usage**: 1 call per slide/image
- **Database Operations**: PostgreSQL with pgvector for semantic search
- **Storage**: Local filesystem for PDFs, images, parsed outputs

---

## IBM Cloud Services Architecture

### Available Services (from image.png)

#### AI/Machine Learning (7 services)

1. **watsonx-Hackathon GOV** - watsonx.governance (Dallas)
2. **watsonx-Hackathon NLU** - Natural Language Understanding (Dallas)
3. **watsonx-Hackathon Orchestrate** - watsonx Orchestrate (Toronto)
4. **watsonx-Hackathon STT** - Speech to Text (Dallas)
5. **watsonx-Hackathon TTS** - Text to Speech (Dallas)
6. **watsonx-Hackathon WML** - watsonx.ai Runtime (Dallas)
7. **watsonx-Hackathon WS** - watsonx.ai Studio (Dallas)

#### Analytics (1 service)

8. **watsonx-Hackathon GOV** - watsonx.governance (Dallas)

#### Databases (1 service)

9. **watsonx-Hackathon Cloudant** - Cloudant (Dallas)

#### Storage (1 service)

10. **watsonx-Hackathon COS** - Cloud Object Storage (Global)

---

## Migration Architecture Design

### Phase 1: Core LLM Migration (CRITICAL)

#### Component: LLM Inference Engine

**Current Implementation:**

```python
# app/intelligence/llm_client.py
self.raw_client = OpenAI(base_url=f"{proxy_host}/v1", api_key="ollama", timeout=timeout)
self.model_name = "qwen2.5-vl:3b"
```

**IBM watsonx.ai Implementation:**

```python
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

credentials = Credentials(
    api_key=os.getenv("IBM_WATSONX_API_KEY"),
    url=os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
)
client = APIClient(credentials)

model = ModelInference(
    model_id="ibm/granite-3-8b-instruct",  # or granite-13b-instruct-v2
    api_client=client,
    project_id=os.getenv("IBM_WATSONX_PROJECT_ID"),
    params={
        GenParams.DECODING_METHOD: "greedy",
        GenParams.MAX_NEW_TOKENS: 2048,
        GenParams.TEMPERATURE: 0.0,
        GenParams.STOP_SEQUENCES: ["</think>"]
    }
)
```

**Recommended Models:**

- **Primary LLM**: `ibm/granite-3-8b-instruct` (8B parameters, fast inference)
- **Vision Alternative**: Use document parsing + text-only LLM (Granite doesn't support vision yet)
- **Embeddings**: `ibm/slate-125m-english-rtrvr` or `sentence-transformers/all-minilm-l6-v2`

#### Component: Embeddings Generation

**Current Implementation:**

```python
response = self.raw_client.embeddings.create(
    model="jina-code-embeddings-cpu", 
    input=text
)
vector = response.data[0].embedding
```

**IBM watsonx.ai Implementation:**

```python
from ibm_watsonx_ai.foundation_models import Embeddings

embedding_model = Embeddings(
    model_id="ibm/slate-125m-english-rtrvr",
    api_client=client,
    project_id=os.getenv("IBM_WATSONX_PROJECT_ID")
)

vector = embedding_model.embed_query(text)
```

---

### Phase 2: Document Processing Migration (HIGH)

#### Component: Document Storage

**Current Implementation:**

- Local filesystem storage in `resumes/`, `projects/`, `parsed_resumes/`
- Direct file path access

**IBM Cloud Object Storage Implementation:**

```python
import ibm_boto3
from ibm_botocore.client import Config

cos_client = ibm_boto3.client(
    "s3",
    ibm_api_key_id=os.getenv("IBM_COS_API_KEY"),
    ibm_service_instance_id=os.getenv("IBM_COS_INSTANCE_ID"),
    config=Config(signature_version="oauth"),
    endpoint_url=os.getenv("IBM_COS_ENDPOINT")
)

# Upload document
cos_client.upload_file(
    Filename=local_path,
    Bucket="roster-documents",
    Key=f"resumes/{file_hash}.pdf"
)

# Download for processing
cos_client.download_file(
    Bucket="roster-documents",
    Key=f"resumes/{file_hash}.pdf",
    Filename=temp_path
)
```

**Bucket Structure:**

```
roster-documents/
├── resumes/
│   ├── raw/          # Original uploaded PDFs
│   └── parsed/       # Parsed markdown outputs
├── projects/
│   ├── raw/
│   └── parsed/
└── temp/             # Temporary processing files
```

---

### Phase 3: Database Migration (HIGH)

#### Component: PostgreSQL → Cloudant

**Current Schema:**

```sql
-- PostgreSQL with pgvector
CREATE TABLE candidates (
    id SERIAL PRIMARY KEY,
    name VARCHAR,
    skills TEXT[],
    embedding vector(768),
    ...
);
```

**IBM Cloudant Implementation:**

Cloudant is a NoSQL document database, so we need to restructure:

```python
from ibmcloudant.cloudant_v1 import CloudantV1, Document
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

authenticator = IAMAuthenticator(os.getenv("IBM_CLOUDANT_API_KEY"))
client = CloudantV1(authenticator=authenticator)
client.set_service_url(os.getenv("IBM_CLOUDANT_URL"))

# Create databases
client.put_database(db='candidates').get_result()
client.put_database(db='projects').get_result()
client.put_database(db='allocations').get_result()

# Document structure
candidate_doc = {
    "_id": f"candidate_{uuid}",
    "type": "candidate",
    "name": "John Doe",
    "skills": ["Python", "FastAPI", "Docker"],
    "embedding": [0.1, 0.2, ...],  # Store as array
    "seniority": "mid",
    "domain_focus": ["backend", "devops"],
    "created_at": "2026-05-15T18:00:00Z"
}

client.post_document(db='candidates', document=candidate_doc).get_result()
```

**Vector Search Strategy:**

Since Cloudant doesn't have native vector search like pgvector, we have two options:

1. **Hybrid Approach** (Recommended):
   - Store documents in Cloudant
   - Use watsonx.ai for embedding generation
   - Implement in-memory vector search for matching (acceptable for <10K candidates)
   - Cache embeddings in Redis

2. **External Vector DB**:
   - Keep PostgreSQL with pgvector for vector operations only
   - Use Cloudant for document storage and metadata
   - Sync IDs between systems

**Recommended: Hybrid Approach Implementation**

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class CloudantVectorSearch:
    def __init__(self, cloudant_client, embedding_model):
        self.client = cloudant_client
        self.embedding_model = embedding_model
        self.cache = {}  # In-memory cache
    
    def similarity_search(self, query_text, db_name, top_k=10):
        # Generate query embedding
        query_vector = self.embedding_model.embed_query(query_text)
        
        # Fetch all documents (with pagination for large datasets)
        all_docs = self.client.post_all_docs(
            db=db_name,
            include_docs=True
        ).get_result()
        
        # Compute similarities
        similarities = []
        for row in all_docs['rows']:
            doc = row['doc']
            if 'embedding' in doc:
                sim = cosine_similarity(
                    [query_vector], 
                    [doc['embedding']]
                )[0][0]
                similarities.append((doc, sim))
        
        # Sort and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
```

---

### Phase 4: Natural Language Understanding (LOW)

#### Component: Watson NLU Integration

**Use Cases:**

- Sentiment analysis on project descriptions
- Emotion detection in candidate profiles
- Entity extraction from resumes
- Keyword extraction for skill normalization

**Implementation:**

```python
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_watson.natural_language_understanding_v1 import Features, EmotionOptions, SentimentOptions, KeywordsOptions

nlu = NaturalLanguageUnderstandingV1(
    version='2022-04-07',
    authenticator=IAMAuthenticator(os.getenv("IBM_NLU_API_KEY"))
)
nlu.set_service_url(os.getenv("IBM_NLU_URL"))

def analyze_text(text):
    response = nlu.analyze(
        text=text,
        features=Features(
            emotion=EmotionOptions(),
            sentiment=SentimentOptions(),
            keywords=KeywordsOptions(limit=10)
        )
    ).get_result()
    
    return {
        "sentiment": response['sentiment']['document']['label'],
        "emotions": response['emotion']['document']['emotion'],
        "keywords": [kw['text'] for kw in response['keywords']]
    }
```

---

## Implementation Strategy

### Migration Phases

#### Phase 1: Parallel Infrastructure (Week 1-2)

- Set up IBM Cloud services
- Create new cloud-based modules alongside existing local modules
- Implement feature flags for switching between local/cloud

#### Phase 2: Core LLM Migration (Week 3-4)

- Migrate LLM inference to watsonx.ai
- Migrate embeddings generation
- Test with existing data
- Performance benchmarking

#### Phase 3: Storage & Database (Week 5-6)

- Migrate document storage to COS
- Implement Cloudant integration
- Data migration scripts
- Dual-write period for safety

#### Phase 4: Optimization & Cleanup (Week 7-8)

- Remove local dependencies
- Optimize cloud API calls
- Cost optimization
- Documentation updates

---

## Code Structure Changes

### New Directory Structure

```
app/
├── cloud/                          # NEW: Cloud integrations
│   ├── __init__.py
│   ├── watsonx_client.py          # watsonx.ai LLM & embeddings
│   ├── cloudant_client.py         # Cloudant database operations
│   ├── cos_client.py              # Cloud Object Storage
│   ├── nlu_client.py              # Watson NLU
│   └── config.py                  # Cloud service configuration
├── intelligence/
│   ├── llm_client.py              # MODIFIED: Add cloud backend
│   ├── agent_service.py           # MODIFIED: Support cloud LLM
│   └── ...
├── database/
│   ├── connection.py              # MODIFIED: Add Cloudant option
│   ├── cloudant_models.py         # NEW: Cloudant document schemas
│   └── ...
└── ...
```

### Configuration Management

**New Environment Variables:**

```bash
# Backend Selection Flags
AI_BACKEND=cloud                    # local | cloud | hybrid
STORAGE_BACKEND=cloud               # local | cloud
DATABASE_BACKEND=cloudant           # postgres | cloudant | hybrid

# IBM watsonx.ai
IBM_WATSONX_API_KEY=your_key
IBM_WATSONX_PROJECT_ID=your_project_id
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
IBM_WATSONX_MODEL_ID=ibm/granite-3-8b-instruct
IBM_WATSONX_EMBEDDING_MODEL=ibm/slate-125m-english-rtrvr

# IBM Watson NLU
IBM_NLU_API_KEY=your_key
IBM_NLU_URL=https://api.us-south.natural-language-understanding.watson.cloud.ibm.com

# IBM Cloudant
IBM_CLOUDANT_API_KEY=your_key
IBM_CLOUDANT_URL=https://your-instance.cloudantnosqldb.appdomain.cloud

# IBM Cloud Object Storage
IBM_COS_API_KEY=your_key
IBM_COS_INSTANCE_ID=your_instance_id
IBM_COS_ENDPOINT=https://s3.us-south.cloud-object-storage.appdomain.cloud
IBM_COS_BUCKET_NAME=roster-documents

# Fallback to local if cloud fails
ENABLE_LOCAL_FALLBACK=true
```

---

## Cost Estimation

### IBM Cloud Lite Tier Limits

| Service | Lite Tier Limit | Estimated Usage | Cost After Limit |
|---------|----------------|-----------------|------------------|
| watsonx.ai | Limited free tokens | ~1000 tokens/doc × 100 docs = 100K tokens | $0.002/1K tokens |
| Watson NLU | 30K items/month | Optional feature | $0.003/item |
| Cloudant | 1GB storage, 20 lookups/sec | ~100MB for 1000 docs | $0.25/GB/month |
| COS | 25GB storage | ~5GB for documents | $0.023/GB/month |

**Estimated Monthly Cost (after free tier):**

- Small org (100 members, 20 projects): **$5-10/month**
- Medium org (500 members, 50 projects): **$25-50/month**
- Large org (2000 members, 100 projects): **$100-200/month**

---

## Performance Considerations

### Latency Comparison

| Operation | Local (Ollama) | IBM Cloud | Notes |
|-----------|---------------|-----------|-------|
| LLM Inference | 2-5s | 1-3s | Cloud is faster (no local GPU warmup) |
| Embeddings | 0.5-1s | 0.3-0.8s | Similar performance |
| Vector Search | 10-50ms | 50-200ms | Cloudant slower than pgvector |
| Document Storage | <10ms | 100-300ms | Network latency |

### Optimization Strategies

1. **Batch Processing**: Group multiple LLM calls
2. **Caching**: Aggressive Redis caching for embeddings
3. **Async Operations**: Use asyncio for parallel cloud calls
4. **Connection Pooling**: Reuse HTTP connections
5. **Regional Deployment**: Use Dallas region for all services

---

## Risk Mitigation

### Fallback Strategy

```python
class HybridLLMClient:
    def __init__(self):
        self.cloud_client = WatsonxClient()
        self.local_client = OllamaClient()
        self.use_cloud = os.getenv("AI_BACKEND") == "cloud"
        self.enable_fallback = os.getenv("ENABLE_LOCAL_FALLBACK") == "true"
    
    def generate_text(self, prompt):
        if self.use_cloud:
            try:
                return self.cloud_client.generate(prompt)
            except Exception as e:
                logger.warning(f"Cloud LLM failed: {e}")
                if self.enable_fallback:
                    logger.info("Falling back to local LLM")
                    return self.local_client.generate(prompt)
                raise
        else:
            return self.local_client.generate(prompt)
```

### Data Migration Safety

1. **Dual-Write Period**: Write to both local and cloud for 1 week
2. **Validation**: Compare results between local and cloud
3. **Rollback Plan**: Keep local infrastructure for 1 month
4. **Backup**: Daily backups of Cloudant to COS

---

## Testing Strategy

### Unit Tests

- Mock IBM Cloud API responses
- Test fallback mechanisms
- Validate data transformations

### Integration Tests

- End-to-end document processing
- Matching algorithm with cloud embeddings
- Performance benchmarks

### Load Tests

- Concurrent API calls
- Rate limiting behavior
- Cost monitoring

---

## Deployment Plan

### Pre-Migration Checklist

- [ ] IBM Cloud account created
- [ ] All services provisioned
- [ ] API keys generated and secured
- [ ] Test project created in watsonx.ai
- [ ] Cloudant databases created
- [ ] COS buckets created
- [ ] Local backup completed

### Migration Execution

1. Deploy cloud modules in parallel
2. Enable hybrid mode
3. Test with 10% of traffic
4. Gradually increase to 100%
5. Monitor for 1 week
6. Disable local fallback
7. Remove local dependencies

### Post-Migration

- Monitor costs daily
- Optimize API usage
- Update documentation
- Train team on cloud operations

---

## Success Metrics

### Technical Metrics

- **Latency**: <3s for LLM inference
- **Availability**: >99.5% uptime
- **Error Rate**: <1% failed requests
- **Cost**: Within budget estimates

### Business Metrics

- **Scalability**: Support 10x more users
- **Reliability**: Zero data loss
- **Performance**: Faster than local setup
- **Maintainability**: Reduced infrastructure overhead

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Provision IBM Cloud services** using the credentials guide
3. **Create feature branch** for cloud migration
4. **Implement Phase 1** (parallel infrastructure)
5. **Begin testing** with sample data

---

## References

- [IBM watsonx.ai Documentation](https://www.ibm.com/docs/en/watsonx-as-a-service)
- [IBM Cloudant Documentation](https://cloud.ibm.com/docs/Cloudant)
- [IBM Cloud Object Storage Documentation](https://cloud.ibm.com/docs/cloud-object-storage)
- [IBM Watson NLU Documentation](https://cloud.ibm.com/docs/natural-language-understanding)

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-15  
**Author:** Bob (Planning Mode)  
**Status:** Ready for Implementation
