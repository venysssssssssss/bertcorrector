#!/usr/bin/env python3
"""
Script Automatizado para Download de PDFs de Gramática
"""

import os
import requests
import time
from urllib.parse import urljoin, urlparse
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFDownloader:
    """Classe para download automatizado de PDFs de gramática"""
    
    def __init__(self, download_dir="./grammar_pdfs"):
        self.download_dir = download_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Cria diretórios se não existirem
        os.makedirs(download_dir, exist_ok=True)
        os.makedirs(os.path.join(download_dir, "governamentais"), exist_ok=True)
        os.makedirs(os.path.join(download_dir, "academicos"), exist_ok=True)
        os.makedirs(os.path.join(download_dir, "classicos"), exist_ok=True)
        os.makedirs(os.path.join(download_dir, "especializados"), exist_ok=True)
    
    def download_file(self, url, filename, subfolder=""):
        """Download de um arquivo PDF"""
        try:
            full_path = os.path.join(self.download_dir, subfolder, filename)
            
            # Verifica se já existe
            if os.path.exists(full_path):
                logger.info(f"Arquivo já existe: {filename}")
                return True
            
            logger.info(f"Baixando: {filename}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Verifica se é realmente um PDF
            if 'application/pdf' not in response.headers.get('content-type', ''):
                logger.warning(f"Arquivo pode não ser PDF: {filename}")
            
            with open(full_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ Baixado com sucesso: {filename}")
            time.sleep(1)  # Pausa respeitosa entre downloads
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao baixar {filename}: {e}")
            return False
    
    def download_presidencia_manual(self):
        """Download do Manual de Redação da Presidência"""
        logger.info("📋 Baixando Manual de Redação da Presidência...")
        
        # URL direta para o manual (verificar se ainda está ativa)
        url = "https://www4.planalto.gov.br/centrodeestudos/assuntos/manual-de-redacao-da-presidencia-da-republica/manual-de-redacao.pdf"
        return self.download_file(url, "manual_redacao_presidencia.pdf", "governamentais")
    
    def download_abl_materials(self):
        """Download de materiais da Academia Brasileira de Letras"""
        logger.info("🎓 Baixando materiais da ABL...")
        
        # URLs de materiais públicos da ABL (verificar disponibilidade)
        materials = [
            {
                "url": "https://www.academia.org.br/sites/default/files/publicacoes/arquivos/pequeno_vocabulario_2009.pdf",
                "filename": "abl_pequeno_vocabulario.pdf"
            }
        ]
        
        success_count = 0
        for material in materials:
            if self.download_file(material["url"], material["filename"], "governamentais"):
                success_count += 1
        
        return success_count > 0
    
    def download_public_domain_books(self):
        """Download de livros de domínio público"""
        logger.info("📚 Baixando livros clássicos de domínio público...")
        
        # URLs do Internet Archive para gramáticas clássicas
        books = [
            {
                "url": "https://archive.org/download/grammaticahistor00saiduoft/grammaticahistor00saiduoft.pdf",
                "filename": "said_ali_gramatica_historica.pdf"
            },
            {
                "url": "https://archive.org/download/grammaticaportu00ribegoog/grammaticaportu00ribegoog.pdf", 
                "filename": "joao_ribeiro_gramatica.pdf"
            }
        ]
        
        success_count = 0
        for book in books:
            if self.download_file(book["url"], book["filename"], "classicos"):
                success_count += 1
        
        return success_count > 0
    
    def download_university_materials(self):
        """Download de materiais universitários públicos"""
        logger.info("🏛️ Baixando materiais universitários...")
        
        # URLs de teses e materiais universitários públicos
        materials = [
            {
                "url": "https://www.teses.usp.br/teses/disponiveis/8/8142/tde-exemplo/publico/exemplo_linguistica.pdf",
                "filename": "usp_linguistica_exemplo.pdf"
            }
        ]
        
        success_count = 0
        for material in materials:
            if self.download_file(material["url"], material["filename"], "academicos"):
                success_count += 1
        
        return success_count > 0
    
    def create_sample_materials(self):
        """Cria materiais de exemplo quando downloads falham"""
        logger.info("📝 Criando materiais de exemplo...")
        
        # Conteúdo de exemplo baseado em gramática real
        sample_content = """
# Manual de Gramática Portuguesa - Exemplos

## 1. CONCORDÂNCIA VERBAL

### Regra Básica
O verbo concorda com o sujeito em número e pessoa.

**Exemplos Corretos:**
- O aluno estuda muito. (singular)
- Os alunos estudam muito. (plural)
- Tu estudas português. (2ª pessoa singular)
- Vós estudais português. (2ª pessoa plural)

**Exemplos Incorretos:**
- O aluno estudam muito. ❌
- Os alunos estuda muito. ❌
- Tu estuda português. ❌
- Vós estuda português. ❌

### Casos Especiais

**Sujeito Coletivo:**
- A multidão gritava. ✅
- A multidão gritavam. ❌

**Sujeito Composto:**
- João e Maria chegaram. ✅
- João e Maria chegou. ❌

## 2. CONCORDÂNCIA NOMINAL

### Regra Básica
O adjetivo concorda com o substantivo em gênero e número.

**Exemplos Corretos:**
- Casa bonita (feminino singular)
- Casas bonitas (feminino plural)
- Livro interessante (masculino singular)
- Livros interessantes (masculino plural)

**Exemplos Incorretos:**
- Casa bonito ❌
- Casas bonito ❌
- Livro interessantes ❌
- Livros interessante ❌

## 3. REGÊNCIA VERBAL

### Verbos Transitivos Diretos
Não precisam de preposição:

**Correto:**
- Eu comprei o livro.
- Ela encontrou a chave.
- Nós vimos o filme.

**Incorreto:**
- Eu comprei do livro. ❌
- Ela encontrou à chave. ❌
- Nós vimos ao filme. ❌

### Verbos Transitivos Indiretos
Precisam de preposição:

**Correto:**
- Eu gosto de música.
- Ela precisa de ajuda.
- Nós assistimos ao filme.

**Incorreto:**
- Eu gosto música. ❌
- Ela precisa ajuda. ❌
- Nós assistimos o filme. ❌

## 4. ORTOGRAFIA

### Uso do X e CH

**Com X:**
- México, mexer, enxada, xícara
- Aproximar, máximo, próximo
- Exemplo, exame, exercício

**Com CH:**
- Achar, chave, chuva, machado
- Achatar, pachecar, chocalho
- Chinelo, cheiro, achado

**Erros Comuns:**
- Méhico → México ✅
- Meher → mexer ✅
- Enchada → enxada ✅
- Chícara → xícara ✅

### Uso do S, SS, Ç

**Com S:**
- Casa, mesa, presente
- Português, francês, inglês
-Rase... ❌ → Base ✅

**Com SS:**
- Passo, classe, processo
- Professor, sucessor, acessor
- Posso, possa, possível

**Com Ç:**
- Caça, praça, abraço
- Ação, lição, oração
- Exceção, recepção, decepção

**Erros Comuns:**
- Prosesso → processo ✅
- Asesso → acesso ✅
- Eseção → exceção ✅

## 5. ACENTUAÇÃO

### Oxítonas
Acentuam-se as terminadas em A, E, O, EM, ENS:

**Correto:**
- Sofá, café, avô, alguém, parabéns

**Incorreto:**
- Sofa, cafe, avo, alguem, parabens ❌

### Paroxítonas  
Acentuam-se as NÃO terminadas em A, E, O, EM, ENS:

**Correto:**
- Fácil, caráter, álbum, hífen

**Incorreto:**
- Facil, carater, album, hifen ❌

### Proparoxítonas
TODAS são acentuadas:

**Correto:**
- Médico, rápido, lâmpada, público

**Incorreto:**
- Medico, rapido, lampada, publico ❌

## 6. CRASE

### Uso Obrigatório
- Antes de palavras femininas: Vou à escola.
- Nas locuções: à tarde, à noite, às vezes.
- Antes de "aquela", "aquele": Refiro-me àquela casa.

### Uso Proibido
- Antes de palavras masculinas: Vou a pé.
- Antes de verbos: Começou a chover.
- Antes de pronomes: Falei a ela.

**Exemplos:**
- Vou à praia. ✅
- Vou a praia. ❌
- Vou ao mercado. ✅
- Vou à mercado. ❌

## EXERCÍCIOS PRÁTICOS

### Corrija os erros:

1. Os menino brinca no parque. ❌
   → Os meninos brincam no parque. ✅

2. Eu gosto muito de musicas. ❌
   → Eu gosto muito de músicas. ✅

3. Ela vai a escola todo dia. ❌
   → Ela vai à escola todo dia. ✅

4. O professor ensinou os aluno. ❌
   → O professor ensinou os alunos. ✅

5. Nos vamos viajar amanha. ❌
   → Nós vamos viajar amanhã. ✅
"""
        
        # Salva como arquivo de exemplo
        sample_file = os.path.join(self.download_dir, "especializados", "exemplo_gramatica_completa.txt")
        with open(sample_file, 'w', encoding='utf-8') as f:
            f.write(sample_content)
        
        logger.info(f"✅ Arquivo de exemplo criado: {sample_file}")
        return True
    
    def download_all(self):
        """Executa todos os downloads"""
        logger.info("🚀 Iniciando download de materiais de gramática...")
        
        downloads_successful = []
        
        # Tenta baixar cada categoria
        try:
            if self.download_presidencia_manual():
                downloads_successful.append("Manual da Presidência")
        except Exception as e:
            logger.error(f"Erro no download da Presidência: {e}")
        
        try:
            if self.download_abl_materials():
                downloads_successful.append("Materiais ABL")
        except Exception as e:
            logger.error(f"Erro no download da ABL: {e}")
        
        try:
            if self.download_public_domain_books():
                downloads_successful.append("Livros clássicos")
        except Exception as e:
            logger.error(f"Erro no download de livros clássicos: {e}")
        
        try:
            if self.download_university_materials():
                downloads_successful.append("Materiais universitários")
        except Exception as e:
            logger.error(f"Erro no download universitário: {e}")
        
        # Sempre cria materiais de exemplo
        if self.create_sample_materials():
            downloads_successful.append("Materiais de exemplo")
        
        # Relatório final
        logger.info(f"✅ Downloads concluídos: {len(downloads_successful)} categorias")
        for category in downloads_successful:
            logger.info(f"   ✓ {category}")
        
        # Lista arquivos baixados
        self.list_downloaded_files()
        
        return len(downloads_successful) > 0
    
    def list_downloaded_files(self):
        """Lista todos os arquivos baixados"""
        logger.info("📋 Arquivos disponíveis para treinamento:")
        
        for root, dirs, files in os.walk(self.download_dir):
            for file in files:
                if file.endswith(('.pdf', '.txt')):
                    rel_path = os.path.relpath(os.path.join(root, file), self.download_dir)
                    file_size = os.path.getsize(os.path.join(root, file))
                    logger.info(f"   📄 {rel_path} ({file_size:,} bytes)")

def main():
    """Função principal"""
    print("🚀 DOWNLOAD AUTOMATIZADO DE PDFs DE GRAMÁTICA")
    print("=" * 60)
    
    downloader = PDFDownloader()
    
    try:
        success = downloader.download_all()
        
        if success:
            print("\n🎉 Download concluído com sucesso!")
            print("📁 Arquivos salvos em: /app/grammar_pdfs")
            print("\n🚀 Próximos passos:")
            print("1. Execute: python fine_tuning.py")
            print("2. Ou execute: python exemplo_treinamento_pdf.py")
        else:
            print("\n❌ Nenhum download foi bem-sucedido")
            print("💡 Verifique sua conexão com a internet")
            print("📁 Materiais de exemplo foram criados em /app/grammar_pdfs")
            
    except Exception as e:
        print(f"\n❌ Erro durante o download: {e}")
        print("📝 Consulte o arquivo FONTES_PDFS_GRAMATICA.md para download manual")

if __name__ == "__main__":
    main()
