#!/usr/bin/env python3
"""
Script de debug para explorar a estrutura dos PDFs
e entender quais dados podem ser extraídos
"""

import pdfplumber
import os
import zipfile
from io import BytesIO
import json
import traceback

def explorar_pdf(arquivo_pdf, nome_arquivo=None):
    """Explora a estrutura completa de um PDF"""
    
    if nome_arquivo is None:
        nome_arquivo = os.path.basename(arquivo_pdf) if isinstance(arquivo_pdf, str) else "pdf_temporario"
    
    print("\n" + "=" * 80)
    print(f"📄 Explorando: {nome_arquivo}")
    print("=" * 80)
    
    try:
        with pdfplumber.open(arquivo_pdf) as pdf:
            print(f"\n✓ Total de páginas: {len(pdf.pages)}")
            
            # Limita a exploração às primeiras 3 páginas
            paginas_para_explorar = min(3, len(pdf.pages))
            
            for num_pagina in range(paginas_para_explorar):
                page = pdf.pages[num_pagina]
                
                print(f"\n{'─' * 80}")
                print(f"📖 PÁGINA {num_pagina + 1}")
                print(f"{'─' * 80}")
                
                try:
                    # 1. Extrair texto
                    print("\n1️⃣  TEXTO EXTRAÍDO:")
                    print("-" * 40)
                    texto = page.extract_text()
                    if texto:
                        # Mostra apenas os primeiros 500 caracteres
                        preview = texto[:500] if len(texto) > 500 else texto
                        print(preview)
                        if len(texto) > 500:
                            print(f"\n... ({len(texto) - 500} caracteres omitidos)")
                        print(f"Total de caracteres: {len(texto)}")
                    else:
                        print("⚠️  Nenhum texto encontrado")
                except Exception as e:
                    print(f"❌ Erro ao extrair texto: {e}")
                
                try:
                    # 2. Procurar por datas
                    print("\n2️⃣  DATAS ENCONTRADAS:")
                    print("-" * 40)
                    import re
                    datas = re.findall(r'\d{2}/\d{2}/\d{4}', texto or "")
                    if datas:
                        for data in set(datas):
                            print(f"   • {data}")
                    else:
                        print("⚠️  Nenhuma data encontrada")
                except Exception as e:
                    print(f"❌ Erro ao procurar datas: {e}")
                
                try:
                    # 3. Extrair tabelas
                    print("\n3️⃣  TABELAS ENCONTRADAS:")
                    print("-" * 40)
                    tables = page.extract_tables()
                    
                    if tables:
                        print(f"Total de tabelas: {len(tables)}")
                        
                        for num_tabela, table in enumerate(tables, 1):
                            print(f"\n   📊 Tabela {num_tabela}:")
                            print(f"   Dimensões: {len(table)} linhas x {len(table[0]) if table else 0} colunas")
                            
                            # Mostra cabeçalho
                            if table and len(table) > 0:
                                print(f"\n   Cabeçalho (primeiras 5 colunas):")
                                for col_idx in range(min(5, len(table[0]))):
                                    val = table[0][col_idx] if table[0][col_idx] else "[vazio]"
                                    print(f"      Col[{col_idx}]: {str(val)[:60]}")
                            
                            # Mostra primeiras linhas
                            if len(table) > 1:
                                print(f"\n   Primeiras 3 linhas de dados:")
                                for row_idx in range(min(3, len(table) - 1)):
                                    row = table[row_idx + 1]
                                    preview = [str(v)[:20] if v else "[vazio]" for v in row[:5]]
                                    print(f"      Linha {row_idx + 1}: {preview}")
                    else:
                        print("⚠️  Nenhuma tabela encontrada")
                except Exception as e:
                    print(f"❌ Erro ao extrair tabelas: {e}")
                    traceback.print_exc()
                
                try:
                    # 4. Procurar por palavras-chave
                    print("\n4️⃣  PALAVRAS-CHAVE:")
                    print("-" * 40)
                    palavras_chave = [
                        "pregão", "data pregão", "especificação", "quantidade", 
                        "preço", "operação", "compra", "venda", "corretora",
                        "negócio", "resumo", "total", "ativo", "código"
                    ]
                    
                    if texto:
                        texto_upper = texto.upper()
                        encontradas = []
                        for palavra in palavras_chave:
                            if palavra.upper() in texto_upper:
                                encontradas.append(palavra)
                        
                        if encontradas:
                            for palavra in encontradas:
                                print(f"   ✓ {palavra}")
                        else:
                            print("⚠️  Nenhuma palavra-chave encontrada")
                except Exception as e:
                    print(f"❌ Erro ao procurar palavras-chave: {e}")
                
                try:
                    # 5. Ocorrências de padrões
                    print("\n5️⃣  PADRÕES ENCONTRADOS:")
                    print("-" * 40)
                    
                    # Procura por Tickers (4 letras + 2 números)
                    tickers = re.findall(r'[A-Z]{4}\d{2}', texto or "")
                    if tickers:
                        print(f"   Tickers: {', '.join(set(tickers))}")
                    else:
                        print("   ⚠️  Nenhum ticker encontrado")
                    
                    # Procura por números com decimais
                    numeros = re.findall(r'\d{1,3}[.,]\d{1,3}[.,]?\d*', texto or "")
                    if numeros:
                        print(f"   Números encontrados: {len(set(numeros))} únicos")
                        print(f"   Exemplos: {list(set(numeros))[:5]}")
                    else:
                        print("   ⚠️  Nenhum número encontrado")
                except Exception as e:
                    print(f"❌ Erro ao procurar padrões: {e}")
    
    except Exception as e:
        print(f"❌ Erro geral ao processar PDF: {str(e)}")
        traceback.print_exc()


