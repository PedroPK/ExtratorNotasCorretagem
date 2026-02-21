#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/src')

import zipfile
import pdfplumber

zip_path = '/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/resouces/inputNotasCorretagem/drive-download-20260216T170007Z-1-001.zip'

print(f"Opening ZIP: {zip_path}")
with zipfile.ZipFile(zip_path, 'r') as z:
    entries = z.namelist()
    pdf_entries = [e for e in entries if e.endswith('.pdf')]
    print(f"Found {len(pdf_entries)} PDF files:")
    for e in pdf_entries[:10]:
        print(f"  - {e}")
    
    # Test extract first PDF
    if pdf_entries:
        first_pdf = pdf_entries[0]
        print(f"\nTesting first PDF: {first_pdf}")
        
        with z.open(first_pdf) as ef:
            try:
                pdf = pdfplumber.open(ef.read(), password='454')
                print(f"  Pages: {len(pdf.pages)}")
                
                # Try first page
                page = pdf.pages[0]
                text = page.extract_text()
                print(f"  Text length: {len(text) if text else 0}")
                
                # Try to find tickers pattern
                import re
                matches = re.findall(r"([A-Za-zÀ-ÿ0-9\.\- ]{2,60}?)\s+(ON|PN|PNA|PNB|DR)\b(?:\s+NM|\s+N1|\s+N2)?", text or '', re.IGNORECASE)
                print(f"  Found {len(matches)} potential assets:")
                for m in matches[:5]:
                    print(f"    - {m}")
            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()
