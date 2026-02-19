#!/usr/bin/env python3
"""
Script para revisar mapeamentos manual de descrições não encontradas.

Fluxo:
1. Lê tickerMapping_unmapped.properties
2. Procura por linhas preenchidas (DESCRICAO=TICKER)
3. Move para tickerMapping.properties
4. Remove do arquivo de unmapped
5. Mostra resumo de ações realizadas
"""

import re
import os
from pathlib import Path


def review_unmapped_mappings():
    """Revisa arquivo de unmapped e importa mapeamentos preenchidos"""
    
    unmapped_file = 'resouces/tickerMapping_unmapped.properties'
    mapping_file = 'resouces/tickerMapping.properties'
    
    if not os.path.exists(unmapped_file):
        print(f"⚠️  Arquivo não encontrado: {unmapped_file}")
        print("   Execute gerar_ticker_mapping.py primeiro para gerar descrições não mapeadas.")
        return
    
    print("\n" + "=" * 70)
    print("📋 REVISANDO MAPEAMENTOS NÃO ENCONTRADOS")
    print("=" * 70 + "\n")
    
    # Lê arquivo de unmapped
    unmapped_entries = []
    rejected_entries = []
    
    try:
        with open(unmapped_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')
                
                # Ignora comentários e linhas vazias
                if not line or line.strip().startswith('#'):
                    rejected_entries.append(line)
                    continue
                
                # Procura por padrão DESCRICAO=TICKER
                if '=' in line:
                    desc, ticker = line.split('=', 1)
                    desc = desc.strip()
                    ticker = ticker.strip()
                    
                    # Se ticker foi preenchido (não está vazio)
                    if ticker:
                        unmapped_entries.append((desc, ticker))
                    else:
                        rejected_entries.append(line)
                else:
                    rejected_entries.append(line)
    except Exception as e:
        print(f"✗ Erro ao ler {unmapped_file}: {str(e)}")
        return
    
    if not unmapped_entries:
        print(f"ℹ️  Nenhum mapeamento preenchido encontrado em {unmapped_file}")
        print(f"   Total de linhas não preenchidas: {len(rejected_entries)}")
        return
    
    print(f"✓ Encontrados {len(unmapped_entries)} mapeamento(s) preenchido(s):\n")
    
    # Lê mapeamentos existentes
    existing_mapping = {}
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')
                if line and '=' in line and not line.startswith('#'):
                    desc, ticker = line.split('=', 1)
                    desc = desc.strip()
                    existing_mapping[desc] = ticker.strip()
    except Exception as e:
        print(f"✗ Erro ao ler {mapping_file}: {str(e)}")
        return
    
    # Importa novos mapeamentos
    imported_count = 0
    skipped_count = 0
    
    for desc, ticker in unmapped_entries:
        if desc in existing_mapping:
            existing_ticker = existing_mapping[desc]
            if existing_ticker == ticker:
                print(f"  ⏭️  {desc:30} → {ticker} (já existe)")
                skipped_count += 1
            else:
                print(f"  ⚠️  {desc:30} → {ticker} (conflita com {existing_ticker}, mantendo {existing_ticker})")
                skipped_count += 1
        else:
            print(f"  ✓ {desc:30} → {ticker}")
            existing_mapping[desc] = ticker
            imported_count += 1
    
    # Se importou algo, atualiza o arquivo
    if imported_count > 0:
        print(f"\n{'=' * 70}")
        print(f"💾 Salvando {imported_count} novo(s) mapeamento(s)...")
        print(f"{'=' * 70}\n")
        
        try:
            # Salva com cabeçalho original
            with open(mapping_file, 'w', encoding='utf-8') as f:
                f.write("# Mapeamento de Descrições de Ativos para Tickers B3\n")
                f.write("# Formato: DESCRICAO_DO_ATIVO=TICKER\n")
                f.write("#\n")
                f.write("# Este arquivo é gerado/atualizado automaticamente pelo script gerar_ticker_mapping.py\n")
                f.write("# Você pode editar manualmente para corrigir mapeamentos incorretos\n")
                f.write("# Nota: Opções são armazenadas em tickerMapping_options.properties\n\n")
                
                for desc, ticker in sorted(existing_mapping.items()):
                    f.write(f"{desc}={ticker}\n")
            
            print(f"✓ {mapping_file} atualizado com sucesso")
        except Exception as e:
            print(f"✗ Erro ao salvar {mapping_file}: {str(e)}")
            return
    
    # Atualiza arquivo de unmapped removendo os importados
    if imported_count > 0:
        print(f"🗑️  Removendo {imported_count} mapeamento(s) do arquivo de unmapped...\n")
        
        try:
            with open(unmapped_file, 'w', encoding='utf-8') as f:
                f.write("# Descrições não mapeadas - PARA REVISÃO MANUAL\n")
                f.write("# Formato: DESRICAO_DO_ATIVO=TICKER_DESEJADO\n")
                f.write("#\n")
                f.write("# Instruções:\n")
                f.write("# 1. Preencha o TICKER_DESEJADO para as descrições que você conhece\n")
                f.write("# 2. Deixe em branco (ou comente com #) as que você não conhece\n")
                f.write("# 3. Execute: python3 review_unmapped_mappings.py\n")
                f.write("# 4. O script moverá os mapeamentos preenchidos para o arquivo padrão\n")
                f.write("# 5. Este arquivo será regenerado na próxima execução com novos não mapeados\n\n")
                
                # Re-escreve linhas rejeitadas (comentadas e vazias)
                for line in rejected_entries:
                    f.write(line + '\n')
            
            print(f"✓ {unmapped_file} limpo")
        except Exception as e:
            print(f"✗ Erro ao atualizar {unmapped_file}: {str(e)}")
            return
    
    # Resumo final
    print("\n" + "=" * 70)
    print("📊 RESUMO")
    print("=" * 70)
    print(f"✓ Mapeamentos importados: {imported_count}")
    print(f"⏭️  Mapeamentos ignorados: {skipped_count}")
    print(f"   Total no arquivo padrão agora: {len(existing_mapping)}")
    print("=" * 70 + "\n")
    
    if imported_count == 0:
        print(f"ℹ️  Nenhuma atualização foi necessária.")
    else:
        print(f"✅ Revisão concluída com sucesso!")
        print(f"   Execute novamente gerar_ticker_mapping.py para processar novos não mapeados.\n")


if __name__ == '__main__':
    review_unmapped_mappings()
