#!/usr/bin/env python3
import zipfile
import pdfplumber

zip_path = '/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/resouces/inputNotasCorretagem/drive-download-20260216T170007Z-1-001.zip'
pdf_name = 'Clear 2018 10 Outubro - Notas Negociação Corretagem.pdf'

with zipfile.ZipFile(zip_path, 'r') as z:
    with z.open(pdf_name) as f:
        pdf = pdfplumber.open(f)
        page = pdf.pages[5]
        
        text = page.extract_text()
        
        # Count occurrences
        print("Buscar por ELETRO*:")
        print(f"  ELETROBRAS: {text.count('ELETROBRAS')}")
        print(f"  ELETROBLA (SEM S): {text.count('ELETROBLA')}")
        print(f"  Preco 21,50: {text.count('21,50')}")
        print(f"  Preco 25,15: {text.count('25,15')}")
        print(f"  RAIADROGASIL: {text.count('RAIADROGASIL')}")
        
        # Find lines with prices
        lines = text.split('\n')
        print("\nLinhas com 21, (preco 21,50):")
        for line in lines:
            if '21,' in line and len(line) < 150:
                print(f"  {line}")
                
        print("\nLinhas com 65, (preco 65,50):")
        for line in lines:
            if '65,' in line and len(line) < 150:
                print(f"  {line}")

