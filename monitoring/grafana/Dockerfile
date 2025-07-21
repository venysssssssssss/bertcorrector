FROM grafana/grafana:latest

# Copy provisioning files
COPY provisioning/ /etc/grafana/provisioning/

# Set environment variables
ENV GF_SECURITY_ADMIN_PASSWORD=admin123
ENV GF_USERS_ALLOW_SIGN_UP=false
ENV GF_INSTALL_PLUGINS=grafana-piechart-panel

EXPOSE 3000
