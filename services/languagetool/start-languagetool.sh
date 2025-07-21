#!/bin/bash

# LanguageTool Startup Script with Custom Configuration
echo "🚀 Starting LanguageTool Server with custom Portuguese rules..."

# Set default values
LANGUAGETOOL_PORT=${LANGUAGETOOL_PORT:-8010}
LANGUAGETOOL_CONFIG=${LANGUAGETOOL_CONFIG:-/app/config}

# Java options for performance
export JAVA_OPTS="${JAVA_OPTS:--Xmx4g -Xms2g -XX:+UseG1GC -XX:MaxGCPauseMillis=200}"

echo "📋 Configuration:"
echo "   Port: ${LANGUAGETOOL_PORT}"
echo "   Config: ${LANGUAGETOOL_CONFIG}"
echo "   Java Options: ${JAVA_OPTS}"
echo "   Rules Directory: /app/rules"
echo "   User Dictionary: /app/userdict"

# Check if custom rules exist
if [ -d "/app/rules" ] && [ "$(ls -A /app/rules)" ]; then
    echo "✅ Custom rules found in /app/rules"
    RULES_PATH="/app/rules"
else
    echo "⚠️  No custom rules found, using default rules"
    RULES_PATH=""
fi

# Check if user dictionary exists
if [ -f "/app/userdict/portuguese.txt" ]; then
    echo "✅ Custom user dictionary found"
    USER_DICT="/app/userdict/portuguese.txt"
else
    echo "⚠️  No custom user dictionary found"
    USER_DICT=""
fi

# Build LanguageTool command
LT_COMMAND="java ${JAVA_OPTS} -cp /LanguageTool/languagetool-server.jar org.languagetool.server.HTTPServer"

# Add configuration parameters
LT_COMMAND="${LT_COMMAND} --port ${LANGUAGETOOL_PORT}"
LT_COMMAND="${LT_COMMAND} --public"
LT_COMMAND="${LT_COMMAND} --allow-origin '*'"

# Add custom rules if available
if [ -n "${RULES_PATH}" ]; then
    LT_COMMAND="${LT_COMMAND} --rules-file ${RULES_PATH}"
fi

# Add user dictionary if available
if [ -n "${USER_DICT}" ]; then
    LT_COMMAND="${LT_COMMAND} --config-file ${LANGUAGETOOL_CONFIG}/languagetool.properties"
fi

# Enable verbose logging for debugging
LT_COMMAND="${LT_COMMAND} --verbose"

echo "🔧 Starting LanguageTool with command:"
echo "   ${LT_COMMAND}"

# Start LanguageTool server
exec ${LT_COMMAND}