def explorar_pasta(caminho_pasta):
    """Explora todos os PDFs de uma pasta"""
    
    if not os.path.exists(caminho_pasta):
        print(f"❌ Pasta não encontrada: {caminho_pasta}")
        return
    
    print("\n" + "=" * 80)
    print(f"📂 Explorando pasta: {caminho_pasta}")
    print("=" * 80)
    
    # Procura por PDFs diretos
    arquivos_pdf = [f for f in os.listdir(caminho_pasta) if f.endswith('.pdf')]
    
    # Procura por ZIPs
    arquivos_zip = [f for f in os.listdir(caminho_pasta) if f.endswith('.zip')]
    
    print(f"\n📄 PDFs encontrados: {len(arquivos_pdf)}")
    print(f"📦 ZIPs encontrados: {len(arquivos_zip)}")
    
    # Processa PDFs diretos
    for arquivo_pdf in arquivos_pdf[:1]:  # Apenas o primeiro para não sobrecarregar
        caminho_completo = os.path.join(caminho_pasta, arquivo_pdf)
        explorar_pdf(caminho_completo, arquivo_pdf)
    
    # Processa primeiro ZIP encontrado
    if arquivos_zip:
        for arquivo_zip in arquivos_zip[:1]:
            caminho_zip = os.path.join(caminho_pasta, arquivo_zip)
            print(f"\n📦 Processando ZIP: {arquivo_zip}")
            
            try:
                with zipfile.ZipFile(caminho_zip, 'r') as z:
                    pdfs_no_zip = [f for f in z.namelist() if f.endswith('.pdf')]
                    print(f"   PDFs no ZIP: {len(pdfs_no_zip)}")
                    
                    # Processa apenas o primeiro PDF do ZIP
                    if pdfs_no_zip:
                        primeiro_pdf = pdfs_no_zip[0]
                        print(f"   Explorando: {primeiro_pdf}")
                        
                        with z.open(primeiro_pdf) as f:
                            bio = BytesIO(f.read())
                            bio.name = primeiro_pdf
                            explorar_pdf(bio, primeiro_pdf)
            
            except Exception as e:
                print(f"❌ Erro ao processar ZIP: {str(e)}")
                traceback.print_exc()


if __name__ == "__main__":
    # Caminho da pasta com os arquivos
    caminho_pasta = "../resouces/inputNotasCorretagem"
    
    # Resolve para caminho absoluto
    caminho_absoluto = os.path.join(os.path.dirname(__file__), caminho_pasta)
    
    print("🔍 EXPLORADOR DE PDFs - Extrator Notas Corretagem\n")
    
    explorar_pasta(caminho_absoluto)
    
    print("\n" + "=" * 80)
    print("✓ Exploração concluída!")
    print("=" * 80)
