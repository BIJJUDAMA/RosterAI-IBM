# IBM Cloud Implementation Roadmap

## Overview

This document provides a detailed, step-by-step implementation guide for migrating the Roster AI system to IBM Cloud. Each phase includes specific tasks, code examples, testing procedures, and success criteria.

---

## Phase 1: Infrastructure Setup (Week 1-2)

### Objectives

- Provision all IBM Cloud services
- Set up development environment
- Create cloud integration modules
- Implement feature flags

### Tasks

#### Task 1.1: Provision IBM Cloud Services (Day 1-2)

**Steps:**

1. Follow [`IBM_CLOUD_CREDENTIALS_SETUP.md`](./IBM_CLOUD_CREDENTIALS_SETUP.md)
2. Create all 4 services:
   - watsonx.ai project
   - Watson NLU instance
   - Cloudant database
   - Cloud Object Storage bucket
3. Obtain all 11 credentials
4. Store credentials securely

**Deliverables:**

- ✅ All services provisioned
- ✅ Credentials documented in secure location
- ✅ `.env.cloud` file created (not committed to git)

**Success Criteria:**

- All services show "Active" status in IBM Cloud dashboard
- Test API calls succeed for each service

---

#### Task 1.2: Update Dependencies (Day 2)

**Add to `requirements.txt`:**

```txt
# IBM Cloud SDKs
ibm-watsonx-ai>=1.0.0
ibm-watson>=8.0.0
ibm-cloud-sdk-core>=3.16.0
ibmcloudant>=0.7.0
ibm-cos-sdk>=2.13.0

# Additional utilities
python-dotenv>=1.0.0
```

**Install:**

```bash
pip install -r requirements.txt
```

**Deliverables:**

- ✅ Updated `requirements.txt`
- ✅ All packages installed successfully

---

#### Task 1.3: Create Cloud Module Structure (Day 3-4)

**Create new directory structure:**

```bash
mkdir -p app/cloud
touch app/cloud/__init__.py
touch app/cloud/config.py
touch app/cloud/watsonx_client.py
touch app/cloud/cloudant_client.py
touch app/cloud/cos_client.py
touch app/cloud/nlu_client.py
```

**File: `app/cloud/config.py`**

```python
"""
IBM Cloud Configuration Management
Centralizes all cloud service configuration and credentials
"""
import os
from typing import Literal
from dotenv import load_dotenv

load_dotenv()

# Backend Selection
AI_BACKEND = os.getenv("AI_BACKEND", "local")  # local | cloud | hybrid
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")  # local | cloud
DATABASE_BACKEND = os.getenv("DATABASE_BACKEND", "postgres")  # postgres | cloudant | hybrid
ENABLE_LOCAL_FALLBACK = os.getenv("ENABLE_LOCAL_FALLBACK", "true").lower() == "true"

# IBM watsonx.ai Configuration
WATSONX_CONFIG = {
    "api_key": os.getenv("IBM_WATSONX_API_KEY"),
    "project_id": os.getenv("IBM_WATSONX_PROJECT_ID"),
    "url": os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
    "model_id": os.getenv("IBM_WATSONX_MODEL_ID", "ibm/granite-3-8b-instruct"),
    "embedding_model": os.getenv("IBM_WATSONX_EMBEDDING_MODEL", "ibm/slate-125m-english-rtrvr"),
}

# IBM Watson NLU Configuration
NLU_CONFIG = {
    "api_key": os.getenv("IBM_NLU_API_KEY"),
    "url": os.getenv("IBM_NLU_URL"),
    "version": "2022-04-07",
}

# IBM Cloudant Configuration
CLOUDANT_CONFIG = {
    "api_key": os.getenv("IBM_CLOUDANT_API_KEY"),
    "url": os.getenv("IBM_CLOUDANT_URL"),
}

# IBM Cloud Object Storage Configuration
COS_CONFIG = {
    "api_key": os.getenv("IBM_COS_API_KEY"),
    "instance_id": os.getenv("IBM_COS_INSTANCE_ID"),
    "endpoint": os.getenv("IBM_COS_ENDPOINT"),
    "bucket_name": os.getenv("IBM_COS_BUCKET_NAME", "roster-documents"),
}

def validate_cloud_config() -> dict:
    """Validates that all required cloud credentials are present"""
    errors = []
    
    if AI_BACKEND == "cloud":
        if not WATSONX_CONFIG["api_key"]:
            errors.append("IBM_WATSONX_API_KEY is required")
        if not WATSONX_CONFIG["project_id"]:
            errors.append("IBM_WATSONX_PROJECT_ID is required")
    
    if DATABASE_BACKEND == "cloudant":
        if not CLOUDANT_CONFIG["api_key"]:
            errors.append("IBM_CLOUDANT_API_KEY is required")
        if not CLOUDANT_CONFIG["url"]:
            errors.append("IBM_CLOUDANT_URL is required")
    
    if STORAGE_BACKEND == "cloud":
        if not COS_CONFIG["api_key"]:
            errors.append("IBM_COS_API_KEY is required")
        if not COS_CONFIG["instance_id"]:
            errors.append("IBM_COS_INSTANCE_ID is required")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "backends": {
            "ai": AI_BACKEND,
            "storage": STORAGE_BACKEND,
            "database": DATABASE_BACKEND,
        }
    }
```

