#!/usr/bin/env python3
"""
Teste rápido para verificar se a fix no regex do _extract_operations_from_text
consegue extrair as 3 operações de 04/10/2018 do PDF
"""
import pdfplumber
import re
import sys
sys.path.insert(0, '/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/src')

from extratorNotasCorretagem import _extract_ticker_from_cells, _normalize_number
from config import get_config

# Carrega mapeamento
config = get_config()
ticker_mapping = config.get_ticker_mapping()

pdf_path = "/tmp/Clear 2018 10 Outubro - Notas Negociação Corretagem.pdf"

print("=" * 100)
print("TESTE DE EXTRAÇÃO COM REGEX CORRIGIDO")
print("=" * 100)

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[1]  # 04/10/2018
    texto = page.extract_text()
    data_pregao = "04/10/2018"
    
    # Novo regex (CORRIGIDO) com [A-Z0-9\s]
    pattern = r'1-BOVESPA\s+([CV])\s+(\w+)\s+(\d{2}/\d{2})\s+([A-Z0-9\s]+?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s+([DC])'
    
    operacoes_encontradas = []
    
    for match in re.finditer(pattern, texto, re.IGNORECASE):
        try:
            operacao_tipo = match.group(1).upper()
            ativo_nome = match.group(4).strip()
            qty_str = match.group(5)
            price_str = match.group(6)
            
            # Extrai ticker
            ticker = _extract_ticker_from_cells([ativo_nome], ticker_mapping)
            if not ticker:
                print(f"  ⚠️  Não conseguiu extrair ticker para: {ativo_nome}")
                continue
            
            quantidade = _normalize_number(qty_str)
            preco = _normalize_number(price_str)
            
            if not quantidade or not preco:
                continue
            
            operacoes_encontradas.append({
                "Ativo": ativo_nome,
                "Ticker": ticker,
                "Operação": operacao_tipo,
                "Quantidade": quantidade,
                "Preço": preco
            })
        except Exception as e:
            print(f"Erro ao processar: {e}")
            continue
    
    print(f"\n✅ Total de operações encontradas: {len(operacoes_encontradas)}\n")
    
    for i, op in enumerate(operacoes_encontradas, 1):
        print(f"{i}. {op['Ativo']:25} → {op['Ticker']:6} | {op['Operação']} | Qtd: {op['Quantidade']} | Preço: {op['Preço']}")
    
    # Verificação final
    print("\n" + "=" * 100)
    if len(operacoes_encontradas) == 3:
        print("✅ SUCESSO! As 3 operações foram extraídas corretamente!")
    else:
        print(f"❌ FALHA! Esperava 3 operações, mas encontrou {len(operacoes_encontradas)}")
