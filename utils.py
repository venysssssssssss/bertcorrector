import re

def preprocess_text(text):
    """Normaliza texto antes da correção"""
    text = re.sub(r'\s+', ' ', text)  # Remove espaços múltiplos
    text = text.replace('"', "'")     # Uniformiza aspas
    return text.strip()