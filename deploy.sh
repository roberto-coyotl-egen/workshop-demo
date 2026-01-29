#!/bin/bash

# ==========================================
# 🚀 AGENT OPS: Master Dual-Deployment Script
# Usage: ./deploy.sh "Commit Message"
# ==========================================

# 1. Load Environment Variables (Project ID)
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Hardcoded Configuration
STAGING_BUCKET="gs://adk_agent_enging_staging"  # <--- FIXED HERE
REGION="us-central1"

if [ -z "$GCP_PROJECT_ID" ]; then
    echo "❌ Error: GCP_PROJECT_ID is missing in .env"
    exit 1
fi

# 2. Grab Commit Message
MSG="$1"
if [ -z "$MSG" ]; then
    MSG="Auto-update agent"
fi

echo "========================================"
echo "🕵️  PHASE 1: QUALITY GATE (Running Tests)"
echo "========================================"

python3 tests/evaluate.py
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ TESTS FAILED. Aborting deployment."
    exit 1
fi

echo ""
echo "✅ TESTS PASSED."
echo ""

echo "========================================"
echo "☁️  PHASE 2: CLOUD RUN DEPLOY (via Git)"
echo "========================================"

if [[ `git status --porcelain` ]]; then
    git add .
    git commit -m "$MSG"
    git push origin main
    echo "✅ Pushed to GitHub -> Triggering Cloud Build."
else
    echo "⚠️  No changes to commit. Skipping Git Push."
fi

echo ""
echo "========================================"
echo "🧠 PHASE 3: VERTEX AI AGENT ENGINE DEPLOY"
echo "========================================"

echo "🚀 Deploying 'brady_agent' to Vertex AI..."
echo "   Target Bucket: $STAGING_BUCKET"

# The ADK command to deploy to the managed engine
adk deploy agent_engine brady_agent \
    --project "$GCP_PROJECT_ID" \
    --region "$REGION" \
    --staging_bucket "$STAGING_BUCKET" \
    --display_name "Brady Logistics Agent"

if [ $? -eq 0 ]; then
    echo "✅ Agent Engine Deployment Complete!"
else
    echo "❌ Agent Engine Deployment Failed."
    # Don't exit 1 here so we can still see the Cloud Build URL below if that part worked
fi

echo ""
echo "🎉 DUAL DEPLOYMENT FINISHED."