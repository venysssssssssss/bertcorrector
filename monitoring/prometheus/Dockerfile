FROM prom/prometheus:latest

# Copy configuration files
COPY prometheus.yml /etc/prometheus/prometheus.yml
COPY rules/ /etc/prometheus/rules/

# Set proper permissions
USER root
RUN chown -R prometheus:prometheus /etc/prometheus
USER prometheus

EXPOSE 9090
