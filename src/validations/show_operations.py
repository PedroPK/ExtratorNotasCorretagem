#!/usr/bin/env python3
import zipfile
import pdfplumber

zip_path = '/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/resouces/inputNotasCorretagem/drive-download-20260216T170007Z-1-001.zip'
pdf_name = 'Clear 2018 10 Outubro - Notas Negociação Corretagem.pdf'

with zipfile.ZipFile(zip_path, 'r') as z:
    with z.open(pdf_name) as f:
        pdf = pdfplumber.open(f)
        page = pdf.pages[5]
        
        tables = page.extract_tables()
        
        print("TABELAS COM 11 COLUNAS - OPERACOES INDIVIDUAIS:")
        print("="*80)
        
        operacao_count = 0
        for idx, table in enumerate(tables):
            if not table or len(table[0]) != 11:
                continue
            
            operacao_count += 1
            
            if len(table) < 1:
                continue
                
            row = table[0]
            cells = [(c or '').strip() for c in row]
            
            # Extract fields
            mercado = cells[1] if len(cells) > 1 else ''
            operacao = cells[2] if len(cells) > 2 else ''
            tipo = cells[3] if len(cells) > 3 else ''
            asset_name = cells[5] if len(cells) > 5 else ''
            qtd = cells[7] if len(cells) > 7 else ''
            preco = cells[8] if len(cells) > 8 else ''
            valor = cells[9] if len(cells) > 9 else ''
            
            print(f"Operacao {operacao_count} (Tabela {idx}): {asset_name:25} | Op:{operacao:3} | Qtd:{qtd:3} | Preco:{preco:7} | Valor:{valor:7}")

