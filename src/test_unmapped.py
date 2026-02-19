#!/usr/bin/env python3
"""Teste do sistema de unmapped mappings"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from gerar_ticker_mapping import TickerMapper

# Cria mapeador customizado para teste (desabilita heurística)
class TestTickerMapper(TickerMapper):
    def generate_ticker_heuristic(self, empresa, tipo, sufixo):
        """Override: desabilita heurística para teste do sistema unmapped"""
        # Retorna None para desabilitar completamente
        return None

# Usa mapeador de teste
mapper = TestTickerMapper()

# Carrega mapeamentos existentes
mapper.load_existing_mapping()

# Lista de descrições para testar (inclui algumas que não existem)
test_descriptions = [
    "BANCO DO BRASIL ON",           # Existente
    "FLEURY ON",                     # Existente
    "EMPRESA MUITO FICTICIA ON",     # NOVO - Não existe
    "SCRIPTO TESTE PN",              # NOVO - Não existe
    "OUTRA EMPRESA DESCONHECIDA ON", # NOVO - Não existe
]

print("\n" + "=" * 70)
print("🧪 TESTE: MAPEAMENTO COM UNMAPPED")
print("=" * 70 + "\n")

print(f"Processando {len(test_descriptions)} descrições:\n")

for desc in test_descriptions:
    mapper.map_asset(desc)
    print()

# Salva os arquivos
mapper.save_mapping()
mapper.save_options_mapping()
mapper.save_unmapped_mapping()

print("\n" + "=" * 70)
print("📊 RESUMO DO TESTE")
print("=" * 70)
print(f"✓ Total de ativos mapeados: {len(mapper.mapping)}")
print(f"✓ Total de não mapeados: {len(mapper.unmapped_mapping)}")
print("=" * 70 + "\n")

print("Arquivos de unmapped criados:")
unmapped_file = 'resouces/tickerMapping_unmapped.properties'
if os.path.exists(unmapped_file):
    print(f"  {unmapped_file}")
    print("\nConteúdo (primeiras 20 linhas):")
    with open(unmapped_file, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:20]):
            print(f"  {line.rstrip()}")
