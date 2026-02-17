#!/usr/bin/env python3
"""Dump textual samples of PDF pages to resouces/output/samples/ for inspection.

Usage: scripts/dump_pdf_samples.py [--year YEAR] [--pages N]
"""
import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from config import get_config


def dump_samples(year=None, pages=3):
    cfg = get_config()
    input_folder = cfg.resolve_path(cfg.get_input_folder())
    out_root = cfg.resolve_path(cfg.get_output_folder())
    samples_dir = os.path.join(out_root, 'samples')
    os.makedirs(samples_dir, exist_ok=True)

    pdf_files = [f for f in os.listdir(input_folder) if f.endswith('.pdf')]
    if not pdf_files:
        print('No PDFs found in', input_folder)
        return 0

    count = 0
    for fname in pdf_files:
        if year is not None:
            import re
            m = re.search(r"\b(19|20)\d{2}\b", fname)
            if not m or int(m.group(0)) != year:
                continue

        path = os.path.join(input_folder, fname)
        safe_name = fname.replace(' ', '_').replace('/', '_')
        try:
            import pdfplumber
        except Exception as e:
            print('pdfplumber not available:', e)
            return count

        try:
            # try with configured password if needed
            pwd = cfg.get_pdf_password() or ''
            with pdfplumber.open(path, password=pwd) as pdf:
                for i, page in enumerate(pdf.pages[:pages], 1):
                    text = page.extract_text() or ''
                    out_file = os.path.join(samples_dir, f"{safe_name}_page{i}.txt")
                    with open(out_file, 'w', encoding='utf-8') as f:
                        f.write(text)
                    count += 1
        except Exception as e:
            # write error note
            errfile = os.path.join(samples_dir, f"{safe_name}.error.txt")
            with open(errfile, 'w', encoding='utf-8') as ef:
                ef.write(str(e))
            continue

    print(f"✓ Samples written: {count} files to {samples_dir}")
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--year', '-y', type=int, default=None)
    parser.add_argument('--pages', '-p', type=int, default=3, help='Pages per PDF to dump')
    args = parser.parse_args()
    dump_samples(year=args.year, pages=args.pages)


if __name__ == '__main__':
    main()
