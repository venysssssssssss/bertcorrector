import re

def preprocess_text(text):
    """Normaliza texto antes da correção"""
    text = re.sub(r'\s+', ' ', text)  # Remove espaços múltiplos
    text = text.replace('"', "'")     # Uniformiza aspas
    return text.strip()

def postprocess_text(text):
    """Ajusta texto após correção"""
    # Corrige espaçamento de pontuação
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    # Corrige espaços múltiplos
    text = re.sub(r'\s+', ' ', text)
    return text.strip()