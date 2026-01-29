#!/bin/bash

# ==========================================
# 🚀 AGENT OPS: Master Dual-Deployment Script
# Usage: ./deploy.sh "Commit Message"
# ==========================================

# 1. CONFIGURATION
export GCP_PROJECT_ID="gen-ai-accel-dev"
export REGION="us-central1"

# --- NEW: TELEMETRY & OBSERVABILITY (From Screenshot) ---
# Enables traces and logs for debugging
export GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
# Enables logging of prompt text (Inputs/Outputs)
export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true

# 2. Grab Commit Message
MSG="$1"
if [ -z "$MSG" ]; then
    MSG="Auto-update agent"
fi

echo "========================================"
echo "🕵️  PHASE 1: QUALITY GATE (Running Tests)"
echo "========================================"

# We pass the project ID explicitly to Python
GCP_PROJECT_ID=$GCP_PROJECT_ID python3 tests/evaluate.py
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ TESTS FAILED. Aborting deployment."
    echo "   (Check the logs above for details)"
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
    echo "⚠️  No local changes. Pushing empty commit to trigger build..."
    git commit --allow-empty -m "Trigger Build: $MSG"
    git push origin main
fi

echo ""
echo "========================================"
echo "🧠 PHASE 3: VERTEX AI AGENT ENGINE DEPLOY"
echo "========================================"

echo "🚀 Deploying 'brady_agent' to Vertex AI..."
echo "   Project: $GCP_PROJECT_ID"
echo "   Telemetry: ENABLED"

# UPDATED: The ADK will pick up the exported telemetry variables above
adk deploy agent_engine brady_agent \
    --project "$GCP_PROJECT_ID" \
    --region "$REGION" \
    --display_name "Brady Logistics Agent"

if [ $? -eq 0 ]; then
    echo "✅ Agent Engine Deployment Complete!"
else
    echo "❌ Agent Engine Deployment Failed."
fi

echo ""
echo "🎉 DUAL DEPLOYMENT FINISHED."