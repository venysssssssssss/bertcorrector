# Como Testar se a Correção está Funcionando

Este guia explica como verificar se o BERTCorrector está funcionando corretamente após as correções aplicadas.

## 🚀 Método 1: Deploy Automatizado (Recomendado)

Execute o script de deploy que automatiza todo o processo:

```bash
./deploy.sh
```

Este script irá:
1. Parar e remover containers existentes
2. Rebuildar a imagem com as correções
3. Iniciar novo container
4. Aguardar a API ficar disponível
5. Executar testes automatizados
6. Mostrar exemplos de uso

## 🧪 Método 2: Testes Manuais Passo a Passo

### 1. Reconstruir e Executar o Container

```bash
# Pare o container existente
docker stop corretor-api
docker rm corretor-api

# Rebuilde com as correções
docker build -t bert-corrector .

# Execute o novo container
docker run -d --gpus all -p 8080:8000 --name corretor-api bert-corrector
```

### 2. Verificar Logs de Inicialização

```bash
# Monitore os logs até ver "Application startup complete"
docker logs -f corretor-api
```

**⚠️ Importante**: Aguarde até ver a mensagem "Application startup complete" antes de testar.

### 3. Testar Health Check

```bash
curl -X GET "http://localhost:8080/health"
```

**Resposta esperada**:
```json
{
  "status": "healthy", 
  "message": "API está funcionando corretamente"
}
```

### 4. Testar Correções

#### Teste Básico:
```bash
curl -X POST "http://localhost:8080/corrigir" \
  -H "Content-Type: application/json" \
  -d '{"text": "eu gosta de comer bolo"}'
```

**Resposta esperada**:
```json
{
  "original": "eu gosta de comer bolo",
  "corrigido": "eu gosto de comer bolo",
  "modelo": "neuralmind/bert-base-portuguese-cased"
}
```

#### Mais Testes:
```bash
# Teste com múltiplas correções
curl -X POST "http://localhost:8080/corrigir" \
  -H "Content-Type: application/json" \
  -d '{"text": "nos fomos ao cinema ontem a noite"}'

# Teste com threshold personalizado
curl -X POST "http://localhost:8080/corrigir" \
  -H "Content-Type: application/json" \
  -d '{"text": "voce esta bem", "threshold": 0.2}'
```

## 🤖 Método 3: Testes Automatizados

Execute o script de testes que verifica múltiplos casos:

```bash
python3 test_corrections.py
```

Este script testa:
- Conectividade da API
- Casos de correção comuns
- Casos extremos
- Performance básica

## 🔬 Método 4: Teste Local (Sem Docker)

Para debug local sem usar Docker:

```bash
python3 test_local.py
```

Este script:
- Verifica dependências
- Testa o modelo localmente
- Não requer Docker

## ✅ Sinais de que está Funcionando

### 1. **Logs Saudáveis**
```
INFO:     Application startup complete.
Modelo carregado com sucesso!
```

### 2. **Health Check OK**
```json
{"status": "healthy", "message": "API está funcionando corretamente"}
```

### 3. **Correções Aplicadas**
- `"eu gosta"` → `"eu gosto"`
- `"nos fomos"` → `"nós fomos"`
- `"dous filhos"` → `"dois filhos"`

### 4. **Sem Erros NumPy**
Não deve aparecer:
```
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.2.6
```

## ❌ Problemas Comuns e Soluções

### API não responde
```bash
# Verifique se o container está rodando
docker ps

# Verifique logs para erros
docker logs corretor-api
```

### Erro NumPy
- **Solução**: As correções já fixaram isso com NumPy 1.24.4

### Correções estranhas
- **Causa**: Modelo ainda carregando
- **Solução**: Aguarde "Application startup complete" nos logs

### Timeout
```bash
# Aumente o timeout ou aguarde mais tempo
# O modelo pode demorar para carregar na primeira vez
```

## 📊 Métricas de Sucesso

Um sistema funcionando deve ter:
- ✅ Health check respondendo
- ✅ Pelo menos 70% dos testes passando
- ✅ Correções sensatas (não quebrando palavras)
- ✅ Tempo de resposta < 10 segundos
- ✅ Sem erros de dependência nos logs

## 🔧 Debug Avançado

### Verificar GPU
```bash
docker exec -it corretor-api nvidia-smi
```

### Logs detalhados
```bash
docker logs corretor-api --tail 50
```

### Testar manualmente dentro do container
```bash
docker exec -it corretor-api python3 -c "from models import load_model; print('OK')"
```

## 🚨 Em Caso de Problemas

1. **Verifique os logs**: `docker logs corretor-api`
2. **Execute os testes**: `python3 test_corrections.py`
3. **Teste local**: `python3 test_local.py`
4. **Reconstrua**: `./deploy.sh`

## 📝 Exemplos de Entrada/Saída

| Entrada | Saída Esperada | Status |
|---------|----------------|---------|
| `"eu gosta de bolo"` | `"eu gosto de bolo"` | ✅ Correção |
| `"ela tem dous filhos"` | `"ela tem dois filhos"` | ✅ Correção |
| `"o texto está correto"` | `"o texto está correto"` | ✅ Sem mudança |
| `""` | `""` | ✅ Texto vazio |

---

**💡 Dica**: Use o `deploy.sh` para deploy completo e automatizado!