**Deliverables:**

- ✅ Cloud module structure created
- ✅ Configuration management implemented
- ✅ Validation function working

---

#### Task 1.4: Implement Feature Flags (Day 4-5)

**Update `.env.example`:**

```bash
# ============================================
# BACKEND SELECTION FLAGS
# ============================================
AI_BACKEND=local                    # local | cloud | hybrid
STORAGE_BACKEND=local               # local | cloud
DATABASE_BACKEND=postgres           # postgres | cloudant | hybrid
ENABLE_LOCAL_FALLBACK=true          # Fallback to local if cloud fails

# ============================================
# IBM WATSONX.AI CREDENTIALS
# ============================================
IBM_WATSONX_API_KEY=
IBM_WATSONX_PROJECT_ID=
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
IBM_WATSONX_MODEL_ID=ibm/granite-3-8b-instruct
IBM_WATSONX_EMBEDDING_MODEL=ibm/slate-125m-english-rtrvr

# ============================================
# IBM WATSON NLU CREDENTIALS
# ============================================
IBM_NLU_API_KEY=
IBM_NLU_URL=

# ============================================
# IBM CLOUDANT CREDENTIALS
# ============================================
IBM_CLOUDANT_API_KEY=
IBM_CLOUDANT_URL=

# ============================================
# IBM CLOUD OBJECT STORAGE CREDENTIALS
# ============================================
IBM_COS_API_KEY=
IBM_COS_INSTANCE_ID=
IBM_COS_ENDPOINT=
IBM_COS_BUCKET_NAME=roster-documents
```

**Deliverables:**

- ✅ `.env.example` updated with cloud variables
- ✅ Feature flags documented

---

## Phase 2: Core LLM Migration (Week 3-4)

### Objectives

- Implement watsonx.ai client
- Migrate LLM inference
- Migrate embeddings generation
- Implement fallback mechanism

### Tasks

#### Task 2.1: Implement watsonx.ai Client (Day 6-8)

**File: `app/cloud/watsonx_client.py`**

