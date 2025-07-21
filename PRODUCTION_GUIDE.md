# LanguageTool Corrector - Production Documentation

## Overview

This is a scalable, production-ready text correction system built with LanguageTool as the primary grammar correction engine, enhanced with SpaCy for semantic analysis. The system is designed for high availability, monitoring, and easy deployment.

## Architecture

### Core Services
- **API Gateway** (Port 8000): FastAPI-based request orchestration with rate limiting and caching
- **LanguageTool Server** (Port 8010): Java-based grammar correction engine with custom Portuguese rules
- **SpaCy Enhancer** (Port 8020): Python-based semantic analysis and contextual suggestions
- **Redis Cache** (Port 6379): High-performance caching layer
- **NGINX Proxy** (Port 80/443): Load balancing and SSL termination

### Monitoring Stack
- **Prometheus** (Port 9090): Metrics collection and alerting
- **Grafana** (Port 3000): Dashboards and visualization
- **Loki**: Centralized logging (integrated with Grafana)

## Quick Start

### Prerequisites
- Ubuntu/Debian Linux (recommended)
- 4 vCPUs, 8GB RAM minimum
- Docker and Docker Compose
- 20GB free disk space

### Installation

1. **Clone and setup:**
```bash
git clone <repository>
cd bertcorrector
```

2. **Deploy the system:**
```bash
./scripts/deploy.sh deploy
```

3. **Check system health:**
```bash
./scripts/health-check.sh
```

4. **Access services:**
- API: http://localhost:8000
- Grafana: http://localhost:3000 (admin/admin123)
- Prometheus: http://localhost:9090

## API Usage

### Basic Text Correction
```bash
curl -X POST "http://localhost:8000/correct" \
  -H "Content-Type: application/json" \
  -d '{"text": "eu gosta de programar em python"}'
```

### Response Format
```json
{
  "original_text": "eu gosta de programar em python",
  "corrected_text": "eu gosto de programar em Python",
  "corrections": [
    {
      "offset": 3,
      "length": 5,
      "message": "Concordância verbal incorreta",
      "suggestions": ["gosto"],
      "category": "GRAMMAR"
    }
  ],
  "enhancements": [
    {
      "offset": 25,
      "length": 6,
      "suggestion": "Python",
      "reason": "proper_noun_capitalization"
    }
  ],
  "processing_time": 0.145,
  "confidence": 0.92
}
```

### Advanced Options
```bash
# Enable only grammar checks
curl -X POST "http://localhost:8000/correct?enable_spacy=false" \
  -H "Content-Type: application/json" \
  -d '{"text": "meu texto"}'

# Batch processing
curl -X POST "http://localhost:8000/correct/batch" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["texto 1", "texto 2", "texto 3"]}'
```

## Management Commands

### Service Management
```bash
# Deploy complete system
./scripts/deploy.sh deploy

# Start services
./scripts/deploy.sh start

# Stop services
./scripts/deploy.sh stop

# Restart services
./scripts/deploy.sh restart

# View service status
./scripts/deploy.sh status

# View logs
./scripts/deploy.sh logs [service-name]

# Run tests
./scripts/deploy.sh test

# Clean everything
./scripts/deploy.sh clean
```

### Health Monitoring
```bash
# Comprehensive health check
./scripts/health-check.sh

# Service-specific logs
docker-compose logs -f api-gateway
docker-compose logs -f languagetool-server
docker-compose logs -f spacy-enhancer
```

## Monitoring and Alerting

### Grafana Dashboards
Access Grafana at http://localhost:3000 (admin/admin123) for:
- Service performance metrics
- Error rates and latency
- System resource usage
- Custom correction quality metrics

### Key Metrics
- `correction_requests_total`: Total correction requests
- `correction_request_duration_seconds`: Request processing time
- `languagetool_requests_total`: LanguageTool service requests
- `spacy_processing_time_seconds`: SpaCy processing time
- `redis_cache_hits_total`: Cache performance
- `api_gateway_rate_limit_hits_total`: Rate limiting events

### Alerts
Prometheus alerts are configured for:
- High error rates (>5%)
- High latency (>2 seconds)
- Service unavailability
- High memory usage (>80%)
- Cache miss rate (>50%)

## Configuration

### Environment Variables
Key configuration options in `docker-compose.yml`:

```yaml
# API Gateway
REDIS_URL: redis://redis-cache:6379
LANGUAGETOOL_URL: http://languagetool-server:8010
SPACY_URL: http://spacy-enhancer:8020
MAX_TEXT_LENGTH: 10000
RATE_LIMIT_PER_MINUTE: 100

# LanguageTool
JAVA_OPTS: -Xmx4g -XX:+UseG1GC
LANGUAGETOOL_LANGUAGE: pt-BR

# SpaCy
SPACY_MODEL: pt_core_news_lg
LOG_LEVEL: INFO
```

