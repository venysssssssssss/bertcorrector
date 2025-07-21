FROM prom/prometheus:latest

# Copy configuration files
COPY prometheus.yml /etc/prometheus/prometheus.yml
COPY rules/ /etc/prometheus/rules/

# Set proper permissions (use nobody:nogroup which exists in alpine)
USER root
RUN chown -R nobody:nogroup /etc/prometheus
USER nobody

EXPOSE 9090
