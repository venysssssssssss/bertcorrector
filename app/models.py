from transformers import BertForMaskedLM, BertTokenizer
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def load_model():
    model_name = "neuralmind/bert-base-portuguese-cased"
    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertForMaskedLM.from_pretrained(model_name).to(device)
    return model, tokenizer

def correct_text(model, tokenizer, text, threshold=0.3):
    # Tokenização e preparação de máscaras
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(device)
    input_ids = inputs["input_ids"]
    
    # Identifica palavras provavelmente erradas
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
    
    # Gera correções
    corrected_tokens = []
    for i, token_id in enumerate(input_ids[0]):
        token = tokenizer.convert_ids_to_tokens([token_id])[0]
        
        if token == "[CLS]" or token == "[SEP]":
            continue
        
        # Calcula probabilidade do token original
        token_prob = torch.softmax(logits[0, i], dim=-1)[token_id].item()
        
        if token_prob < threshold:
            # Encontra melhores alternativas
            top_candidates = torch.topk(logits[0, i], k=5)
            candidates = []
            for idx in top_candidates.indices:
                candidate = tokenizer.convert_ids_to_tokens([idx])[0]
                if candidate not in ["[CLS]", "[SEP]", "[PAD]", "[UNK]"]:
                    candidates.append(candidate.replace("##", ""))
            
            corrected_tokens.append(candidates[0] if candidates else token)
        else:
            corrected_tokens.append(token.replace("##", ""))
    
    return " ".join(corrected_tokens).replace(" .", ".").replace(" ,", ",")