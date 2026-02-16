#!/usr/bin/env python3
"""
Script para gerar/atualizar mapeamento de ativos para tickers B3
Utiliza web scraping e heurísticas para encontrar tickers
"""

import re
import os
from pathlib import Path
from typing import Dict, Optional

class TickerMapper:
    """Mapeia descrições de ativos para tickers B3"""
    
    def __init__(self):
        self.mapping = {}
        self.mapping_file = 'resouces/tickerMapping.properties'
        
    def parse_asset_name(self, asset_name: str) -> tuple:
        """
        Parse nome do ativo para extrair empresa e tipo
        
        Exemplos:
        - "Embraer ON NM" → ("Embraer", "ON")
        - "Suzano ON NM" → ("Suzano", "ON")
        - "Brasken PNA N1" → ("Brasken", "PN")
        """
        # Remove extra spaces
        name = asset_name.strip()
        
        # Procura por padrões conhecidos
        patterns = {
            r'(\w+)\s+ON\s+NM': ('ON', 3),  # ON (Ordinária) = sufixo 3
            r'(\w+)\s+PN\s+N1': ('PN', 4),  # PN (Preferencial) = sufixo 4 ou 5
            r'(\w+)\s+PN\s+N2': ('PN', 5),
            r'(\w+)\s+PNA': ('PN', 5),
            r'(\w+)\s+PNB': ('PN', 6),
            r'(\w+)\s+DR': ('DR', None),    # ADR/DR (não tem sufixo padrão)
        }
        
        for pattern, (tipo, sufixo) in patterns.items():
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                empresa = match.group(1)
                return (empresa, tipo, sufixo)
        
        # Fallback: assume ON e extrai primeira palavra
        empresa = name.split()[0]
        return (empresa, 'ON', 3)
    
    def generate_ticker_heuristic(self, empresa: str, tipo: str, sufixo: Optional[int]) -> Optional[str]:
        """
        Gera ticker usando heurísticas simples
        
        Regras:
        - Pegue as primeiras 4 letras (ou 5) da empresa
        - Adicione sufixo (3=ON, 4/5=PN, etc)
        
        Exemplos:
        - "Embraer" + ON → "EMBR3"
        - "Suzano" + ON → "SUZB3"
        - "Ultrap" + ON → "UGPA3"
        """
        if not sufixo:
            return None
        
        empresa_upper = empresa.upper()
        
        # Alguns casos especiais conhecidos
        especiais = {
            'EMBRAER': ('EMBR', 3),
            'ULTRAPAR': ('UGPA', 3),
            'SUZANO': ('SUZB', 3),
            'BRASKEN': ('BRKM', 5),
            'PETROBRAS': ('PETR', 3),
            'VALE': ('VALE', 3),
            'COSAN': ('CSAN', 3),
            'CESP': ('CESP', 6),
            'BANCO DO BRASIL': ('BBAS', 3),
        }
        
        # Tenta encontrar nos especiais
        for empresa_chave, (prefixo, sufixo_correto) in especiais.items():
            if empresa_upper.startswith(empresa_chave.split()[0]):
                return f"{prefixo}{sufixo_correto}"
        
        # Heurística: primeiras 4 letras + sufixo
        prefixo = empresa_upper[:4]
        return f"{prefixo}{sufixo}"
    
    def search_b3_api(self, empresa: str) -> Optional[str]:
        """
        Tenta buscar ticker via API pública ou web scraping da B3
        
        TODO: Implementar integração com:
        - B3 Dados (https://www.b3.com.br)
        - Yahoo Finance Brasil
        - Fundamentus
        """
        # Atualmente apenas retorna None - implementar no futuro
        return None
    
    def load_existing_mapping(self):
        """Carrega mapeamento existente do arquivo"""
        if os.path.exists(self.mapping_file):
            try:
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            desc, ticker = line.split('=', 1)
                            self.mapping[desc.strip()] = ticker.strip()
                print(f"✓ Carregados {len(self.mapping)} mapeamentos existentes")
            except Exception as e:
                print(f"⚠️  Erro ao carregar tickerMapping.properties: {str(e)}")
    
    def save_mapping(self):
        """Salva mapeamento em arquivo"""
        try:
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                f.write("# Mapeamento de Descrições de Ativos para Tickers B3\n")
                f.write("# Formato: DESCRICAO_DO_ATIVO=TICKER\n")
                f.write("#\n")
                f.write("# Este arquivo é gerado/atualizado automaticamente pelo script gerar_ticker_mapping.py\n")
                f.write("# Você pode editar manualmente para corrigir mapeamentos incorretos\n\n")
                
                for desc, ticker in sorted(self.mapping.items()):
                    f.write(f"{desc}={ticker}\n")
            
            print(f"✓ Salvos {len(self.mapping)} mapeamentos em {self.mapping_file}")
        except Exception as e:
            print(f"✗ Erro ao salvar tickerMapping.properties: {str(e)}")
    
    def map_asset(self, asset_description: str) -> Optional[str]:
        """
        Mapeia descrição de ativo para ticker B3
        
        Estratégia:
        1. Verifica se já existe no mapeamento
        2. Tenta buscar via web scraping
        3. Usa heurística como fallback
        """
        # 1. Verifica cache
        if asset_description in self.mapping:
            return self.mapping[asset_description]
        
        # 2. Parseia nome
        empresa, tipo, sufixo = self.parse_asset_name(asset_description)
        
        # 3. Tenta web scraping (futuro)
        ticker = self.search_b3_api(empresa)
        
        # 4. USA heurística como fallback
        if not ticker:
            ticker = self.generate_ticker_heuristic(empresa, tipo, sufixo)
        
        if ticker:
            self.mapping[asset_description] = ticker
            print(f"  ✓ {asset_description:30} → {ticker}")
            return ticker
        
        print(f"  ✗ {asset_description:30} → NÃO MAPEADO")
        return None
    
    def generate_from_pdf_descriptions(self, descriptions: list):
        """
        Gera mapeamento a partir de lista de descrições extraídas de PDFs
        
        Args:
            descriptions: List de descrições de ativos extraídas dos PDFs
        """
        print("\n" + "="*70)
        print("🔍 GERANDO MAPEAMENTO DE TICKERS")
        print("="*70 + "\n")
        
        self.load_existing_mapping()
        
        print(f"\n📊 Processando {len(descriptions)} ativos únicos:\n")
        
        for desc in sorted(set(descriptions)):
            self.map_asset(desc)
        
        self.save_mapping()
        
        print("\n" + "="*70)
        print(f"✅ Mapeamento atualizado!")
        print(f"   Total de ativos mapeados: {len(self.mapping)}")
        print(f"   Arquivo: {self.mapping_file}")
        print("="*70 + "\n")


def main():
    """Script principal"""
    import sys
    
    print("\n🚀 Gerador de Mapeamento de Tickers B3\n")
    
    mapper = TickerMapper()
    
    # Exemplos de teste
    exemplos = [
        "Embraer ON NM",
        "Ultrapar ON NM",
        "Suzano ON NM",
        "Brasken PNA N1",
        "Vale ON NM",
        "Petrobras ON",
        "Cosan ON NM",
    ]
    
    mapper.generate_from_pdf_descriptions(exemplos)
    
    # Opcionalmente, pode fornecer lista de ativos
    if len(sys.argv) > 1:
        if sys.argv[1] == '--from-pdf':
            # TODO: Extrair ativos de PDFs e gerar mapeamento
            print("📄 Modo: Extrair ativos de PDFs e gerar mapeamento")
            print("   (Será implementado quando integrado com extratorNotasCorretagem.py)")


if __name__ == '__main__':
    main()
