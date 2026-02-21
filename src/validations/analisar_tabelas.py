#!/usr/bin/env python3
"""
Script para analisar a estrutura exata das tabelas nos PDFs
"""

import pdfplumber
import pdfplumber.utils
import os
import zipfile
from io import BytesIO
import json
import traceback

def analisar_tabelas_detalhadamente(arquivo_pdf, nome_arquivo=None):
    """Analisa as tabelas em detalhes"""
    
    if nome_arquivo is None:
        nome_arquivo = os.path.basename(arquivo_pdf) if isinstance(arquivo_pdf, str) else "pdf"
    
    print(f"\n{'='*90}")
    print(f"📄 Analisando: {nome_arquivo}")
    print(f"{'='*90}")
    
    # Levanta exceção aqui se não conseguir abrir
    pdf = pdfplumber.open(arquivo_pdf)
    
    try:
        print(f"\n✓ Páginas: {len(pdf.pages)}")
        
        # Analisa apenas primeira página
        page = pdf.pages[0]
        
        # Extrai todo o texto para referência
        texto = page.extract_text()
        print(f"\n📋 TEXTO DA PÁGINA 1 (primeiros 600 caracteres):")
        print("-" * 90)
        print(texto[:600])
        
        # Obtém tabelas
        tabelas = page.extract_tables()
        print(f"\n\n🔍 TABELAS ENCONTRADAS: {len(tabelas)}")
        
        for num_tabela, tabela in enumerate(tabelas):
            print(f"\n{'─'*90}")
            print(f"📊 TABELA {num_tabela + 1}")
            print(f"{'─'*90}")
            print(f"Dimensões: {len(tabela)} linhas × {len(tabela[0]) if tabela else 0} colunas")
            
            if not tabela:
                continue
            
            # Mostra cada coluna
            num_cols = len(tabela[0])
            print(f"\nEstrutura das colunas:")
            for col_idx in range(num_cols):
                print(f"\n  COL[{col_idx}]:")
                for row_idx in range(min(5, len(tabela))):
                    valor = tabela[row_idx][col_idx]
                    valor_str = str(valor)[:60] if valor else "[VAZIO]"
                    print(f"    Linha {row_idx}: {valor_str}")
            
            # Se for a tabela de negociações (11 colunas)
            if num_cols == 11 and len(tabela) > 1:
                print(f"\n📈 Esta parece ser a tabela de NEGOCIAÇÕES!")
                print(f"\nCabeçalhos (linha 0):")
                for col_idx, valor in enumerate(tabela[0]):
                    print(f"  [{col_idx}]: {valor}")
                
                print(f"\nExemplo de primeira linha de dados (linha 1):")
                if len(tabela) > 1:
                    for col_idx, valor in enumerate(tabela[1]):
                        print(f"  [{col_idx}]: {valor}")
    
    finally:
        pdf.close()


def analisar_zip(caminho_zip):
    """Analisa PDFs no ZIP"""
    
    try:
        with zipfile.ZipFile(caminho_zip, 'r') as z:
            pdfs = [f for f in z.namelist() if f.endswith('.pdf')]
            print(f"\n📦 Total de PDFs: {len(pdfs)}")
            
            # Testa até encontrar 1 que funcione
            sucesso = 0
            for pdf_nome in pdfs:
                if sucesso >= 1:
                    break
                
                try:
                    print(f"\n⏳ Tentando: {pdf_nome}...", end=" ")
                    with z.open(pdf_nome) as f:
                        bio = BytesIO(f.read())
                        bio.name = pdf_nome
                        analisar_tabelas_detalhadamente(bio, pdf_nome)
                        sucesso += 1
                except pdfplumber.utils.exceptions.PdfminerException:
                    print(f"⏭️  PDF protegido")
                    continue
                except Exception as e:
                    print(f"⏭️  {type(e).__name__}")
                    continue
    
    except Exception as e:
        print(f"❌ Erro ao processar ZIP: {str(e)}")



if __name__ == "__main__":
    caminho_pasta = "../resouces/inputNotasCorretagem"
    caminho_absoluto = os.path.join(os.path.dirname(__file__), caminho_pasta)
    
    print("\n" + "="*90)
    print("🔬 ANÁLISE DETALHADA DE TABELAS")
    print("="*90)
    
    arquivos_zip = [f for f in os.listdir(caminho_absoluto) if f.endswith('.zip')]
    
    if arquivos_zip:
        analisar_zip(os.path.join(caminho_absoluto, arquivos_zip[0]))
