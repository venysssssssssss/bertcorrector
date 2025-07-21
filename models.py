from transformers import BertForMaskedLM, AutoTokenizer
import torch
import re
import logging
from difflib import SequenceMatcher

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Dicionário de correções comuns integrado
COMMON_CORRECTIONS = {
    # Concordância verbal - frases completas
    'eu gosta': 'eu gosto',
    'tu gosta': 'tu gostas',
    'nos fomos': 'nós fomos',
    'nos temos': 'nós temos',
    'voces tem': 'vocês têm',
    
    # Concordância verbal - palavras individuais
    'gosta': 'gosto',  # quando usado com "eu"
    
    # Ortografia comum
    'dous': 'dois',
    'tres': 'três', 
    'voce': 'você',
    'esta': 'está',
    'rapido': 'rápido',
    'facil': 'fácil',
    'util': 'útil',
    'otimo': 'ótimo',
    'musica': 'música',
    'medico': 'médico',
    'publico': 'público',
    'pratico': 'prático',
    'critica': 'crítica',
    'matematica': 'matemática',
    'amanha': 'amanhã',
    'arvore': 'árvore',
    'numero': 'número',
    'pagina': 'página',
    'rapida': 'rápida',
    'ultima': 'última',
    'proximo': 'próximo',
    'basico': 'básico',
    'grafico': 'gráfico',
    'fantastico': 'fantástico',
    'automatico': 'automático',
    'economico': 'econômico',
    'academico': 'acadêmico',
}

# Palavras que devem ser preservadas
PRESERVE_WORDS = {
    'casa', 'carro', 'amor', 'vida', 'tempo', 'pessoa', 'mundo', 'mão', 'dia',
    'noite', 'sol', 'lua', 'água', 'fogo', 'terra', 'ar', 'homem', 'mulher',
    'criança', 'família', 'amigo', 'trabalho', 'escola', 'livro', 'filme',
    'música', 'comida', 'cidade', 'país', 'brasil', 'português', 'inglês',
    'joão', 'maria', 'pedro', 'ana', 'carlos', 'josé', 'antonio', 'francisco',
    'muito', 'bem', 'bom', 'boa', 'grande', 'pequeno', 'novo', 'velho'
}

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

def should_preserve_word(word):
    """Verifica se uma palavra deve ser preservada"""
    word_lower = word.lower()
    
    # Preserva nomes próprios
    if word[0].isupper() and len(word) > 1:
        return True
    
    # Preserva palavras muito curtas
    if len(word) <= 2:
        return True
    
    # Preserva palavras corretas conhecidas
    if word_lower in PRESERVE_WORDS:
        return True
    
    # Preserva números
    if word.isdigit():
        return True
    
    return False

def get_direct_correction(phrase):
    """Busca correção direta no dicionário"""
    phrase_lower = phrase.lower().strip()
    return COMMON_CORRECTIONS.get(phrase_lower)

def get_word_correction(word, context_before=""):
    """Busca correção para palavra individual considerando contexto"""
    word_lower = word.lower().strip()
    
    # Correções diretas
    direct_correction = COMMON_CORRECTIONS.get(word_lower)
    if direct_correction:
        return direct_correction
    
    # Correções contextuais específicas
    context_lower = context_before.lower().strip()
    
    # "eu gosta" -> "eu gosto"
    if word_lower == 'gosta' and context_lower.endswith('eu'):
        return 'gosto'
    
    # "nos" -> "nós" (pronome, não preposição)
    if word_lower == 'nos' and (not context_lower or context_lower.split()[-1] not in ['de', 'da', 'do', 'das', 'dos']):
        return 'nós'
    
    return None

def correct_text(model, tokenizer, text, threshold=0.2):
    """
    Correção híbrida: dicionário + BERT de forma muito conservadora
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
        
        # Verifica correção direta da palavra com contexto
        context_before = " ".join(words[:i]) if i > 0 else ""
        direct_word_correction = get_word_correction(clean_word, context_before)
        if direct_word_correction:
            corrected_words.append(direct_word_correction + punctuation)
            logger.info(f"Correção de palavra: '{clean_word}' -> '{direct_word_correction}'")
            continue
        
        # Para outras palavras, mantém original (BERT muito conservador)
        # Apenas aplica BERT se a palavra parece ter erro óbvio
        if len(clean_word) >= 4 and clean_word.isalpha():
            # Verifica se tem características de erro (falta de acentos em palavras longas)
            if any(char in clean_word.lower() for char in ['a', 'e', 'i', 'o', 'u']) and len(clean_word) > 5:
                bert_correction = correct_word_with_bert_conservative(
                    model, tokenizer, clean_word, words, i, threshold
                )
                corrected_words.append(bert_correction + punctuation)
            else:
                corrected_words.append(word)
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
        logger.info("Nenhuma correção aplicada - texto mantido")
    
    return result

def correct_word_with_bert_conservative(model, tokenizer, word, words, word_index, threshold):
    """
    Usa BERT apenas para correções extremamente conservadoras
    """
    # Só aplica se tem contexto
    if word_index == 0 and len(words) == 1:
        return word
    
    # Contexto mínimo
    context_before = words[word_index - 1] if word_index > 0 else ""
    context_after = words[word_index + 1] if word_index < len(words) - 1 else ""
    
    # Remove pontuação do contexto
    context_before = re.sub(r'[^\w\s]', '', context_before).strip()
    context_after = re.sub(r'[^\w\s]', '', context_after).strip()
    
    # Sem contexto suficiente, não corrige
    if not context_before and not context_after:
        return word
    
    # Cria contexto
    if context_before and context_after:
        context = f"{context_before} [MASK] {context_after}"
    elif context_before:
        context = f"{context_before} [MASK]"
    elif context_after:
        context = f"[MASK] {context_after}"
    else:
        return word
    
    try:
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
            
            # Threshold extremamente alto para ser ultra-conservador
            if original_prob > 0.1:  # Se tem pelo menos 10% de probabilidade, mantém
                return word
            
            # Procura apenas o melhor candidato muito similar
            top_k = torch.topk(probabilities, k=3)
            
            for prob, token_id in zip(top_k.values, top_k.indices):
                candidate = tokenizer.decode([token_id]).strip()
                
                # Filtros ultra-rigorosos
                if (candidate and 
                    candidate.isalpha() and 
                    len(candidate) >= 2 and
                    candidate.lower() != word.lower() and
                    similarity(word, candidate) > 0.8 and  # 80% similaridade mínima
                    abs(len(word) - len(candidate)) <= 1 and  # Diferença máxima de 1 caractere
                    prob.item() > original_prob * 3):  # Deve ser 3x melhor
                    
                    logger.info(f"Correção BERT ultra-conservadora: '{word}' -> '{candidate}' (sim: {similarity(word, candidate):.2f})")
                    return candidate
            
            return word
            
    except Exception as e:
        logger.error(f"Erro no BERT para palavra '{word}': {e}")
        return word