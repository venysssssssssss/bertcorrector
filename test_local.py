#!/usr/bin/env python3
"""
Script para testar as correções localmente (sem Docker)
"""

import os
import sys
import torch

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_local_correction():
    """Testa o sistema de correção localmente"""
    try:
        from models import load_model, correct_text
        from utils import preprocess_text, postprocess_text
        
        print("🔄 Carregando modelo...")
        model, tokenizer = load_model()
        print("✅ Modelo carregado com sucesso!")
        
        # Casos de teste
        test_cases = [
            "eu gosta de comer bolo",
            "ela tem dous filhos", 
            "nos fomos ao cinema",
            "o menino correu muito rapido",
            "voce esta bem",
            "nos vamos para casa amanha"
        ]
        
        print("\n" + "="*50)
        print("🧪 TESTANDO CORREÇÕES LOCALMENTE")
        print("="*50)
        
        for i, text in enumerate(test_cases, 1):
            print(f"\n📝 Teste {i}:")
            print(f"Original: '{text}'")
            
            # Preprocessa
            processed = preprocess_text(text)
            
            # Corrige
            corrected = correct_text(model, tokenizer, processed, threshold=0.3)
            
            # Pós-processa
            final = postprocess_text(corrected)
            
            print(f"Corrigido: '{final}'")
            
            if text != final:
                print("✅ Correção aplicada")
            else:
                print("ℹ️  Nenhuma correção necessária")
                
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("Verifique se todas as dependências estão instaladas")
    except Exception as e:
        print(f"❌ Erro: {e}")

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    print("🔍 Verificando dependências...")
    
    deps = [
        ("torch", "PyTorch"),
        ("transformers", "Transformers"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("numpy", "NumPy"),
        ("scipy", "SciPy")
    ]
    
    missing = []
    
    for dep, name in deps:
        try:
            __import__(dep)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - FALTANDO")
            missing.append(name)
    
    if missing:
        print(f"\n⚠️  Dependências faltando: {', '.join(missing)}")
        print("Execute: pip install transformers torch fastapi uvicorn scipy numpy")
        return False
    
    print("\n✅ Todas as dependências estão instaladas!")
    return True

def check_gpu():
    """Verifica disponibilidade de GPU"""
    print("\n🔍 Verificando GPU...")
    
    if torch.cuda.is_available():
        gpu_count = torch.cuda.device_count()
        current_device = torch.cuda.current_device()
        gpu_name = torch.cuda.get_device_name(current_device)
        
        print(f"✅ GPU disponível: {gpu_name}")
        print(f"   Dispositivos: {gpu_count}")
        print(f"   Memória: {torch.cuda.get_device_properties(current_device).total_memory / 1e9:.1f} GB")
    else:
        print("⚠️  GPU não disponível - usando CPU")

if __name__ == "__main__":
    print("🚀 TESTE LOCAL DO BERTCORRECTOR")
    print("=" * 50)
    
    # Verifica dependências
    if not check_dependencies():
        sys.exit(1)
    
    # Verifica GPU
    check_gpu()
    
    # Executa testes
    test_local_correction()