```python
"""
IBM watsonx.ai Client
Handles LLM inference and embeddings generation using IBM Granite models
"""
import os
import time
from typing import List, Optional, Dict, Any
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference, Embeddings
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import WATSONX_CONFIG
from ..logging_config import logger
from ..exceptions import LLMError, LLMTimeoutError, LLMConnectionError

class WatsonxClient:
    """Client for IBM watsonx.ai foundation models"""
    
    def __init__(self):
        """Initialize watsonx.ai client with credentials"""
        try:
            credentials = Credentials(
                api_key=WATSONX_CONFIG["api_key"],
                url=WATSONX_CONFIG["url"]
            )
            self.client = APIClient(credentials)
            self.project_id = WATSONX_CONFIG["project_id"]
            self.model_id = WATSONX_CONFIG["model_id"]
            self.embedding_model_id = WATSONX_CONFIG["embedding_model"]
            
            # Initialize model instances
            self._init_models()
            
            logger.info(f"✅ watsonx.ai client initialized: {self.model_id}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize watsonx.ai client: {e}")
            raise LLMConnectionError("Could not connect to watsonx.ai", str(e))
    
    def _init_models(self):
        """Initialize LLM and embedding models"""
        try:
            # LLM for text generation
            self.llm = ModelInference(
                model_id=self.model_id,
                api_client=self.client,
                project_id=self.project_id,
                params={
                    GenParams.DECODING_METHOD: "greedy",
                    GenParams.MAX_NEW_TOKENS: 2048,
                    GenParams.TEMPERATURE: 0.0,
                    GenParams.STOP_SEQUENCES: ["</think>", "<|endoftext|>"],
                    GenParams.REPETITION_PENALTY: 1.1,
                }
            )
            
            # Embeddings model
            self.embeddings = Embeddings(
                model_id=self.embedding_model_id,
                api_client=self.client,
                project_id=self.project_id
            )
            
            logger.debug("Models initialized successfully")
        except Exception as e:
            logger.error(f"Model initialization failed: {e}")
            raise
    
    def check_connectivity(self) -> bool:
        """Test connection to watsonx.ai"""
        try:
            # Simple test generation
            response = self.llm.generate_text(prompt="Hello", params={
                GenParams.MAX_NEW_TOKENS: 10
            })
            return bool(response)
        except Exception as e:
            logger.error(f"Connectivity check failed: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def generate_text(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.0
    ) -> str:
        """
        Generate text using Granite LLM
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic)
        
        Returns:
            Generated text
        """
        try:
            start_time = time.time()
            
            # Combine system and user prompts
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Add strict instruction to prevent thinking tags
            full_prompt += "\n\nSTRICT RULE: Do not output <think> tags or internal reasoning. Provide only the final response."
            
            response = self.llm.generate_text(
                prompt=full_prompt,
                params={
                    GenParams.MAX_NEW_TOKENS: max_tokens,
                    GenParams.TEMPERATURE: temperature,
                    GenParams.DECODING_METHOD: "greedy" if temperature == 0 else "sample",
                }
            )
            
            latency = time.time() - start_time
            logger.debug(f"LLM generation completed in {latency:.2f}s")
            
            # Clean response
            response = response.strip()
            # Remove any thinking tags that might appear
            import re
            response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
            
            return response
            
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise LLMError("watsonx.ai text generation failed", str(e))
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text
        
        Args:
            text: Input text to embed
        
        Returns:
            Embedding vector (768 dimensions for Slate model)
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return None
            
            start_time = time.time()
            
            # Generate embedding
            vector = self.embeddings.embed_query(text)
            
            latency = time.time() - start_time
            logger.debug(f"Embedding generated in {latency:.2f}s (dim: {len(vector)})")
            
            return vector
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise LLMError("watsonx.ai embedding generation failed", str(e))
    
    def generate_structured(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output
        
        Args:
            prompt: User prompt
            response_schema: JSON schema for response
            system_prompt: Optional system instruction
        
        Returns:
            Parsed JSON object
        """
        try:
            # Add schema to prompt
            schema_prompt = f"{system_prompt or ''}\n\nReturn ONLY a valid JSON object matching this schema:\n{response_schema}\n\n{prompt}"
            
            response_text = self.generate_text(
                prompt=prompt,
                system_prompt=schema_prompt,
                temperature=0.0
            )
            
            # Extract JSON from response
            import json
            import re
            
            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # Try parsing entire response
                return json.loads(response_text)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response_text}")
            raise LLMError("Failed to parse structured response", str(e))
        except Exception as e:
            logger.error(f"Structured generation failed: {e}")
            raise LLMError("watsonx.ai structured generation failed", str(e))
```

**Deliverables:**

- ✅ watsonx.ai client implemented
- ✅ Text generation working
- ✅ Embeddings generation working
- ✅ Error handling and retries implemented

---

#### Task 2.2: Implement Hybrid LLM Client (Day 9-10)

**File: `app/intelligence/hybrid_llm_client.py`**

