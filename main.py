from fastapi import FastAPI, HTTPException
from models import load_model, correct_text
from utils import preprocess_text, postprocess_text
import torch
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="BERTimbau Corrector API",
    description="API para correção gramatical usando BERTimbau",
    version="1.0.0"
)

# Carrega o modelo ao iniciar
@app.on_event("startup")
async def startup_event():
    try:
        app.state.model, app.state.tokenizer = load_model()
        logging.info("Modelo carregado com sucesso!")
    except Exception as e:
        logging.error(f"Erro ao carregar modelo: {str(e)}")
        raise RuntimeError("Falha na inicialização do modelo")

@app.get("/health")
async def health_check():
    """Endpoint para verificar se a API está funcionando"""
    return {"status": "healthy", "message": "API está funcionando corretamente"}

@app.post("/corrigir")
async def corrigir_texto(request: dict):
    try:
        text = request.get("text", "")
        threshold = request.get("threshold", 0.3)
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="Texto vazio fornecido")
        
        # Preprocessa o texto
        processed_text = preprocess_text(text)
        
        # Corrige o texto
        resultado = correct_text(
            model=app.state.model,
            tokenizer=app.state.tokenizer,
            text=processed_text,
            threshold=threshold
        )
        
        # Pós-processa o resultado
        resultado = postprocess_text(resultado)
        
        return {
            "original": text,
            "corrigido": resultado,
            "modelo": "neuralmind/bert-base-portuguese-cased"
        }
    except Exception as e:
        logging.error(f"Erro na correção: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno no processamento")