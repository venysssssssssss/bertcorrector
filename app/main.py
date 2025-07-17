from fastapi import FastAPI, HTTPException
from .models import load_model, correct_text
import logging

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

@app.post("/corrigir")
async def corrigir_texto(text: str, threshold: float = 0.3):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Texto vazio fornecido")
    
    try:
        resultado = correct_text(
            model=app.state.model,
            tokenizer=app.state.tokenizer,
            text=text,
            threshold=threshold
        )
        return {
            "original": text,
            "corrigido": resultado,
            "modelo": "neuralmind/bert-base-portuguese-cased"
        }
    except Exception as e:
        logging.error(f"Erro na correção: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno no processamento")

@app.get("/health")
async def health_check():
    return {"status": "online", "gpu": str(torch.cuda.is_available())}