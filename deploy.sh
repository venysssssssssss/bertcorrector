#!/bin/bash

# Script para facilitar deployment e testes do BERTCorrector

set -e  # Para em caso de erro

echo "🚀 BERTCorrector - Deploy e Teste Automatizado"
echo "=============================================="

# Função para logs coloridos
log_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

log_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

log_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

# Verifica se está no diretório correto
if [ ! -f "Dockerfile" ]; then
    log_error "Dockerfile não encontrado. Execute este script no diretório do projeto."
    exit 1
fi

# Para e remove container existente
log_info "Parando e removendo container existente..."
docker stop corretor-api 2>/dev/null || true
docker rm corretor-api 2>/dev/null || true

# Rebuild da imagem
log_info "Rebuilding imagem Docker..."
if docker build -t bert-corrector .; then
    log_success "Imagem construída com sucesso!"
else
    log_error "Falha na construção da imagem"
    exit 1
fi

# Inicia novo container
log_info "Iniciando novo container..."
if docker run -d --gpus all -p 8080:8000 --name corretor-api bert-corrector; then
    log_success "Container iniciado!"
else
    log_error "Falha ao iniciar container"
    exit 1
fi

# Aguarda inicialização
log_info "Aguardando inicialização..."
sleep 5

# Monitora logs por 30 segundos ou até ver "startup complete"
log_info "Monitorando logs de inicialização..."
timeout 30 docker logs -f corretor-api &
LOGS_PID=$!

# Aguarda até a API estar pronta
MAX_ATTEMPTS=15
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        kill $LOGS_PID 2>/dev/null || true
        log_success "API está funcionando!"
        break
    fi
    
    log_info "Tentativa $ATTEMPT/$MAX_ATTEMPTS - aguardando API..."
    sleep 2
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
    log_error "API não respondeu dentro do tempo limite"
    log_info "Verificando logs do container:"
    docker logs corretor-api --tail 20
    exit 1
fi

# Executa testes
log_info "Executando testes automatizados..."
if python3 test_corrections.py; then
    log_success "Todos os testes passaram!"
else
    log_warning "Alguns testes falharam. Verifique os logs acima."
fi

# Testes manuais rápidos
log_info "Executando testes manuais..."

echo ""
echo "🧪 Teste 1: Health Check"
curl -s http://localhost:8080/health | python3 -m json.tool

echo ""
echo "🧪 Teste 2: Correção simples"
curl -s -X POST "http://localhost:8080/corrigir" \
  -H "Content-Type: application/json" \
  -d '{"text": "eu gosta de comer bolo"}' | python3 -m json.tool

echo ""
echo "🧪 Teste 3: Múltiplas correções"
curl -s -X POST "http://localhost:8080/corrigir" \
  -H "Content-Type: application/json" \
  -d '{"text": "nos fomos ao cinema ontem a noite"}' | python3 -m json.tool

echo ""
log_success "Deploy concluído com sucesso!"
echo ""
echo "📋 Próximos passos:"
echo "   • API rodando em: http://localhost:8080"
echo "   • Health check: curl http://localhost:8080/health"
echo "   • Logs: docker logs -f corretor-api"
echo "   • Parar: docker stop corretor-api"
echo ""
echo "📖 Exemplos de uso:"
echo '   curl -X POST "http://localhost:8080/corrigir" \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"text": "seu texto aqui"}'"'"
