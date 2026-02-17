#!/usr/bin/env python3
"""Extrai descrições diretamente dos PDFs (texto puro) e gera o tickerMapping.properties

Uso: scripts/run_map_from_pdfs.py [--year YEAR]
"""
import re
import os
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from config import get_config
from gerar_ticker_mapping import TickerMapper


def extract_from_pdf_path(path, senha=None):
    import pdfplumber
    descs = set()
    try:
        with pdfplumber.open(path, password=senha or '') as pdf:
            for page in pdf.pages:
                txt = page.extract_text() or ''
                for m in re.finditer(r"([A-Za-zÀ-ÿ0-9\.\- ]{2,60}?)\s+(ON|PN|PNA|PNB|DR)\b(?:\s+NM|\s+N1|\s+N2)?", txt, re.IGNORECASE):
                    descs.add(m.group(0).strip())
    except Exception:
        return set()
    return descs


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--year', '-y', type=int, default=None)
    args = parser.parse_args()

    cfg = get_config()
    input_folder = cfg.resolve_path(cfg.get_input_folder())
    senha = cfg.get_pdf_password()

    if not os.path.exists(input_folder):
        print('Input folder not found:', input_folder)
        sys.exit(1)

    all_descs = set()

    # PDFs in folder
    for f in os.listdir(input_folder):
        if not f.endswith('.pdf'):
            continue
        if args.year is not None:
            m = re.search(r'\b(19|20)\d{2}\b', f)
            if not m or int(m.group(0)) != args.year:
                continue
        p = os.path.join(input_folder, f)
        ds = extract_from_pdf_path(p, senha=senha)
        all_descs.update(ds)

    # PDFs inside zips
    for zf in [x for x in os.listdir(input_folder) if x.endswith('.zip')]:
        try:
            with zipfile.ZipFile(os.path.join(input_folder, zf), 'r') as z:
                for entry in z.namelist():
                    if not entry.endswith('.pdf'):
                        continue
                    if args.year is not None:
                        m = re.search(r'\b(19|20)\d{2}\b', entry)
                        if not m or int(m.group(0)) != args.year:
                            continue
                    with z.open(entry) as ef:
                        # write to temp file? pdfplumber can open bytes via BytesIO
                        from io import BytesIO
                        data = ef.read()
                        try:
                            import pdfplumber
                            with pdfplumber.open(BytesIO(data), password=senha or '') as pdf:
                                for page in pdf.pages:
                                    txt = page.extract_text() or ''
                                    for m in re.finditer(r"([A-Za-zÀ-ÿ0-9\.\- ]{2,60}?)\s+(ON|PN|PNA|PNB|DR)\b(?:\s+NM|\s+N1|\s+N2)?", txt, re.IGNORECASE):
                                        all_descs.add(m.group(0).strip())
                        except Exception:
                            continue
        except Exception:
            continue

    print(f'✓ Encontradas {len(all_descs)} descrições únicas')
    for d in sorted(all_descs)[:50]:
        print('-', d)

    if not all_descs:
        print('Nenhuma descrição encontrada; verifique PDFs ou passe outro ano com --year')
        return

    mapper = TickerMapper()
    mapper.generate_from_pdf_descriptions(sorted(all_descs))


if __name__ == '__main__':
    main()