### Custom Portuguese Rules
LanguageTool includes custom Brazilian Portuguese rules in:
- `services/languagetool/rules/custom-portuguese.xml`
- `services/languagetool/userdict/portuguese.txt`

### Rate Limiting
NGINX is configured with rate limiting:
- 10 requests per second per IP
- Burst capacity of 20 requests
- 503 status for exceeded limits

## Performance Tuning

### Recommended Settings

**For High Traffic (1000+ req/min):**
```yaml
# Increase LanguageTool heap
JAVA_OPTS: -Xmx6g -XX:+UseG1GC -XX:MaxGCPauseMillis=200

# Scale services
replicas:
  api-gateway: 3
  spacy-enhancer: 2

# Increase rate limits
rate_limit: 200/minute
```

**For Low Latency (<500ms):**
```yaml
# Enable parallel processing
ENABLE_PARALLEL_PROCESSING: true

# Optimize cache
REDIS_TTL: 3600
CACHE_MAX_SIZE: 10000

# Tune LanguageTool
LT_TIMEOUT: 5000
LT_MAX_TEXT_LENGTH: 5000
```

## Scaling

### Horizontal Scaling
```bash
# Scale API Gateway
docker-compose up -d --scale api-gateway=3

# Scale SpaCy service
docker-compose up -d --scale spacy-enhancer=2
```

### Load Balancing
NGINX automatically load balances between service replicas using round-robin.

### Database Scaling
For production deployments, consider:
- External Redis cluster
- Persistent volume for custom dictionaries
- External metrics storage (Prometheus remote write)

## Security

### SSL/TLS
NGINX is configured for SSL termination:
```nginx
# Place certificates in configs/nginx/ssl/
ssl_certificate /etc/nginx/ssl/cert.pem;
ssl_certificate_key /etc/nginx/ssl/key.pem;
```

### API Security
- Rate limiting per IP
- Request size limits (10MB)
- CORS protection
- Health check endpoints

### Network Security
- Internal Docker network isolation
- Service-to-service communication on private network
- External access only through NGINX proxy

## Troubleshooting

### Common Issues

**Services not starting:**
```bash
# Check logs
docker-compose logs

# Verify resources
docker system df
free -h

# Clean and redeploy
./scripts/deploy.sh clean
./scripts/deploy.sh deploy
```

**High memory usage:**
```bash
# Check container stats
docker stats

# Reduce LanguageTool heap
# Edit docker-compose.yml: JAVA_OPTS: -Xmx2g
```

**Slow responses:**
```bash
# Check service health
./scripts/health-check.sh

# Monitor metrics
curl http://localhost:8000/metrics

# Check cache performance
redis-cli -h localhost -p 6379 info stats
```

### Log Analysis
```bash
# API Gateway errors
docker-compose logs api-gateway | grep ERROR

# LanguageTool performance
docker-compose logs languagetool-server | grep -E "(took|ms)"

# SpaCy processing issues
docker-compose logs spacy-enhancer | grep -E "(error|exception)"
```

## Development

### Local Development
```bash
# Start only core services
docker-compose up api-gateway languagetool-server spacy-enhancer redis-cache

# Run API Gateway locally
cd services/api-gateway
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Adding Custom Rules
1. Edit `services/languagetool/rules/custom-portuguese.xml`
2. Rebuild LanguageTool service:
```bash
docker-compose build languagetool-server
docker-compose up -d languagetool-server
```

### Testing
```bash
# Run health checks
./scripts/health-check.sh

# Load testing
apt install apache2-utils
ab -n 1000 -c 10 -T 'application/json' -p test-payload.json http://localhost:8000/correct
```

## Production Deployment

### VM Requirements
- **Minimum**: 4 vCPUs, 8GB RAM, 50GB SSD
- **Recommended**: 8 vCPUs, 16GB RAM, 100GB SSD
- **High Load**: 16 vCPUs, 32GB RAM, 200GB SSD

### System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Configure system limits
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
```

### Backup and Recovery
```bash
# Backup configuration
tar -czf backup-$(date +%Y%m%d).tar.gz services/ configs/ docker-compose.yml

# Backup Redis data
docker exec redis-cache redis-cli BGSAVE

# Recovery
./scripts/deploy.sh stop
tar -xzf backup-*.tar.gz
./scripts/deploy.sh deploy
```

## Support

### Logs Location
- Application logs: `docker-compose logs [service]`
- Nginx logs: `configs/nginx/logs/`
- Prometheus data: `monitoring/prometheus/data/`
- Grafana data: `monitoring/grafana/data/`

### Performance Metrics
Monitor these key metrics in Grafana:
- Request rate and latency
- Error rate by service
- Memory and CPU usage
- Cache hit ratio
- Queue lengths

### Getting Help
1. Check health status: `./scripts/health-check.sh`
2. Review logs for errors: `docker-compose logs`
3. Verify configuration: `docker-compose config`
4. Monitor metrics in Grafana: http://localhost:3000
