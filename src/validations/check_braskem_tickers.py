#!/usr/bin/env python3
"""
Procura informações sobre os tickers BRKM3, BRKM4, BRKM5 para determinar 
qual mapeamento está correto
"""
import sys
sys.path.insert(0, '/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/src')

from gerar_ticker_mapping import TickerMapper

mapper = TickerMapper()

# Testa o que o web scraping encontra para BRASKEM
test_companies = ['BRASKEM', 'BRASKEM ON', 'BRASKEM PN', 'BRASKEM PNA']

print("=" * 80)
print("TESTANDO WEB SCRAPING PARA BRASKEM")
print("=" * 80)

for company in test_companies:
    print(f"\nBuscando: {company}")
    
    # Tenta B3 API
    ticker_b3 = mapper.search_b3_api(company)
    if ticker_b3:
        print(f"  B3 API: {ticker_b3}")
    
    # Tenta heurística
    ticker_heur = mapper.generate_ticker_heuristic(company, 'ON', '')
    if ticker_heur:
        print(f"  Heurística: {ticker_heur}")
