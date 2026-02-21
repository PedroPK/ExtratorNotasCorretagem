#!/usr/bin/env python3
"""
Script de debug avançado para explorar PDFs protegidos
"""

import pdfplumber
import os
import zipfile
from io import BytesIO
import traceback

def tentar_abrir_pdf(arquivo_pdf, nome_arquivo=None):
    """Tenta abrir PDF com várias estratégias"""
    
    if nome_arquivo is None:
        nome_arquivo = os.path.basename(arquivo_pdf) if isinstance(arquivo_pdf, str) else "pdf_temporario"
    
    print(f"\n📄 Tentando abrir: {nome_arquivo}")
    
    senhas = ["", None]  # Tira com senha vazia
    
    for senha in senhas:
        try:
            if senha is not None:
                pdf = pdfplumber.open(arquivo_pdf, password=senha)
            else:
                pdf = pdfplumber.open(arquivo_pdf)
            
            print(f"✓ PDF aberto com sucesso!")
            print(f"  Total de páginas: {len(pdf.pages)}")
            
            # Tenta extrair texto da primeira página
            pagina1 = pdf.pages[0]
            texto = pagina1.extract_text()
            
            if texto:
                print(f"✓ Texto extraível!")
                print(f"  Primeiros 200 caracteres:")
                print(f"  {texto[:200]}")
                print(f"  Total de caracteres na página 1: {len(texto)}")
            else:
                print("⚠️  Nenhum texto extraído da página")
            
            # Tenta extrair tabelas
            tabelas = pagina1.extract_tables()
            if tabelas:
                print(f"✓ Tabelas encontradas: {len(tabelas)}")
                for i, tabela in enumerate(tabelas):
                    print(f"  Tabela {i+1}: {len(tabela)} linhas x {len(tabela[0]) if tabela else 0} colunas")
            else:
                print("⚠️  Nenhuma tabela encontrada")
            
            pdf.close()
            return True
            
        except pdfplumber.utils.exceptions.PdfminerException as e:
            print(f"⚠️  Esta abordagem não funcionou: Erro PDFMiner")
            continue
        except Exception as e:
            # Continua tentando outras senhas
            continue
    
    print(f"❌ Não foi possível abrir o PDF")
    return False


def explorar_zip(caminho_zip):
    """Explora PDFs dentro de um ZIP"""
    
    print(f"\n📦 Explorando ZIP: {os.path.basename(caminho_zip)}")
    
    try:
        with zipfile.ZipFile(caminho_zip, 'r') as z:
            pdfs = [f for f in z.namelist() if f.endswith('.pdf')]
            print(f"   Total de PDFs: {len(pdfs)}")
            
            # Testa os 3 primeiros PDFs
            for pdf_nome in pdfs[:3]:
                print(f"\n{'─' * 80}")
                
                with z.open(pdf_nome) as f:
                    bio = BytesIO(f.read())
                    bio.name = pdf_nome
                    tentar_abrir_pdf(bio, pdf_nome)
    
    except Exception as e:
        print(f"❌ Erro ao processar ZIP: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    caminho_pasta = "../resouces/inputNotasCorretagem"
    caminho_absoluto = os.path.join(os.path.dirname(__file__), caminho_pasta)
    
    print("=" * 80)
    print("🔍 EXPLORADOR AVANÇADO DE PDFs")
    print("=" * 80)
    
    if not os.path.exists(caminho_absoluto):
        print(f"❌ Pasta não encontrada: {caminho_absoluto}")
    else:
        arquivos_zip = [f for f in os.listdir(caminho_absoluto) if f.endswith('.zip')]
        
        if arquivos_zip:
            for arquivo_zip in arquivos_zip[:1]:
                explorar_zip(os.path.join(caminho_absoluto, arquivo_zip))
        else:
            print("❌ Nenhum arquivo ZIP encontrado")
    
    print("\n" + "=" * 80)
    print("✓ Exploração concluída!")
    print("=" * 80)
