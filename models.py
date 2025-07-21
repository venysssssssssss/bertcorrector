from transformers import BertForMaskedLM, AutoTokenizer
import torch
import re
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def load_model():
    model_name = "neuralmind/bert-base-portuguese-cased"
    logger.info(f"Carregando modelo {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = BertForMaskedLM.from_pretrained(model_name).to(device)
    logger.info("Modelo carregado com sucesso!")
    return model, tokenizer

def correct_text(model, tokenizer, text, threshold=0.3):
    """
    Corrige texto usando BERT para análise contextual de cada palavra
    """
    # Preprocessamento básico
    text = text.strip()
    if not text:
        return text
    
    # Divide em palavras preservando pontuação
    words = text.split()
    corrected_words = []
    
    for word_idx, word in enumerate(words):
        # Separa pontuação do final da palavra
        punctuation = ""
        clean_word = word
        
        # Extrai pontuação do final
        while clean_word and clean_word[-1] in ".,!?;:\"'":
            punctuation = clean_word[-1] + punctuation
            clean_word = clean_word[:-1]
        
        if not clean_word or len(clean_word) < 2:
            corrected_words.append(word)
            continue
        
        # Cria contexto para o BERT
        context_words = words.copy()
        context_words[word_idx] = "[MASK]"
        context_text = " ".join(context_words)
        
        # Tokeniza o contexto
        inputs = tokenizer(context_text, return_tensors="pt", padding=True, truncation=True).to(device)
        
        # Encontra a posição do [MASK]
        mask_token_id = tokenizer.mask_token_id
        mask_positions = (inputs["input_ids"] == mask_token_id).nonzero(as_tuple=True)
        
        if len(mask_positions[1]) == 0:
            # Se não encontrou MASK, usa a palavra original
            corrected_words.append(word)
            continue
            
        mask_pos = mask_positions[1][0].item()
        
        # Gera predições para a posição mascarada
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits[0, mask_pos]
            
            # Pega os top-k candidatos
            top_k = torch.topk(logits, k=10)
            candidates = []
            
            for score, token_id in zip(top_k.values, top_k.indices):
                candidate = tokenizer.decode([token_id]).strip()
                
                # Filtra candidatos válidos
                if (candidate and 
                    candidate.isalpha() and 
                    len(candidate) > 1 and
                    candidate.lower() != clean_word.lower()):
                    
                    candidates.append((candidate, score.item()))
            
            # Decide se deve corrigir
            if candidates:
                # Calcula score da palavra original
                original_tokens = tokenizer(clean_word, add_special_tokens=False)["input_ids"]
                if original_tokens:
                    original_score = torch.softmax(logits, dim=-1)[original_tokens[0]].item()
                    
                    # Se a palavra original tem score baixo, considera correção
                    if original_score < threshold and candidates:
                        best_candidate = candidates[0][0]
                        # Aplica a correção
                        corrected_words.append(best_candidate + punctuation)
                        logger.info(f"Correção: '{clean_word}' -> '{best_candidate}'")
                        continue
            
            # Mantém palavra original se não encontrou correção adequada
            corrected_words.append(word)
    
    result = " ".join(corrected_words)
    
    # Pós-processamento para ajustar espaçamento
    result = re.sub(r'\s+([,.!?;:])', r'\1', result)
    result = re.sub(r'\s+', ' ', result)
    
    return result.strip()