#!/usr/bin/env python3
"""
Script para corrigir mapeamentos incorretos de 'V FRACIONARIO'.

A operação 'V FRACIONARIO' apenas indica modo fracionário, não é um ticker.
Este script:
1. Identifica entradas com "V FRACIONARIO"
2. Extrai o ativo base
3. Substitui pela entrada correta (sem o prefixo)
4. Remove duplicatas
"""

import re

mapping_file = "/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/resouces/tickerMapping.properties"

# Ler arquivo
with open(mapping_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Processar linhas
fixed_lines = []
seen_keys = {}  # Para rastrear duplicatas
removed_fracionario = []

for line in lines:
    line = line.rstrip('\n')
    
    # Manter comentários e linhas vazias
    if line.startswith('#') or not line.strip():
        fixed_lines.append(line)
        continue
    
    # Processar entradas de mapeamento
    if '=' in line:
        key, value = line.split('=', 1)
        
        # Se tem "V FRACIONARIO", extrair o ativo base
        if 'V FRACIONARIO' in key.upper():
            # Remover "V FRACIONARIO " do início
            base_key = re.sub(r'^V\s+FRACIONARIO\s+', '', key, flags=re.IGNORECASE).strip()
            
            # Procurar o mapeamento do ativo base
            found_base = False
            for seen_key in seen_keys:
                if seen_key.upper() == base_key.upper():
                    # Usar o ticker do ativo base (ignorar o valor V FRACIONARIO)
                    ticker = seen_keys[seen_key]
                    removed_fracionario.append(f"{key} → {base_key}={ticker}")
                    found_base = True
                    break
            
            # Se não encontrou ainda, pode estar adiante. Será tratado na segunda passagem.
            if not found_base:
                removed_fracionario.append(f"{key} → DESCARTAR (não encontrou ativo base ainda)")
            continue
        
        # Manter apenas a primeira ocorrência de cada chave
        if key.upper() not in [k.upper() for k in seen_keys.keys()]:
            seen_keys[key] = value
            fixed_lines.append(line)
        else:
            # Duplicata, ignorar
            pass
    else:
        fixed_lines.append(line)

# Segunda passagem: processar linhas com "V FRACIONARIO" novamente
# tentando encontrar o ativo base
final_lines = []
seen_keys_final = {}

for line in fixed_lines:
    if line.startswith('#') or not line.strip():
        final_lines.append(line)
        continue
    
    if '=' in line:
        key, value = line.split('=', 1)
        
        if 'V FRACIONARIO' in key.upper():
            # Extrair ativo base
            base_key = re.sub(r'^V\s+FRACIONARIO\s+', '', key, flags=re.IGNORECASE).strip()
            
            # Procurar na lista final
            found = False
            for final_key, final_value in seen_keys_final.items():
                if final_key.upper() == base_key.upper():
                    # Encontrou! Usar o ticker base
                    print(f"✓ Mapeado: {key} → {base_key}={final_value}")
                    final_lines.append(f"{base_key}={final_value}")
                    found = True
                    break
            
            if not found:
                # Ainda não encontrou, será obtido em futuro processamento
                print(f"? Aguardando: {key} (ativo base: {base_key})")
        else:
            key_upper = key.upper()
            if key_upper not in [k.upper() for k in seen_keys_final.keys()]:
                seen_keys_final[key] = value
                final_lines.append(line)

# Salvar resultado
output = '\n'.join(final_lines)
if output and not output.endswith('\n'):
    output += '\n'

print(f"\n=== RESUMO ===")
print(f"Entradas 'V FRACIONARIO' encontradas e processadas:")
for item in removed_fracionario[:10]:  # Mostrar primeiras 10
    print(f"  {item}")
if len(removed_fracionario) > 10:
    print(f"  ... e mais {len(removed_fracionario) - 10}")

print(f"\nTotal de linhas (antes): {len([l for l in lines if '=' in l])}")
print(f"Total de linhas (depois): {len([l for l in final_lines if '=' in l])}")

with open(mapping_file, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"\n✓ Arquivo atualizado: {mapping_file}")
