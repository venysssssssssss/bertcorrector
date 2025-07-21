from transformers import BertForMaskedLM, AutoTokenizer
import torch
import re
import logging
from difflib import SequenceMatcher
from corrections_dict import get_direct_correction, get_word_correction, should_preserve_word

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

def similarity(a, b):
    """Calcula similaridade entre duas strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def correct_text(model, tokenizer, text, threshold=0.2):
    """
    Correção híbrida: dicionário + BERT de forma conservadora
    """
    # Preprocessamento
    original_text = text
    text = text.strip()
    if not text:
        return text
    
    logger.info(f"Corrigindo: '{text}'")
    
    # Primeira passada: correções diretas do dicionário
    direct_correction = get_direct_correction(text)
    if direct_correction:
        logger.info(f"Correção direta encontrada: '{text}' -> '{direct_correction}'")
        return direct_correction
    
    # Segunda passada: palavra por palavra
    words = text.split()
    corrected_words = []
    
    for i, word in enumerate(words):
        # Separa pontuação
        punctuation = ""
        clean_word = word
        
        # Extrai pontuação do final
        while clean_word and clean_word[-1] in ".,!?;:\"'":
            punctuation = clean_word[-1] + punctuation
            clean_word = clean_word[:-1]
        
        # Preserva palavras que não devem ser alteradas
        if should_preserve_word(clean_word):
            corrected_words.append(word)
            continue
        
        # Verifica correção direta da palavra
        direct_word_correction = get_word_correction(clean_word)
        if direct_word_correction:
            corrected_words.append(direct_word_correction + punctuation)
            logger.info(f"Correção de palavra: '{clean_word}' -> '{direct_word_correction}'")
            continue
        
        # Se não encontrou correção direta, usa BERT de forma muito conservadora
        if len(clean_word) >= 3 and clean_word.isalpha():
            bert_correction = correct_word_with_bert(
                model, tokenizer, clean_word, words, i, threshold
            )
            corrected_words.append(bert_correction + punctuation)
        else:
            corrected_words.append(word)
    
    result = " ".join(corrected_words)
    
    # Pós-processamento mínimo
    result = re.sub(r'\s+([,.!?;:])', r'\1', result)
    result = re.sub(r'\s+', ' ', result)
    result = result.strip()
    
    # Log da correção final
    if result != original_text:
        logger.info(f"Correção final: '{original_text}' -> '{result}'")
    else:
        logger.info("Nenhuma correção aplicada")
    
    return result

def correct_word_with_bert(model, tokenizer, word, words, word_index, threshold):
    """
    Usa BERT apenas para correções muito conservadoras
    """
    # Contexto limitado para não alterar significado
    context_size = 1  # Apenas 1 palavra de cada lado
    
    context_before = ""
    context_after = ""
    
    if word_index > 0:
        context_before = words[word_index - 1]
        # Remove pontuação do contexto
        context_before = re.sub(r'[^\w\s]', '', context_before).strip()
    
    if word_index < len(words) - 1:
        context_after = words[word_index + 1]
        # Remove pontuação do contexto
        context_after = re.sub(r'[^\w\s]', '', context_after).strip()
    
    # Cria contexto simples
    if context_before and context_after:
        context = f"{context_before} [MASK] {context_after}"
    elif context_before:
        context = f"{context_before} [MASK]"
    elif context_after:
        context = f"[MASK] {context_after}"
    else:
        # Sem contexto suficiente, não corrige
        return word
    
    # Tokeniza
    inputs = tokenizer(context, return_tensors="pt", padding=True, truncation=True).to(device)
    
    # Encontra posição do MASK
    mask_token_id = tokenizer.mask_token_id
    mask_positions = (inputs["input_ids"] == mask_token_id).nonzero(as_tuple=True)
    
    if len(mask_positions[1]) == 0:
        return word
    
    mask_pos = mask_positions[1][0].item()
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits[0, mask_pos]
        probabilities = torch.softmax(logits, dim=-1)
        
        # Probabilidade da palavra original
        original_tokens = tokenizer.encode(word, add_special_tokens=False)
        if not original_tokens:
            return word
            
        original_token_id = original_tokens[0]
        original_prob = probabilities[original_token_id].item()
        
        # Threshold muito alto para ser conservador
        if original_prob > threshold:
            return word
        
        # Procura apenas candidatos muito similares
        top_k = torch.topk(probabilities, k=5)  # Menos candidatos
        
        for prob, token_id in zip(top_k.values, top_k.indices):
            candidate = tokenizer.decode([token_id]).strip()
            
            # Filtros muito rigorosos
            if (candidate and 
                candidate.isalpha() and 
                len(candidate) >= 2 and
                candidate.lower() != word.lower() and
                similarity(word, candidate) > 0.7 and  # 70% similaridade mínima
                abs(len(word) - len(candidate)) <= 2 and  # Diferença máxima de 2 caracteres
                prob.item() > original_prob * 2):  # Deve ser MUITO melhor
                
                logger.info(f"Correção BERT conservadora: '{word}' -> '{candidate}' (sim: {similarity(word, candidate):.2f})")
                return candidate
        
        return word