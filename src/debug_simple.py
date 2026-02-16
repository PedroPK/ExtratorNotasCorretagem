#!/usr/bin/env python3
"""Debug direto: testa a validação em uma tabela específica."""

import os
import sys
import zipfile
import pdfplumber
import re
from io import BytesIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from extratorNotasCorretagem import _is_valid_data_row, _extract_ticker_from_cells

caminho = os.path.join(os.path.dirname(__file__), 'resouces', 'inputNotasCorretagem')
zip_file = None
for f in os.listdir(caminho):
    if f.endswith('.zip'):
        zip_file = os.path.join(caminho, f)
        break

if not zip_file:
    print("No ZIP found")
    sys.exit(1)

print(f"Opening: {zip_file}")

with zipfile.ZipFile(zip_file, 'r') as z:
    pdf_names = [n for n in z.namelist() if n.endswith('.pdf')]
    
    # Use first PDF
    first_pdf = pdf_names[0]
    print(f"Testing: {first_pdf}\n")
    
    with z.open(first_pdf) as pdf_stream:
        pdf_bytes = pdf_stream.read()
        bio = BytesIO(pdf_bytes)
        bio.name = first_pdf
        
        try:
            pdf = pdfplumber.open(bio, password='454')
        except:
            print("Error opening PDF")
            sys.exit(1)
        
        with pdf:
            # Find a table with 11 columns
            for page_idx, page in enumerate(pdf.pages[:1]):
                tables = page.extract_tables()
                
                for table_idx, table in enumerate(tables):
                    if not table:
                        continue
                    
                    num_cols = len(table[0]) if table[0] else 0
                    if num_cols != 11:
                        continue
                    
                    print(f"Found 11-column table on page {page_idx + 1}, table {table_idx}")
                    print(f"Total rows: {len(table)}\n")
                    
                    # Test each row
                    passed = 0
                    failed = 0
                    for row_idx, row in enumerate(table[:20]):  # First 20 rows
                        if not row or all(not (str(c).strip()) for c in row):
                            continue
                        
                        cells = [(c or '').strip() for c in row]
                        
                        # Test with negotiation flag
                        is_valid = _is_valid_data_row(cells, is_negotiation_table=True)
                        
                        if is_valid:
                            ticker = _extract_ticker_from_cells(cells)
                            print(f"✓ Row {row_idx}: PASSA | ticker={ticker}")
                            print(f"  Cells: {cells[:5]}")
                            passed += 1
                        else:
                            failed += 1
                            # Debug why it failed
                            row_text = ' '.join(cells).upper()
                            if 'RESUMO' in row_text:
                                print(f"✗ Row {row_idx}: REJEITADA (resumo)")
                            elif 'TOTAL' in row_text:
                                print(f"✗ Row {row_idx}: REJEITADA (total)")
                            elif 'CLIENTE' in row_text:
                                print(f"✗ Row {row_idx}: REJEITADA (cliente)")
                            else:
                                # Check if has number
                                has_num = any(re.search(r'\d', str(c)) for c in cells)
                                if not has_num:
                                    print(f"✗ Row {row_idx}: REJEITADA (sem número)")
                                else:
                                    print(f"✗ Row {row_idx}: REJEITADA (skip keyword?)")
                                    print(f"  Text: {row_text[:80]}")
                    
                    print(f"\nResumo: {passed} passou, {failed} rejeitada")
                    break
