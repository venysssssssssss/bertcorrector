#!/bin/bash

# SpaCy Enhancer Service Startup Script
echo "🚀 Starting SpaCy Enhancer Service..."

# Set default values
SPACY_PORT=${SPACY_PORT:-8020}
WORKERS=${WORKERS:-2}
SPACY_MODEL=${SPACY_MODEL:-pt_core_news_lg}

echo "📋 Configuration:"
echo "   Port: ${SPACY_PORT}"
echo "   Workers: ${WORKERS}"
echo "   SpaCy Model: ${SPACY_MODEL}"

# Check if SpaCy model is available
echo "🔍 Checking SpaCy model availability..."
python -c "import spacy; spacy.load('${SPACY_MODEL}')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ SpaCy model '${SPACY_MODEL}' is available"
else
    echo "⚠️  SpaCy model '${SPACY_MODEL}' not found, trying to download..."
    python -m spacy download ${SPACY_MODEL}
    
    if [ $? -eq 0 ]; then
        echo "✅ SpaCy model downloaded successfully"
    else
        echo "❌ Failed to download SpaCy model, falling back to smaller model"
        export SPACY_MODEL=pt_core_news_sm
        python -m spacy download pt_core_news_sm
    fi
fi

# Start the service
echo "🚀 Starting SpaCy Enhancer on port ${SPACY_PORT}..."
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port ${SPACY_PORT} \
    --workers ${WORKERS} \
    --log-level info \
    --access-log
