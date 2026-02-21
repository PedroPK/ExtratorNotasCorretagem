#!/usr/bin/env python3
import zipfile
import pdfplumber

zip_path = '/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/resouces/inputNotasCorretagem/drive-download-20260216T170007Z-1-001.zip'
pdf_name = 'Clear 2018 10 Outubro - Notas Negociação Corretagem.pdf'

with zipfile.ZipFile(zip_path, 'r') as z:
    with z.open(pdf_name) as f:
        pdf = pdfplumber.open(f)
        page = pdf.pages[5]
        
        # Get all tables
        tables = page.extract_tables()
        
        print("TODAS AS TABELAS ENCONTRADAS:")
        print("="*80)
        
        for idx, table in enumerate(tables):
            if not table:
                continue
            num_cols = len(table[0])
            num_rows = len(table)
            
            # Check if contains ELETROBRAS ON N1 or RAIADROGASIL
            has_eletrobras_on = False
            has_raiadrogasil = False
            has_eletrobras_pnb = False
            has_cemig = False
            
            for row in table:
                full_row = ' '.join(str(c or '') for c in row)
                if 'ELETROBRAS ON N1' in full_row:
                    has_eletrobras_on = True
                if 'ELETROBRAS PNB' in full_row:
                    has_eletrobras_pnb = True
                if 'RAIADROGASIL' in full_row:
                    has_raiadrogasil = True
                if 'CEMIG' in full_row:
                    has_cemig = True
            
            marker = ""
            if has_eletrobras_on:
                marker += " [ELETROBRAS ON]"
            if has_eletrobras_pnb:
                marker += " [ELETROBRAS PNB]"
            if has_raiadrogasil:
                marker += " [RAIADROGASIL]"
            if has_cemig:
                marker += " [CEMIG]"
            
            print(f"Tabela {idx}: {num_rows} linhas x {num_cols} colunas{marker}")

