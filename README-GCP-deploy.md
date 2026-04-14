# PDF RAG API – Deployment on GCP (Cloud Run)

This repository contains a FastAPI-based Retrieval-Augmented Generation (RAG) service deployed on Google Cloud Run. It answers questions over documents using embeddings and an LLM.

---

## Overview

This project demonstrates a production-style deployment:

* FastAPI backend
* RAG pipeline (embeddings + retrieval + LLM)
* Google Cloud Run (serverless container)
* Cloud Build (automatic containerization)
* Artifact Registry (image storage)
* Secret Manager (secure API key handling)

---

## Architecture

```
Client → Cloud Run → FastAPI → OpenAI API
```

Note:

* Local files are not available in Cloud Run
* Use external storage (e.g., GCS) for production data

---

## Project Structure

```
.
├── main.py
├── requirements.txt
├── Procfile
└── README.md
```

---

## Prerequisites

* Google Cloud Project
* Billing enabled
* Cloud Shell or gcloud CLI
* OpenAI API key

---

## Setup and Deployment

### 1. Set Project

```bash
gcloud config set project llm-pdf-493302
```

---

### 2. Enable Services

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

---

### 3. Store API Key in Secret Manager

```bash
echo -n "YOUR_API_KEY" | gcloud secrets create OPENAI_API_KEY --data-file=-
```

To update later:

```bash
echo -n "YOUR_API_KEY" | gcloud secrets versions add OPENAI_API_KEY --data-file=-
```

Important:

* Do not include quotes in the key value

---

### 4. Grant Access to Cloud Run

```bash
gcloud secrets add-iam-policy-binding OPENAI_API_KEY \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

### 5. Procfile (required for Buildpacks)

Create a file named `Procfile`:

```
web: uvicorn main:app --host 0.0.0.0 --port ${PORT}
```

---

### 6. Deploy to Cloud Run

```bash
gcloud run deploy pdf-rag-app \
  --source . \
  --region northamerica-northeast1 \
  --allow-unauthenticated \
  --set-secrets OPENAI_API_KEY=OPENAI_API_KEY:latest
```

When prompted:

```
Do you want to continue (Y/n)?
```

Type:

```
Y
```

---

## Endpoints

### Health Check

```
GET /health
```

Test:

```bash
curl https://YOUR_URL/health
```

---

### Ask Question

```
POST /ask
```

Test:

```bash
curl -X POST https://YOUR_URL/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the project duration?"}'
```

---

## Common Issues

| Issue                    | Fix                          |
| ------------------------ | ---------------------------- |
| gcloud not recognized    | Use Cloud Shell              |
| Build failed             | Deploy from correct folder   |
| Secret permission denied | Add IAM binding              |
| Invalid API key          | Remove quotes, update secret |
| Method Not Allowed       | Use POST endpoint            |
| Not Found                | Root endpoint not defined    |
| Upload too large         | Remove large files           |

---

## Notes

* Do not include large datasets in deployment
* Use Google Cloud Storage for documents
* Environment variables come from Secret Manager, not `.env`

---

## Next Improvements

* Integrate Google Cloud Storage for documents
* Add frontend (Streamlit or web UI)
* Add authentication layer
* Improve retrieval with reranking
* Add monitoring and logging

---

## Deployment Pipeline

```
Code → Cloud Build → Container → Cloud Run → Public API
```

---


