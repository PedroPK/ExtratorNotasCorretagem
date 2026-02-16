#!/usr/bin/env python3
"""Debug script to test _is_valid_data_row() function on actual PDF data."""

import os
import sys
import zipfile
import pdfplumber
import re
from io import BytesIO

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from extratorNotasCorretagem import _is_valid_data_row, _extract_ticker_from_cells, _normalize_number

def test_pdf_extraction():
    """Extract rows from first PDF and test validation."""
    caminho = os.path.join(os.path.dirname(__file__), 'resouces', 'inputNotasCorretagem')
    
    # Check if ZIP exists
    files = os.listdir(caminho)
    pdf_files = [f for f in files if f.endswith('.zip') or f.endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF or ZIP files found")
        return
    
    # Try to find ZIP
    zip_file = None
    for f in pdf_files:
        if f.endswith('.zip'):
            zip_file = os.path.join(caminho, f)
            break
    
    if not zip_file:
        print("No ZIP file found")
        return
    
    print(f"Opening ZIP: {zip_file}")
    
    with zipfile.ZipFile(zip_file, 'r') as z:
        pdf_names = [n for n in z.namelist() if n.endswith('.pdf')]
        print(f"Found {len(pdf_names)} PDFs, using first one...")
        
        if not pdf_names:
            print("No PDFs in ZIP")
            return
        
        first_pdf = pdf_names[0]
        print(f"\nTesting with: {first_pdf}")
        
        with z.open(first_pdf) as pdf_stream:
            pdf_bytes = pdf_stream.read()
            bio = BytesIO(pdf_bytes)
            bio.name = first_pdf  # Add name attribute
            
            try:
                # Try without password first
                pdf = pdfplumber.open(bio)
            except:
                # Try with common password
                try:
                    bio.seek(0)
                    pdf = pdfplumber.open(bio, password='454')
                except Exception as e:
                    print(f"Error opening PDF: {e}")
                    return
            
            with pdf:
                total_pages = len(pdf.pages)
                print(f"Total pages: {total_pages}\n")
                
                # Find the table that contains actual transactions (has tickers)
                for page_idx, page in enumerate(pdf.pages[:2]):  # Check first 2 pages
                    tables = page.extract_tables()
                    print(f"\n=== PAGE {page_idx + 1}: {len(tables)} tables ===")
                    
                    for table_idx, table in enumerate(tables):
                        if not table:
                            continue
                        
                        num_cols = len(table[0]) if table[0] else 0
                        table_text = ' '.join(' '.join([str(c) for c in row if c]) for row in table[:5])
                        has_ticker = any(re.search(r'[A-Z]{4}\d{2}', str(cell)) for row in table for cell in row if cell)
                        
                        print(f"Table {table_idx}: {num_cols} cols, {len(table)} rows, has_ticker={has_ticker}")
                        print(f"  First row: {table[0][:3] if table else 'empty'}")
                        
                        if has_ticker:
                            print(f"  ✓ This table has tickers!")
                            # Show first transaction row
                            for row in table[:10]:
                                cells = [(c or '').strip() for c in row]
                                # Find row with ticker
                                for cell in cells:
                                    if re.search(r'[A-Z]{4}\d{2}', str(cell)):
                                        print(f"    Transaction row: {cells[:6]}")
                                        break

if __name__ == '__main__':
    test_pdf_extraction()
