#!/usr/bin/env python3
"""
Script para testar as correções do BERTimbau Corrector
"""

import requests
import json
import time
import sys

def wait_for_api(base_url, max_attempts=30):
    """Aguarda a API ficar disponível"""
    print("Aguardando API inicializar...")
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API está pronta!")
                return True
        except:
            pass
        
        print(f"Tentativa {attempt + 1}/{max_attempts}...")
        time.sleep(2)
    
    return False

def test_api():
    """Testa a API de correção"""
    base_url = "http://localhost:8080"
    
    # Aguarda API ficar disponível
    if not wait_for_api(base_url):
        print("❌ API não respondeu dentro do tempo limite")
        return False
    
    # Teste de saúde detalhado
    try:
        response = requests.get(f"{base_url}/health")
        print(f"\n🔍 Health check: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"Response: {health_data}")
        else:
            print("⚠️  API retornou status não-OK")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar com a API: {e}")
        return False
    
    # Testes de correção
    test_cases = [
        {
            "text": "eu gosta de comer bolo",
            "description": "Concordância verbal (eu gosta -> eu gosto)",
            "expected_improvements": ["gosto"]
        },
        {
            "text": "ela tem dous filhos",
            "description": "Erro ortográfico (dous -> dois)",
            "expected_improvements": ["dois"]
        },
        {
            "text": "nos fomos ao cinema",
            "description": "Pronome sem acento (nos -> nós)",
            "expected_improvements": ["nós"]
        },
        {
            "text": "o menino correu muito rapido",
            "description": "Falta de acento (rapido -> rápido)",
            "expected_improvements": ["rápido"]
        },
        {
            "text": "voce esta bem",
            "description": "Múltiplos acentos (voce esta -> você está)",
            "expected_improvements": ["você", "está"]
        },
        {
            "text": "nos vamos para casa amanha",
            "description": "Múltiplas correções",
            "expected_improvements": ["nós", "vamos", "amanhã"]
        },
        {
            "text": "o gato subiu no arvore",
            "description": "Concordância de gênero (no arvore -> na árvore)",
            "expected_improvements": ["na", "árvore"]
        }
    ]
    
    print("\n" + "="*60)
    print("🧪 TESTANDO CORREÇÕES DO BERTCORRECTOR")
    print("="*60)
    
    successful_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Teste {i}/{total_tests}:")
        print(f"   Caso: {test_case['description']}")
        print(f"   Original: '{test_case['text']}'")
        
        try:
            # Teste com threshold padrão
            response = requests.post(
                f"{base_url}/corrigir",
                headers={"Content-Type": "application/json"},
                json={"text": test_case['text'], "threshold": 0.3},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                corrected = result['corrigido']
                print(f"   Corrigido: '{corrected}'")
                
                # Verifica se houve alguma melhoria
                if result['original'] != corrected:
                    print("   ✅ Correção aplicada")
                    
                    # Verifica se alguma das melhorias esperadas foi aplicada
                    improvements_found = []
                    for expected in test_case['expected_improvements']:
                        if expected.lower() in corrected.lower():
                            improvements_found.append(expected)
                    
                    if improvements_found:
                        print(f"   🎯 Melhorias detectadas: {', '.join(improvements_found)}")
                        successful_tests += 1
                    else:
                        print(f"   ⚠️  Correção aplicada, mas não as esperadas: {test_case['expected_improvements']}")
                else:
                    print("   ℹ️  Nenhuma correção aplicada")
                    
            else:
                print(f"   ❌ Erro HTTP: {response.status_code}")
                print(f"   Resposta: {response.text}")
                
        except requests.exceptions.Timeout:
            print("   ⏱️  Timeout na requisição")
        except Exception as e:
            print(f"   ❌ Erro na requisição: {e}")
        
        time.sleep(0.5)  # Pausa entre requests

    # Relatório final
    print("\n" + "="*60)
    print("📊 RELATÓRIO DE TESTES")
    print("="*60)
    print(f"Testes bem-sucedidos: {successful_tests}/{total_tests}")
    print(f"Taxa de sucesso: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests >= total_tests * 0.7:  # 70% de sucesso
        print("🎉 Resultado: APROVADO")
        return True
    else:
        print("❌ Resultado: REPROVADO - Muitos testes falharam")
        return False

def test_edge_cases():
    """Testa casos extremos"""
    base_url = "http://localhost:8080"
    
    print("\n" + "="*60)
    print("🔬 TESTANDO CASOS EXTREMOS")
    print("="*60)
    
    edge_cases = [
        {"text": "", "description": "Texto vazio"},
        {"text": "   ", "description": "Apenas espaços"},
        {"text": "a", "description": "Uma letra apenas"},
        {"text": "123 456", "description": "Apenas números"},
        {"text": "!@#$%", "description": "Apenas símbolos"},
        {"text": "palavra_muito_longa_que_nao_existe_no_vocabulario", "description": "Palavra muito longa"},
    ]
    
    for case in edge_cases:
        print(f"\n🧪 {case['description']}: '{case['text']}'")
        try:
            response = requests.post(
                f"{base_url}/corrigir",
                headers={"Content-Type": "application/json"},
                json={"text": case['text']},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Resposta: '{result['corrigido']}'")
            else:
                print(f"   ⚠️  Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")

if __name__ == "__main__":
    success = test_api()
    test_edge_cases()
    
    # Exit code para integração com CI/CD
    sys.exit(0 if success else 1)