```python
"""
Hybrid LLM Client
Supports both local (Ollama) and cloud (watsonx.ai) backends with automatic fallback
"""
import os
from typing import Optional, List
from .llm_client import LLMClient as LocalLLMClient
from ..cloud.watsonx_client import WatsonxClient
from ..cloud.config import AI_BACKEND, ENABLE_LOCAL_FALLBACK
from ..logging_config import logger
from ..exceptions import LLMError

class HybridLLMClient:
    """
    Unified LLM client that supports local and cloud backends
    Automatically falls back to local if cloud fails
    """
    
    def __init__(self, model_name=None):
        self.backend = AI_BACKEND
        self.enable_fallback = ENABLE_LOCAL_FALLBACK
        
        # Initialize clients based on backend
        self.cloud_client = None
        self.local_client = None
        
        if self.backend in ["cloud", "hybrid"]:
            try:
                self.cloud_client = WatsonxClient()
                logger.info(f"✅ Cloud LLM client initialized (watsonx.ai)")
            except Exception as e:
                logger.warning(f"⚠️ Cloud LLM initialization failed: {e}")
                if not self.enable_fallback:
                    raise
        
        if self.backend in ["local", "hybrid"] or (self.enable_fallback and not self.cloud_client):
            try:
                self.local_client = LocalLLMClient(model_name)
                logger.info(f"✅ Local LLM client initialized (Ollama)")
            except Exception as e:
                logger.warning(f"⚠️ Local LLM initialization failed: {e}")
                if self.backend == "local":
                    raise
    
    def _use_cloud(self) -> bool:
        """Determine if cloud should be used"""
        return self.backend == "cloud" or (self.backend == "hybrid" and self.cloud_client is not None)
    
    def check_connectivity(self) -> bool:
        """Check connectivity to active backend"""
        if self._use_cloud() and self.cloud_client:
            return self.cloud_client.check_connectivity()
        elif self.local_client:
            return self.local_client.check_connectivity()
        return False
    
    def request_raw_text(self, system_prompt: str, user_content: str) -> str:
        """Generate text using active backend with fallback"""
        if self._use_cloud() and self.cloud_client:
            try:
                return self.cloud_client.generate_text(
                    prompt=user_content,
                    system_prompt=system_prompt
                )
            except Exception as e:
                logger.error(f"❌ Cloud LLM failed: {e}")
                if self.enable_fallback and self.local_client:
                    logger.info("🔄 Falling back to local LLM")
                    return self.local_client.request_raw_text(system_prompt, user_content)
                raise
        elif self.local_client:
            return self.local_client.request_raw_text(system_prompt, user_content)
        else:
            raise LLMError("No LLM backend available")
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using active backend with fallback"""
        if self._use_cloud() and self.cloud_client:
            try:
                return self.cloud_client.get_embedding(text)
            except Exception as e:
                logger.error(f"❌ Cloud embedding failed: {e}")
                if self.enable_fallback and self.local_client:
                    logger.info("🔄 Falling back to local embeddings")
                    return self.local_client.get_embedding(text)
                raise
        elif self.local_client:
            return self.local_client.get_embedding(text)
        else:
            raise LLMError("No embedding backend available")
    
    # Delegate other methods to appropriate client
    def search_technical_taxonomy(self, query: str, db_session):
        client = self.cloud_client if self._use_cloud() else self.local_client
        if hasattr(client, 'search_technical_taxonomy'):
            return client.search_technical_taxonomy(query, db_session)
        return self.local_client.search_technical_taxonomy(query, db_session)
    
    def analyze_image_region(self, image_path: str, box: List[int]):
        # Vision not supported in Granite yet, use local
        if self.local_client:
            return self.local_client.analyze_image_region(image_path, box)
        raise LLMError("Vision analysis not available")
    
    def docling_parse(self, file_path: str):
        # Docling is local-only
        if self.local_client:
            return self.local_client.docling_parse(file_path)
        raise LLMError("Docling parsing not available")
```

**Update `app/intelligence/llm_client.py`:**

```python
# At the top of the file, add:
from ..cloud.config import AI_BACKEND

# Replace the LLMClient instantiation at the bottom with:
if AI_BACKEND in ["cloud", "hybrid"]:
    from .hybrid_llm_client import HybridLLMClient as LLMClient
# else: use existing LLMClient
```

**Deliverables:**

- ✅ Hybrid client implemented
- ✅ Automatic fallback working
- ✅ Backward compatibility maintained

---

## Phase 3: Storage Migration (Week 5-6)

### Objectives

- Implement Cloud Object Storage integration
- Implement Cloudant database integration
- Create data migration scripts
- Test hybrid mode

### Tasks

#### Task 3.1: Implement COS Client (Day 11-13)

**File: `app/cloud/cos_client.py`**

