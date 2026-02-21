#!/usr/bin/env python3
"""
Gera mapeamento de tickers a partir do arquivo limpo de descrições.
"""
import sys
sys.path.insert(0, '/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/src')

from gerar_ticker_mapping import TickerMapper

# Ler descrições do arquivo limpo
clean_file = '/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/resouces/all_descriptions_clean.txt'

print(f"📄 Lendo descrições de: {clean_file}\n")

descriptions = []
with open(clean_file, 'r', encoding='utf-8') as f:
    descriptions = [line.strip() for line in f if line.strip()]

print(f"✓ Carregadas {len(descriptions)} descrições\n")

# Gerar mapeamento
mapper = TickerMapper()
mapper.generate_from_pdf_descriptions(descriptions)
