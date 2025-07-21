FROM nginx:alpine

# Install OpenSSL for self-signed certificates
RUN apk add --no-cache openssl

# Copy configuration
COPY grafana.conf /etc/nginx/conf.d/default.conf

# Create SSL directory
RUN mkdir -p /etc/nginx/ssl

# Generate self-signed certificate (para desenvolvimento)
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/grafana.key \
    -out /etc/nginx/ssl/grafana.crt \
    -subj "/C=BR/ST=State/L=City/O=Organization/CN=localhost"

# Copy custom nginx.conf if needed
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
