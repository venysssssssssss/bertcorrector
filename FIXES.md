# BERTimbau Corrector - Correções Aplicadas

## Problemas Corrigidos

### 1. Conflito de Versão NumPy
- **Problema**: Incompatibilidade entre NumPy 1.x e 2.x causando crash na inicialização
- **Solução**: Fixado NumPy em versão < 2.0 no Dockerfile e pyproject.toml

### 2. API Depreciada
- **Problema**: Uso de `BertTokenizer` que está obsoleto
- **Solução**: Migrado para `AutoTokenizer` que é a API recomendada

### 3. Lógica de Correção Inadequada
- **Problema**: Tokenização estava quebrando palavras incorretamente
- **Solução**: Reescrita completa da lógica para processar palavras inteiras

### 4. Tratamento de Pontuação
- **Problema**: Espaços incorretos ao redor de pontuação
- **Solução**: Adicionado pós-processamento para corrigir espaçamento

## Como Rebuildar e Testar

### 1. Pare e remova o container existente
```bash
docker stop corretor-api
docker rm corretor-api
```

### 2. Rebuilde a imagem
```bash
docker build -t bert-corrector .
```

### 3. Execute o novo container
```bash
docker run -d --gpus all -p 8080:8000 --name corretor-api bert-corrector
```

### 4. Aguarde a inicialização
```bash
# Monitore os logs até ver "Application startup complete"
docker logs -f corretor-api
```

### 5. Teste a API
```bash
# Teste de saúde
curl -X GET "http://localhost:8080/health"

# Teste de correção
curl -X POST "http://localhost:8080/corrigir" \
  -H "Content-Type: application/json" \
  -d '{"text": "eu gosta de comer bolo"}'
```

### 6. Execute o script de teste automatizado
```bash
python3 test_corrections.py
```

## Melhorias Implementadas

1. **Endpoint de Health Check**: `/health` para monitoramento
2. **Melhor Tratamento de Erros**: Logs mais detalhados
3. **Preprocessamento**: Normalização de texto antes da correção
4. **Pós-processamento**: Correção de espaçamento após a correção
5. **Lógica de Correção Melhorada**: Preserva estrutura das palavras

## Parâmetros da API

### POST /corrigir
```json
{
  "text": "texto para corrigir",
  "threshold": 0.3  // opcional, padrão 0.3
}
```

- **threshold**: Controla a sensibilidade da correção (0.1-0.9)
  - Valores menores = mais correções
  - Valores maiores = correções mais conservadoras

## Exemplo de Uso

```bash
curl -X POST "http://localhost:8080/corrigir" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "nos fomos ao cinema ontem a noite",
    "threshold": 0.3
  }'
```

Resposta esperada:
```json
{
  "original": "nos fomos ao cinema ontem a noite",
  "corrigido": "nós fomos ao cinema ontem à noite",
  "modelo": "neuralmind/bert-base-portuguese-cased"
}
```
