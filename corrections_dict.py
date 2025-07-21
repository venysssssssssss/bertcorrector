"""
Módulo de correções específicas para português brasileiro
"""

# Dicionário de correções comuns e específicas
COMMON_CORRECTIONS = {
    # Concordância verbal
    'eu gosta': 'eu gosto',
    'eu tinha': 'eu tinha',  # já correto
    'tu gosta': 'tu gostas',
    'nos fomos': 'nós fomos',
    'nos temos': 'nós temos',
    'voces tem': 'vocês têm',
    
    # Ortografia comum
    'dous': 'dois',
    'tres': 'três', 
    'voce': 'você',
    'esta': 'está',  # contexto-dependente
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
    
    # Preposições e artigos
    'no arvore': 'na árvore',
    'na problema': 'no problema',
    'um agua': 'uma água',
    'uma problema': 'um problema',
    
    # Palavras específicas
    'vc': 'você',
    'pq': 'por que',
    'tbm': 'também',
    'hj': 'hoje',
    'ontem': 'ontem',  # já correto
}

# Padrões que NÃO devem ser alterados
PRESERVE_PATTERNS = [
    # Nomes próprios (começam com maiúscula)
    r'^[A-Z][a-z]+$',
    # Siglas
    r'^[A-Z]{2,}$',
    # Números
    r'^\d+$',
    # URLs/emails
    r'@',
    r'\.com',
    r'\.br',
    # Palavras estrangeiras comuns
    r'^(smartphone|tablet|laptop|notebook|software|hardware|download|upload|email|site|online|offline)$'
]

def should_preserve_word(word):
    """Verifica se uma palavra deve ser preservada sem correção"""
    import re
    word_lower = word.lower()
    
    for pattern in PRESERVE_PATTERNS:
        if re.match(pattern, word, re.IGNORECASE):
            return True
    
    # Preserva palavras muito curtas
    if len(word) <= 2:
        return True
    
    # Preserva palavras que já estão corretas
    correct_words = {
        'casa', 'carro', 'amor', 'vida', 'tempo', 'pessoa', 'mundo', 'mão', 'dia',
        'noite', 'sol', 'lua', 'água', 'fogo', 'terra', 'ar', 'homem', 'mulher',
        'criança', 'família', 'amigo', 'trabalho', 'escola', 'livro', 'filme',
        'música', 'comida', 'cidade', 'país', 'brasil', 'português', 'inglês'
    }
    
    if word_lower in correct_words:
        return True
    
    return False

def get_direct_correction(phrase):
    """Busca correção direta no dicionário"""
    phrase_lower = phrase.lower().strip()
    
    # Verifica frases completas primeiro
    for wrong, correct in COMMON_CORRECTIONS.items():
        if phrase_lower == wrong:
            return correct
    
    return None

def get_word_correction(word):
    """Busca correção para palavra individual"""
    word_lower = word.lower().strip()
    
    for wrong, correct in COMMON_CORRECTIONS.items():
        if word_lower == wrong:
            return correct
    
    return None
