#!/bin/bash

echo "🔄 Teste Rápido das Melhorias de Correção"
echo "========================================="

# Para container atual
echo "Parando container anterior..."
docker stop corretor-api 2>/dev/null || true
docker rm corretor-api 2>/dev/null || true

# Rebuild
echo "Rebuilding com melhorias..."
docker build -t bert-corrector . -q

# Inicia novo container
echo "Iniciando container..."
docker run -d --gpus all -p 8080:8000 --name corretor-api bert-corrector

# Aguarda inicialização
echo "Aguardando inicialização (30s)..."
sleep 30

# Testes específicos
echo ""
echo "🧪 TESTANDO CORREÇÕES MELHORADAS"
echo "================================"

echo ""
echo "Teste 1: Concordância verbal"
echo "Entrada: 'eu gosta de comer bolo'"
curl -s -X POST "http://localhost:8080/corrigir" \
  -H "Content-Type: application/json" \
  -d '{"text": "eu gosta de comer bolo"}' | jq -r '.corrigido'

echo ""
echo "Teste 2: Ortografia simples"  
echo "Entrada: 'ela tem dous filhos'"
curl -s -X POST "http://localhost:8080/corrigir" \
  -H "Content-Type: application/json" \
  -d '{"text": "ela tem dous filhos"}' | jq -r '.corrigido'

echo ""
echo "Teste 3: Acentuação"
echo "Entrada: 'nos fomos ao cinema'"
curl -s -X POST "http://localhost:8080/corrigir" \
  -H "Content-Type: application/json" \
  -d '{"text": "nos fomos ao cinema"}' | jq -r '.corrigido'

echo ""
echo "Teste 4: Texto já correto (não deve alterar)"
echo "Entrada: 'a casa é muito bonita'"
curl -s -X POST "http://localhost:8080/corrigir" \
  -H "Content-Type: application/json" \
  -d '{"text": "a casa é muito bonita"}' | jq -r '.corrigido'

echo ""
echo "Teste 5: Nome próprio (deve preservar)"
echo "Entrada: 'João foi ao medico'"
curl -s -X POST "http://localhost:8080/corrigir" \
  -H "Content-Type: application/json" \
  -d '{"text": "João foi ao medico"}' | jq -r '.corrigido'

echo ""
echo "✅ Testes concluídos!"
echo ""
echo "💡 Para testes detalhados, execute:"
echo "   python3 test_corrections.py"