```python
"""
IBM Cloud Object Storage Client
Handles document upload, download, and management
"""
import os
import hashlib
from typing import Optional, BinaryIO
import ibm_boto3
from ibm_botocore.client import Config
from ibm_botocore.exceptions import ClientError

from .config import COS_CONFIG
from ..logging_config import logger
from ..exceptions import ExtractionError

class COSClient:
    """Client for IBM Cloud Object Storage"""
    
    def __init__(self):
        """Initialize COS client"""
        try:
            self.client = ibm_boto3.client(
                "s3",
                ibm_api_key_id=COS_CONFIG["api_key"],
                ibm_service_instance_id=COS_CONFIG["instance_id"],
                config=Config(signature_version="oauth"),
                endpoint_url=COS_CONFIG["endpoint"]
            )
            self.bucket_name = COS_CONFIG["bucket_name"]
            logger.info(f"✅ COS client initialized: {self.bucket_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize COS client: {e}")
            raise
    
    def upload_file(
        self,
        file_path: str,
        object_key: Optional[str] = None,
        folder: str = "uploads"
    ) -> str:
        """
        Upload file to COS
        
        Args:
            file_path: Local file path
            object_key: Optional custom object key
            folder: Folder prefix in bucket
        
        Returns:
            Object key in COS
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Generate object key if not provided
            if not object_key:
                file_hash = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
                file_ext = os.path.splitext(file_path)[1]
                object_key = f"{folder}/{file_hash}{file_ext}"
            
            # Upload
            self.client.upload_file(
                Filename=file_path,
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            logger.info(f"✅ Uploaded to COS: {object_key}")
            return object_key
            
        except ClientError as e:
            logger.error(f"❌ COS upload failed: {e}")
            raise ExtractionError(f"Failed to upload to COS", str(e))
    
    def download_file(
        self,
        object_key: str,
        local_path: str
    ) -> str:
        """
        Download file from COS
        
        Args:
            object_key: Object key in COS
            local_path: Local destination path
        
        Returns:
            Local file path
        """
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download
            self.client.download_file(
                Bucket=self.bucket_name,
                Key=object_key,
                Filename=local_path
            )
            
            logger.debug(f"Downloaded from COS: {object_key}")
            return local_path
            
        except ClientError as e:
            logger.error(f"❌ COS download failed: {e}")
            raise ExtractionError(f"Failed to download from COS", str(e))
    
    def delete_file(self, object_key: str) -> bool:
        """Delete file from COS"""
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            logger.debug(f"Deleted from COS: {object_key}")
            return True
        except ClientError as e:
            logger.error(f"❌ COS delete failed: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> list:
        """List files in COS bucket"""
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            return [obj['Key'] for obj in response.get('Contents', [])]
        except ClientError as e:
            logger.error(f"❌ COS list failed: {e}")
            return []
```

**Deliverables:**

- ✅ COS client implemented
- ✅ Upload/download working
- ✅ Error handling implemented

---

## Phase 4: Testing & Optimization (Week 7-8)

### Objectives

- Comprehensive testing
- Performance optimization
- Cost optimization
- Documentation updates

### Testing Checklist

#### Unit Tests

- [ ] watsonx.ai client connectivity
- [ ] Text generation with various prompts
- [ ] Embedding generation
- [ ] Fallback mechanism
- [ ] COS upload/download
- [ ] Cloudant CRUD operations

#### Integration Tests

- [ ] End-to-end resume parsing (cloud)
- [ ] End-to-end project parsing (cloud)
- [ ] Matching algorithm with cloud embeddings
- [ ] Hybrid mode switching
- [ ] Error recovery and fallback

#### Performance Tests

- [ ] LLM latency benchmarks
- [ ] Embedding generation speed
- [ ] Vector search performance
- [ ] Concurrent request handling
- [ ] Cost per operation

---

## Success Metrics

### Technical Metrics

- ✅ LLM latency < 3s (95th percentile)
- ✅ Embedding latency < 1s (95th percentile)
- ✅ API error rate < 1%
- ✅ Fallback success rate > 95%
- ✅ Zero data loss during migration

### Business Metrics

- ✅ Support 10x more concurrent users
- ✅ 99.9% uptime
- ✅ Cost within budget ($50/month for medium org)
- ✅ Zero downtime migration

---

## Rollback Plan

If migration fails:

1. **Immediate Rollback** (< 5 minutes)

   ```bash
   # Switch back to local
   export AI_BACKEND=local
   export DATABASE_BACKEND=postgres
   export STORAGE_BACKEND=local
   
   # Restart services
   docker-compose restart
   ```

2. **Data Recovery** (< 30 minutes)
   - Restore PostgreSQL from backup
   - Restore local files from backup
   - Verify data integrity

3. **Post-Mortem**
   - Document failure reasons
   - Update migration plan
   - Schedule retry

---

## Next Steps

1. **Review this roadmap** with team
2. **Start Phase 1** - Infrastructure setup
3. **Daily standups** to track progress
4. **Weekly demos** to stakeholders
5. **Continuous monitoring** of costs and performance

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-15  
**Author:** Bob (Planning Mode)  
**Status:** Ready for Implementation
