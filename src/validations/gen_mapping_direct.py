#!/usr/bin/env python3
"""
Gera mapeamento direto do arquivo limpo de descrições.
"""
import sys
import os
sys.path.insert(0, '/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/src')

# Mudar diretório para resouces para que o arquivo seja criado no lugar certo
os.chdir('/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem')

from gerar_ticker_mapping import TickerMapper

# Ler descrições do arquivo limpo
clean_file = 'resouces/all_descriptions_clean.txt'

print(f"\n🔍 GERANDO MAPEAMENTO DE TICKERS (arquivo limpo)\n")
print(f"Lendo: {clean_file}\n")

descriptions = []
with open(clean_file, 'r', encoding='utf-8') as f:
    descriptions = [line.strip() for line in f if line.strip()]

print(f"✓ Carregadas {len(descriptions)} descrições únicas\n")

# Gerar mapeamento
mapper = TickerMapper()
mapper.generate_from_pdf_descriptions(descriptions)

print(f"✓ Mapeamento concluído!")
