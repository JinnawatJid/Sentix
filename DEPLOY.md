# Sentix Bot - Google Cloud Run Deployment Guide

## 1. Prerequisites
- Google Cloud SDK installed (`gcloud`).
- A Google Cloud Project created.

## 2. Environment Variables
You need to set the following secrets in Cloud Run:
- `GEMINI_API_KEY`
- `TWITTER_CONSUMER_KEY`
- `TWITTER_CONSUMER_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_TOKEN_SECRET`
- `DATABASE_URL` (Optional: If using Cloud SQL. Defaults to local SQLite if unset, which is **NOT** persistent in Cloud Run).

**Important:** For persistence in Cloud Run, you MUST use an external database (like Cloud SQL / PostgreSQL) because Cloud Run containers are stateless (local files like `sentix.db` disappear on restart).

## 3. Deployment Steps

### Step 1: Build & Push Docker Image
```bash
export PROJECT_ID="your-google-cloud-project-id"
gcloud builds submit --tag gcr.io/$PROJECT_ID/sentix-bot
```

### Step 2: Deploy to Cloud Run
```bash
gcloud run deploy sentix-bot \
  --image gcr.io/$PROJECT_ID/sentix-bot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --set-env-vars "DATABASE_URL=postgresql://user:pass@host:5432/dbname"
```
*(Note: Remove `--allow-unauthenticated` if you want to restrict access to IAM users only)*

## 4. Database Setup (Cloud SQL)
1. Create a Cloud SQL instance (PostgreSQL 14+).
2. Create a database (e.g., `sentix`).
3. Create a user.
4. Connect Cloud Run to Cloud SQL (add `--add-cloudsql-instances INSTANCE_CONNECTION_NAME` to the deploy command).

## 5. Accessing the Dashboard
Once deployed, Cloud Run will provide a URL (e.g., `https://sentix-bot-xyz.a.run.app`).
Navigate there to see your Dashboard.
