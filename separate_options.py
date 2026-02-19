#!/usr/bin/env python3
"""Separa opções de ativos normais no mapeamento de tickers"""

import re

# Padrão de opções
OPTION_PATTERN = r'^[A-Z0-9]{3,5}[A-Z]\d{3}E?$'

mapping_file = 'resouces/tickerMapping.properties'
options_file = 'resouces/tickerMapping_options.properties'

normal_entries = []
option_entries = []

# Lê arquivo
with open(mapping_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Separa cabeçalho e dados
header_lines = []
data_lines = []
header_complete = False

for line in lines:
    if not header_complete and line.strip().startswith('#'):
        header_lines.append(line)
    elif not header_complete and (not line.strip() or line.startswith('\n')):
        header_complete = True
    elif header_complete and line.strip():
        data_lines.append(line)

# Processa linhas de dados
for line in data_lines:
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    if '=' in line:
        desc, ticker = line.split('=', 1)
        desc = desc.strip()
        
        # Remove sufixos ON/PN/etc para detectar corretamente opções
        desc_base = re.sub(r'\s+(ON|PN|PNA|PNB|DR)\s*$', '', desc, flags=re.IGNORECASE)
        
        # Detecta se é opção
        if re.match(OPTION_PATTERN, desc_base):
            option_entries.append((desc, ticker.strip()))
        else:
            normal_entries.append((desc, ticker.strip()))

# Salva arquivo normal
with open(mapping_file, 'w', encoding='utf-8') as f:
    f.write("# Mapeamento de Descrições de Ativos para Tickers B3\n")
    f.write("# Formato: DESCRICAO_DO_ATIVO=TICKER\n")
    f.write("#\n")
    f.write("# Este arquivo é gerado/atualizado automaticamente pelo script gerar_ticker_mapping.py\n")
    f.write("# Você pode editar manualmente para corrigir mapeamentos incorretos\n")
    f.write("# Nota: Opções são armazenadas em tickerMapping_options.properties\n\n")
    
    for desc, ticker in sorted(normal_entries):
        f.write(f"{desc}={ticker}\n")

# Salva arquivo de opções
if option_entries:
    with open(options_file, 'w', encoding='utf-8') as f:
        f.write("# Mapeamento de Opções para Tickers B3\n")
        f.write("# Formato: OPCAO_DESCRICAO=TICKER\n")
        f.write("#\n")
        f.write("# Opções = Contrato futuro de ativos\n")
        f.write("# Padrão: [TICKER_BASE][MES][PRECO][E?]\n")
        f.write("# Exemplos: ABEVA135, B3SAB725, BBASK344E\n")
        f.write("# Este arquivo é gerado/atualizado automaticamente pelo script gerar_ticker_mapping.py\n\n")
        
        for desc, ticker in sorted(option_entries):
            f.write(f"{desc}={ticker}\n")

print(f"✓ Separação concluída!")
print(f"  Normal: {len(normal_entries)} ativos")
print(f"  Opções: {len(option_entries)} contratos")
print(f"  Arquivo normal: {mapping_file}")
print(f"  Arquivo opções: {options_file}")
