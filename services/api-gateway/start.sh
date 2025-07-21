#!/bin/bash

# API Gateway Startup Script
echo "🚀 Starting API Gateway Service..."

# Set default values
GATEWAY_PORT=${GATEWAY_PORT:-8000}
GATEWAY_WORKERS=${GATEWAY_WORKERS:-4}
LANGUAGETOOL_URL=${LANGUAGETOOL_URL:-http://languagetool:8010}
SPACY_URL=${SPACY_URL:-http://spacy-enhancer:8020}

echo "📋 Configuration:"
echo "   Port: ${GATEWAY_PORT}"
echo "   Workers: ${GATEWAY_WORKERS}"
echo "   LanguageTool URL: ${LANGUAGETOOL_URL}"
echo "   SpaCy URL: ${SPACY_URL}"

# Wait for dependencies to be ready
echo "⏳ Waiting for dependencies..."

# Wait for LanguageTool
echo "🔍 Checking LanguageTool availability..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if curl -s -f "${LANGUAGETOOL_URL}/v2/check?text=test" > /dev/null; then
        echo "✅ LanguageTool is ready"
        break
    fi
    echo "⏳ LanguageTool not ready, waiting... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    echo "⚠️  LanguageTool not ready after ${timeout}s, starting anyway..."
fi

# Wait for SpaCy (optional)
echo "🔍 Checking SpaCy availability..."
timeout=30
counter=0
while [ $counter -lt $timeout ]; do
    if curl -s -f "${SPACY_URL}/health" > /dev/null; then
        echo "✅ SpaCy is ready"
        break
    fi
    echo "⏳ SpaCy not ready, waiting... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    echo "⚠️  SpaCy not ready after ${timeout}s, starting anyway..."
fi

# Start the gateway
echo "🚀 Starting API Gateway on port ${GATEWAY_PORT}..."
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port ${GATEWAY_PORT} \
    --workers ${GATEWAY_WORKERS} \
    --log-level info \
    --access-log
