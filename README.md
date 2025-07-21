# 🚀 BertCorrector v2 - Poetry & Microservices Architecture

Sistema de correção gramatical e ortográfica baseado em LanguageTool com Poetry para gerenciamento de dependências, arquitetura de microserviços, monitoramento completo e alta disponibilidade.

## � Tecnologias

### Core Stack
- **Poetry**: Gerenciamento de dependências Python
- **LanguageTool**: Motor principal de correção gramatical
- **SpaCy**: Análise semântica e contextual
- **FastAPI**: Framework web assíncrono
- **Docker**: Containerização dos serviços

### Monitoring & DevOps
- **Prometheus**: Coleta de métricas
- **Grafana**: Dashboards e visualização
- **NGINX**: Proxy reverso e load balancer
- **Redis**: Cache de alta performance

## �🏗️ Arquitetura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   NGINX Proxy   │────│  API Gateway     │────│ Load Balancer   │
│   (SSL/Proxy)   │    │  (FastAPI)       │    │ (Multi-node)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
            ┌───────▼──┐ ┌──────▼───┐ ┌─────▼─────┐
            │LanguageTool│ │SpaCy PT-BR │ │Monitoring │
            │ (Port 8010)│ │(Port 8020) │ │(Metrics)  │
            └────────────┘ └────────────┘ └───────────┘
                    │           │           │
            ┌───────▼──┐ ┌──────▼───┐ ┌─────▼─────┐
            │Prometheus│ │  Grafana   │ │Redis Cache│
            │(Port 9090)│ │(Port 3000) │ │(Port 6379)│
            └──────────┘ └────────────┘ └───────────┘
```

## 🚀 Quick Start

### Pré-requisitos
- Python 3.12+ (< 3.14 devido ao SpaCy)
- Poetry 1.7+
- Docker & Docker Compose
- 4GB RAM mínimo

```bash
# 1. Clone e configure
git clone <repo>
cd bertcorrector

# 2. Instalar Poetry (se necessário)
curl -sSL https://install.python-poetry.org | python3 -

# 3. Instalar dependências
./scripts/poetry-deps.sh install

# 4. Deploy completo
./scripts/deploy.sh deploy

# 5. Verificar status
./scripts/health-check.sh

# 6. Acessar dashboards
# API: http://localhost:8000
# Grafana: http://localhost:3000 (admin/admin123)
# Prometheus: http://localhost:9090
```

## � Gerenciamento de Dependências com Poetry

### Comandos Principais
```bash
# Instalar todas as dependências
./scripts/poetry-deps.sh install

# Atualizar dependências
./scripts/poetry-deps.sh update

# Adicionar nova dependência
./scripts/poetry-deps.sh add api-gateway requests

# Remover dependência
./scripts/poetry-deps.sh remove spacy-enhancer numpy

# Mostrar dependências
./scripts/poetry-deps.sh show

# Exportar requirements.txt
./scripts/poetry-deps.sh export
```

### Estrutura de Dependências
- **Root Project**: Dependências de desenvolvimento (pytest, black, etc.)
- **API Gateway**: FastAPI, Redis, HTTP clients, autenticação
- **SpaCy Enhancer**: SpaCy, modelos NLP, análise semântica

## �📊 Monitoramento

### Métricas Principais
- Latência de correção (P50, P95, P99)
- Taxa de throughput (req/s)
- Taxa de erro (4xx, 5xx)
- Uso de CPU e memória
- Cache hit ratio (Redis)
- Métricas específicas do LanguageTool

### Alertas Configurados
- Alta latência (>2s)
- Taxa de erro alta (>5%)
- Uso de memória (>80%)
- Taxa de erro >5%
- Uso de CPU >80%
- Uso de memória >85%
- Serviços indisponíveis

## 🔧 Configuração

### Variáveis de Ambiente
```bash
# LanguageTool
LANGUAGETOOL_JAVA_OPTS="-Xmx4g -Xms2g"
LANGUAGETOOL_PORT=8010

# SpaCy
SPACY_MODEL=pt_core_news_lg
SPACY_PORT=8020

# Gateway
GATEWAY_PORT=8000
GATEWAY_WORKERS=4

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

## 🎛️ Escalabilidade

### Horizontal Scaling
```bash
# Escalar LanguageTool
docker service scale languagetool=3

# Escalar SpaCy
docker service scale spacy-enhancer=2

# Auto-scaling baseado em CPU
docker service update --limit-cpu 0.8 languagetool
```

### Vertical Scaling
```yaml
# docker-compose.yml
services:
  languagetool:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 8G
        reservations:
          cpus: '1.0'
          memory: 4G
```

## 🔒 Segurança

### SSL/TLS
- Certificados Let's Encrypt automáticos
- Redirect HTTP → HTTPS
- HSTS headers

### Firewall
```bash
# Permitir apenas portas necessárias
ufw allow 80,443/tcp  # HTTP/HTTPS
ufw allow 22/tcp      # SSH
ufw deny 8010,8020    # Serviços internos
```

### Rate Limiting
```nginx
# nginx.conf
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;
```

## 📈 Performance

### Benchmarks Esperados
- **Latência**: <2s (P95)
- **Throughput**: 100+ req/s
- **Disponibilidade**: 99.9%
- **Tempo de resposta**: <500ms (textos simples)

### Otimizações
- Cache de regras LanguageTool
- Pool de conexões
- Compressão gzip
- CDN para assets estáticos

## 🛠️ Desenvolvimento

### Estrutura do Projeto
```
├── services/           # Microserviços
│   ├── languagetool/   # Motor principal
│   ├── spacy-enhancer/ # Análise semântica
│   └── api-gateway/    # Orquestração
├── monitoring/         # Prometheus, Grafana
├── configs/           # Configurações
├── rules/             # Regras customizadas
├── scripts/           # Automação
└── docs/              # Documentação
```

### CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
stages:
  - test
  - build
  - security-scan
  - deploy-staging
  - deploy-production
```

## 📚 Documentação

- [🏗️ Guia de Arquitetura](docs/architecture.md)
- [🚀 Guia de Deploy](docs/deployment.md)
- [📊 Guia de Monitoramento](docs/monitoring.md)
- [🔧 Guia de Configuração](docs/configuration.md)
- [🐛 Troubleshooting](docs/troubleshooting.md)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch feature (`git checkout -b feature/amazing-feature`)
3. Commit suas mudanças (`git commit -m 'Add amazing feature'`)
4. Push para a branch (`git push origin feature/amazing-feature`)
5. Abra um Pull Request

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

**🎯 Objetivo**: Sistema de correção de classe mundial com 99.9% de uptime, latência sub-segundo e capacidade de escalar para milhões de requisições.
