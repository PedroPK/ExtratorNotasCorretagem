#!/usr/bin/env python3
import re

# REGEX CORRIGIDO: adiciona 0-9 para capturar dígitos nos nomes de ativos
pattern_old = r'1-BOVESPA\s+([CV])\s+(\w+)\s+(\d{2}/\d{2})\s+([A-Z\s]+?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s+([DC])'
pattern_new = r'1-BOVESPA\s+([CV])\s+(\w+)\s+(\d{2}/\d{2})\s+([A-Z0-9\s]+?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s+([DC])'

test_lines = [
    "1-BOVESPA C FRACIONARIO 01/00 B2W DIGITAL ON NM 2 28,90 57,80 D",
    "1-BOVESPA V FRACIONARIO 01/00 BRASKEM PNA N1 1 56,50 56,50 C",
    "1-BOVESPA C FRACIONARIO 01/00 FLEURY ON NM 1 21,25 21,25 D"
]

print("="*100)
print("REGEX ANTIGO (BUGADO):")
print("="*100)
print(f"Pattern: ...([A-Z\\s]+?)...\n")

for line in test_lines:
    print(f"Teste: {line}")
    match = re.search(pattern_old, line, re.IGNORECASE)
    if match:
        print(f"  ✓ ENCONTRADO! Ativo: {match.group(4)}")
    else:
        print(f"  ✗ NÃO ENCONTRADO")
    print()

print("="*100)
print("REGEX NOVO (CORRIGIDO):")
print("="*100)
print(f"Pattern: ...([A-Z0-9\\s]+?)...\n")

for line in test_lines:
    print(f"Teste: {line}")
    match = re.search(pattern_new, line, re.IGNORECASE)
    if match:
        print(f"  ✓ ENCONTRADO! Ativo: {match.group(4)}")
    else:
        print(f"  ✗ NÃO ENCONTRADO")
    print()
