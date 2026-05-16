# IBM Cloud Quick Start Guide

## 🚀 Get Started in 30 Minutes

This guide helps you quickly set up and test IBM Cloud integration for the Roster AI system.

---

## Prerequisites

- ✅ IBM Cloud account (free tier available)
- ✅ Python 3.10+
- ✅ Git
- ✅ 30 minutes of time

---

## Step 1: Clone and Setup (5 minutes)

```bash
# Clone repository
git clone <repo-url>
cd JobGiver_LocalAI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: Provision IBM Cloud Services (10 minutes)

Follow the **[IBM Cloud Credentials Setup Guide](./IBM_CLOUD_CREDENTIALS_SETUP.md)** to:

1. Create IBM Cloud account
2. Provision 4 services:
   - watsonx.ai (LLM & embeddings)
   - Watson NLU (sentiment analysis)
   - Cloudant (database)
   - Cloud Object Storage (document storage)
3. Obtain 11 credentials

**Quick Links:**

- watsonx.ai: <https://dataplatform.cloud.ibm.com/wx/home>
- IBM Cloud Console: <https://cloud.ibm.com/resources>

---

## Step 3: Configure Environment (5 minutes)

Create `.env` file:

```bash
cp .env.example .env
```

Add your IBM Cloud credentials:

```bash
# Backend Selection
AI_BACKEND=cloud
STORAGE_BACKEND=cloud
DATABASE_BACKEND=cloudant
ENABLE_LOCAL_FALLBACK=true

# IBM watsonx.ai
IBM_WATSONX_API_KEY=your_key_here
IBM_WATSONX_PROJECT_ID=your_project_id_here
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com

# IBM Cloudant
IBM_CLOUDANT_API_KEY=your_key_here
IBM_CLOUDANT_URL=https://your-instance.cloudantnosqldb.appdomain.cloud

# IBM Cloud Object Storage
IBM_COS_API_KEY=your_key_here
IBM_COS_INSTANCE_ID=your_instance_id_here
IBM_COS_ENDPOINT=https://s3.us-south.cloud-object-storage.appdomain.cloud
IBM_COS_BUCKET_NAME=roster-documents

# IBM Watson NLU (optional)
IBM_NLU_API_KEY=your_key_here
IBM_NLU_URL=https://api.us-south.natural-language-understanding.watson.cloud.ibm.com
```

---

## Step 4: Test Connection (5 minutes)

Create `test_cloud.py`:

```python
from app.cloud.watsonx_client import WatsonxClient
from app.cloud.cloudant_client import CloudantClient
from app.cloud.cos_client import COSClient

# Test watsonx.ai
print("Testing watsonx.ai...")
wx = WatsonxClient()
response = wx.generate_text("What is Python?")
print(f"✅ LLM Response: {response[:100]}...")

# Test embeddings
print("\nTesting embeddings...")
vector = wx.get_embedding("Hello world")
print(f"✅ Embedding dimension: {len(vector)}")

# Test Cloudant
print("\nTesting Cloudant...")
cloudant = CloudantClient()
cloudant.create_database("test_db")
print("✅ Cloudant connected")

# Test COS
print("\nTesting Cloud Object Storage...")
cos = COSClient()
with open("test.txt", "w") as f:
    f.write("Hello from Roster AI!")
key = cos.upload_file("test.txt", folder="test")
print(f"✅ COS upload successful: {key}")

print("\n🎉 All services connected successfully!")
```

Run test:

```bash
python test_cloud.py
```

---

## Step 5: Run the Application (5 minutes)

### Option A: Cloud-Only Mode

```bash
# Set environment
export AI_BACKEND=cloud
export DATABASE_BACKEND=cloudant
export STORAGE_BACKEND=cloud

# Start application
uvicorn app.main:app --reload
```

### Option B: Hybrid Mode (Recommended for Testing)

```bash
# Set environment
export AI_BACKEND=hybrid
export DATABASE_BACKEND=hybrid
export STORAGE_BACKEND=cloud
export ENABLE_LOCAL_FALLBACK=true

# Start local services
docker-compose up -d postgres redis

# Start application
uvicorn app.main:app --reload
```

### Option C: Local Mode with Cloud Fallback

```bash
# Set environment
export AI_BACKEND=local
export ENABLE_LOCAL_FALLBACK=true

# Start all local services
docker-compose up -d

# Start application
uvicorn app.main:app --reload
```

---

## Verify Installation

1. **Open browser**: <http://localhost:8000>
2. **Check status**: <http://localhost:8000/api/status>
3. **Upload a resume**: Use the frontend or API
4. **Check logs**: Look for "✅ watsonx.ai" messages

---

## Common Issues

### Issue: "Invalid API Key"

**Solution:**

```bash
# Verify credentials
python -c "from app.cloud.config import validate_cloud_config; print(validate_cloud_config())"
```

### Issue: "Connection timeout"

**Solution:**

```bash
# Check network connectivity
curl -I https://us-south.ml.cloud.ibm.com

# Enable fallback
export ENABLE_LOCAL_FALLBACK=true
```

### Issue: "Bucket not found"

**Solution:**

```python
# Create bucket
from app.cloud.cos_client import COSClient
cos = COSClient()
cos.client.create_bucket(
    Bucket="roster-documents",
    CreateBucketConfiguration={"LocationConstraint": "us-south-standard"}
)
```

---

## Next Steps

1. ✅ **Read the full migration plan**: [IBM_CLOUD_MIGRATION_PLAN.md](./IBM_CLOUD_MIGRATION_PLAN.md)
2. ✅ **Review architecture**: [IBM_CLOUD_ARCHITECTURE_DIAGRAM.md](./IBM_CLOUD_ARCHITECTURE_DIAGRAM.md)
3. ✅ **Follow implementation roadmap**: [IBM_CLOUD_IMPLEMENTATION_ROADMAP.md](./IBM_CLOUD_IMPLEMENTATION_ROADMAP.md)
4. ✅ **Monitor costs**: <https://cloud.ibm.com/billing/usage>

---

## Cost Monitoring

### Free Tier Limits

- **watsonx.ai**: Limited free tokens/month
- **Watson NLU**: 30,000 items/month
- **Cloudant**: 1GB storage, 20 lookups/sec
- **COS**: 25GB storage

### Set Up Alerts

```bash
# IBM Cloud CLI
ibmcloud login
ibmcloud billing spending-notification-create \
  --threshold 10 \
  --email your@email.com
```

---

## Support

- **Documentation**: See `docs/` folder
- **IBM Cloud Support**: <https://cloud.ibm.com/unifiedsupport/supportcenter>
- **Community**: <https://community.ibm.com/community/user/watsonai/home>

---

## Architecture Overview

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────┐
│           FastAPI Backend                    │
│  ┌────────────────────────────────────────┐ │
│  │      Hybrid LLM Client                 │ │
│  │  ┌──────────┐      ┌──────────┐       │ │
│  │  │ watsonx  │ ◄──► │  Ollama  │       │ │
│  │  │  (Cloud) │      │ (Local)  │       │ │
│  │  └──────────┘      └──────────┘       │ │
│  └────────────────────────────────────────┘ │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│         IBM Cloud Services                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ watsonx  │  │ Cloudant │  │   COS    │  │
│  │   .ai    │  │ Database │  │ Storage  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────┘
```

---

**Quick Start Version:** 1.0  
**Last Updated:** 2026-05-15  
**Estimated Time:** 30 minutes  
**Difficulty:** Beginner-Friendly
