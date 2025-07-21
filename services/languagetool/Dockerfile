# Use LanguageTool official image as base
FROM erikvl87/languagetool:latest

# Maintainer information
LABEL maintainer="bertcorrector-team"
LABEL version="2.0.0"
LABEL description="LanguageTool server with custom Portuguese rules and monitoring"

# Switch to root to copy files
USER root

# Configure Java options for better performance
ENV JAVA_OPTS="-Xmx4g -Xms2g -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -XX:+UseStringDeduplication"

# LanguageTool specific configurations
ENV LANGUAGETOOL_PORT=8010
ENV LANGUAGETOOL_CONFIG=/app/config

# Create directories for custom rules and configurations
RUN mkdir -p /app/rules \
    && mkdir -p /app/config \
    && mkdir -p /app/cache \
    && mkdir -p /app/userdict

# Copy custom Portuguese rules
COPY rules/ /app/rules/
COPY config/ /app/config/
COPY userdict/ /app/userdict/

# Create custom LanguageTool configuration
COPY languagetool.properties /app/config/
COPY start-languagetool.sh /app/

# Make start script executable
RUN chmod +x /app/start-languagetool.sh

# Set working directory
WORKDIR /app

# Switch back to languagetool user
USER languagetool

# Expose port
EXPOSE 8010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8010/v2/check?text=test || exit 1

# Start LanguageTool with custom configuration
CMD ["/app/start-languagetool.sh"]
