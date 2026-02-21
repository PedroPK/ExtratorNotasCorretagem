#!/usr/bin/env python3
"""Testa mapeamento das novas descrições com sufixos NM/N1"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from gerar_ticker_mapping import TickerMapper

mapper = TickerMapper()
mapper.load_existing_mapping()

# Testa as 3 descrições problemáticas
test_descriptions = [
    "B2W DIGITAL ON",
    "B2W DIGITAL ON NM",
    "BRASKEM PNA",
    "BRASKEM PNA N1",
    "FLEURY ON",
    "FLEURY ON NM",
]

print("=" * 70)
print("TESTE DE MAPEAMENTO COM FALLBACK NM/N1")
print("=" * 70)
print()

for desc in test_descriptions:
    ticker = mapper.map_asset(desc)
    print()

print("=" * 70)
print(f"Total de ativos em mapper.mapping: {len(mapper.mapping)}")
print("=" * 70)
print()
print("Mapeamentos das 6 descrições testadas:")
for desc in test_descriptions:
    ticker = mapper.mapping.get(desc, "NÃO ENCONTRADO")
    print(f"  {desc:30} → {ticker}")

