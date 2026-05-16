# IBM Cloud Credentials Setup Guide for Roster AI System

## Overview

This guide provides step-by-step instructions for obtaining all necessary IBM Cloud credentials for RosterAI

**Required Services:** 1 IBM Cloud services with 3 total credentials

---

## Prerequisites

1. **IBM Cloud Account**

   - Go to [https://cloud.ibm.com/registration](https://cloud.ibm.com/registration)
   - Sign up for a free IBM Cloud account
   - Verify your email address
   - **Note**: Credit card required but Lite tier is free
2. **IBM Cloud CLI (Optional but Recommended)**

   ```bash
   # Install IBM Cloud CLI
   curl -fsSL https://clis.cloud.ibm.com/install/linux | sh

   # Login
   ibmcloud login

   # Target your region (use Dallas/us-south for consistency)
   ibmcloud target -r us-south
   ```

---

## Service 1: IBM watsonx.ai (LLM & Embeddings)

### Step 1: Create watsonx.ai Project

1. **Access watsonx.ai**

   - Go to [https://dataplatform.cloud.ibm.com/wx/home](https://dataplatform.cloud.ibm.com/wx/home)
   - Or from IBM Cloud console: [https://cloud.ibm.com/watsonx/overview](https://cloud.ibm.com/watsonx/overview)
2. **Create a Project**

   - Click **Projects** in left sidebar
   - Click **New project**
   - Select **Create an empty project**
   - Project name: `roster-ai-production`
   - Description: "AI-powered resource allocation and team matching"
   - Storage: Select or create Cloud Object Storage instance (will be created automatically)
   - Click **Create**
3. **Get Project ID**

   - Once project is created, click **Manage** tab
   - Copy the **Project ID** (UUID format)
   - Save as: `IBM_WATSONX_PROJECT_ID`
   - Example: `12345678-abcd-1234-abcd-12345 6789abc`

### Step 2: Get watsonx.ai API Key

1. **Create IBM Cloud API Key**

   - Go to [https://cloud.ibm.com/iam/apikeys](https://cloud.ibm.com/iam/apikeys)
   - Click **Create an IBM Cloud API key**
   - Name: `roster-watsonx-apikey`
   - Description: "API key for Roster watsonx.ai access"
   - Click **Create**
   - **IMPORTANT:** Copy the API key immediately (shown only once)
   - Save as: `IBM_WATSONX_API_KEY`
2. **Get watsonx.ai URL**

   - Default URL: `https://us-south.ml.cloud.ibm.com`
   - If your project is in a different region:
     - US South (Dallas): `https://us-south.ml.cloud.ibm.com`
     - Frankfurt: `https://eu-de.ml.cloud.ibm.com`
     - Tokyo: `https://jp-tok.ml.cloud.ibm.com`
   - Save as: `IBM_WATSONX_URL`

### Step 3: Associate Watson Machine Learning Service

1. **In your watsonx.ai project, go to Manage tab**

   - Click **Services & integrations**
   - Click **Associate service**
   - Select **Watson Machine Learning**
2. **If you don't have Watson Machine Learning:**

   - Click **New service**
   - Select region: **US South (Dallas)**
   - Select plan: **Lite** (free tier)
   - Service name: `roster-watson-ml`
   - Click **Create**
   - Associate the service with your project
3. **Verify Model Access**

   - Go to **Assets** tab in your project
   - Click **New asset** → **Work with foundation models**
   - Verify you can see:
     - `ibm/granite-3-8b-instruct` (recommended for Roster)
     - `ibm/granite-13b-instruct-v2` (more powerful, slower)
     - `ibm/slate-125m-english-rtrvr` (embeddings)

### Step 4: Verify watsonx.ai Setup

Test with Python:

```python
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

credentials = Credentials(
    api_key="YOUR_WATSONX_API_KEY",
    url="https://us-south.ml.cloud.ibm.com"
)
client = APIClient(credentials)

model = ModelInference(
    model_id="ibm/granite-3-8b-instruct",
    api_client=client,
    project_id="YOUR_PROJECT_ID"
)

response = model.generate_text(prompt="What is Python?")
print(response)
```

**Credentials Summary:**

- ✅ `IBM_WATSONX_API_KEY` - IAM API key
- ✅ `IBM_WATSONX_PROJECT_ID` - Project UUID
- ✅ `IBM_WATSONX_URL` - Regional endpoint

---

## Complete .env Configuration

After obtaining all credentials, create/update your `.env` file:

```bash
# IBM WATSONX.AI CONFIGURATION 

IBM_WATSONX_API_KEY=your_watsonx_api_key_here
IBM_WATSONX_PROJECT_ID=your_watsonx_project_id_here
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com

# Model Configuration
IBM_WATSONX_MODEL_ID=meta-llama/llama-3-2-11b-vision-instruct
IBM_WATSONX_EMBEDDING_MODEL=intfloat/multilingual-e5-large

# LLM Timeout (seconds)
LLM_TIMEOUT=600

# LOCAL DATABASE CONFIGURATION 
DATABASE_URL=postgresql://postgres:password@localhost:5432/roster
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=roster

# LOCAL REDIS CONFIGURATION 

REDIS_HOST=localhost
REDIS_PORT=6379

# APPLICATION CONFIGURATION

# Server
HOST=0.0.0.0
PORT=8000

# Logging
LOG_LEVEL=INFO

# Organization Context
ORG_NAME=Your Org Name
ORG_CONTEXT=""

# Document Processing
TEMP_UPLOAD_DIR=./temp_processing
PARSED_RESUMES_DIR=./parsed_resumes
PROJECTS_DIR=./projects
RESUMES_DIR=./resumes

```

---

## Credential Security Best Practices

### 1. Never Commit Credentials to Git

```bash
# Ensure .env is in .gitignore
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Ensure .env is ignored"
```

### 2. Use Environment Variables in Production

For deployment platforms (Heroku, AWS, Azure, etc.):

```bash
# Set environment variables
export IBM_WATSONX_API_KEY="your_key"
export IBM_CLOUDANT_API_KEY="your_key"
# ... etc
```

### 3. Rotate API Keys Regularly

- Go to IBM Cloud console
- Delete old credentials
- Create new credentials
- Update your .env file
- Recommended: Rotate every 90 days

### 4. Use IAM Access Groups (Production)

For team environments:

1. Create service IDs for applications
2. Assign minimal required permissions
3. Use access groups for team management
4. Enable MFA for all team members

### 5. Monitor API Usage

- Go to [https://cloud.ibm.com/billing/usage](https://cloud.ibm.com/billing/usage)
- View usage by service
- Set up spending notifications
- Review access logs regularly

---

## Troubleshooting

### Issue: "Invalid API Key"

**Solution:**

1. Verify API key is copied correctly (no extra spaces)
2. Check if API key is for the correct service
3. Ensure API key hasn't been deleted or rotated
4. Regenerate credentials if needed

### Issue: "Project ID not found"

**Solution:**

1. Verify project ID format (UUID without dashes in some cases)
2. Check if project is in the correct region
3. Ensure Watson Machine Learning is associated with project
4. Verify you have access to the project

### Issue: "Insufficient permissions"

**Solution:**

1. Recreate service credentials with **Manager** or **Writer** role
2. Verify IAM permissions for your IBM Cloud account
3. Check if service is properly associated with project (watsonx.ai)
4. Ensure you're using the correct API key for each service

### Issue: "Region mismatch"

**Solution:**

1. Ensure all services are in the same region (Dallas/us-south recommended)
2. Update region in .env to match service region
3. Check service URL contains correct region
4. Verify endpoint URLs match your service locations

---

## Quick Reference: All Required Credentials

| Service    | Credential Name            | Where to Find         | Format             |
| ---------- | -------------------------- | --------------------- | ------------------ |
| watsonx.ai | `IBM_WATSONX_API_KEY`    | IAM → API keys       | String (40+ chars) |
| watsonx.ai | `IBM_WATSONX_PROJECT_ID` | Project → Manage tab | UUID format        |
| watsonx.ai | `IBM_WATSONX_URL`        | Region-specific       | Full HTTPS URL     |

**Total: 3 credentials required**

---

## Cost Monitoring

### Free Tier Limits

**watsonx.ai**: Limited free tokens per month

### Setting Up Spending Notifications

1. Go to [https://cloud.ibm.com/billing/spending-notifications](https://cloud.ibm.com/billing/spending-notifications)
2. Click **Create notification**
3. Set threshold (e.g., $10, $50, $100)
4. Add email addresses
5. Click **Create**

### Monitoring Usage

- Dashboard: [https://cloud.ibm.com/billing/usage](https://cloud.ibm.com/billing/usage)
- View usage by service
- Export usage reports
- Set up alerts for approaching limits

---

## Support Resources

- **IBM Cloud Support**: [https://cloud.ibm.com/unifiedsupport/supportcenter](https://cloud.ibm.com/unifiedsupport/supportcenter)
- **watsonx.ai Documentation**: [https://www.ibm.com/docs/en/watsonx-as-a-service](https://www.ibm.com/docs/en/watsonx-as-a-service)

---

**Document Version:** 1.0
**Last Updated:** 2026-05-15
**Author:** Bob (Planning Mode)
**Status:** Ready for Use
