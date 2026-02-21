#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/src')

import zipfile
import pdfplumber

zip_path = '/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/resouces/inputNotasCorretagem/drive-download-20260216T170007Z-1-001.zip'
pdf_name = 'Clear 2018 10 Outubro - Notas Negociação Corretagem.pdf'

with zipfile.ZipFile(zip_path, 'r') as z:
    with z.open(pdf_name) as f:
        pdf = pdfplumber.open(f)
        page = pdf.pages[5]  # Page 6
        
        # Get raw text
        text = page.extract_text()
        
        print(f"{'='*80}")
        print(f"PROCURANDO ELETROBLAS E RAIADROGASIL NA PÁGINA 6")
        print(f"{'='*80}\n")
        
        if 'ELETROBLAS ON' in text:
            print("✓ ENCONTRADO: ELETROBLAS ON")
        else:
            print("✗ NÃO ENCONTRADO: ELETROBLAS ON")
            
        if 'ELETROBRA ON N1' in text:
            print("✓ ENCONTRADO: ELETROBRA ON N1 (SEM S)")
        else:
            print("✗ NÃO ENCONTRADO: ELETROBRA ON N1")
            
        if 'RAIADROGASIL' in text:
            print("✓ ENCONTRADO: RAIADROGASIL")
        else:
            print("✗ NÃO ENCONTRADO: RAIADROGASIL")
        
        # Show all 11-column tables
        print(f"\n{'='*80}")
        print("TODAS AS TABELAS (não apenas as com 11 colunas):")
        print(f"{'='*80}\n")
        
        tables = page.extract_tables()
        for idx, table in enumerate(tables):
            if table and len(table) > 0:
                num_cols = len(table[0])
                num_rows = len(table)
                
                # Extract some text to identify
                text = ' '.join(' '.join([str(c or '') for c in row]) for row in table[:2])
                
                print(f"Tabela {idx}: {num_rows} linhas × {num_cols} colunas - {text[:70]}...")

