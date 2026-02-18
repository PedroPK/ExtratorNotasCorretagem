#!/usr/bin/env python3
"""
Script para gerar/atualizar mapeamento de ativos para tickers B3
Utiliza web scraping e heurísticas para encontrar tickers
"""

import re
import os
import sys
import json
try:
    import requests
except Exception:
    requests = None
from pathlib import Path
from typing import Dict, Optional
from config import get_config

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

        # Captura nomes multi-palavra seguidos de sufixo (ON, PN, PNA, PNB, DR)
        m = re.search(r"([A-Za-zÀ-ÿ0-9\.\- ]{2,80}?)\s+(ON|PN|PNA|PNB|DR)\b", name, re.IGNORECASE)
        if m:
            empresa = m.group(1).strip()
            tipo = m.group(2).upper()
            # Normaliza sufixo numérico
            if tipo == 'ON':
                sufixo = 3
            elif tipo == 'PN':
                # PN pode ter variações N1/N2; tenta inferir pelo texto
                if re.search(r'PN\s+N2', name, re.IGNORECASE) or re.search(r'PNA', name, re.IGNORECASE):
                    sufixo = 5
                else:
                    sufixo = 4
            elif tipo == 'PNA':
                sufixo = 5
            elif tipo == 'PNB':
                sufixo = 6
            else:
                sufixo = None
            return (empresa, tipo, sufixo)

        # Fallback: use the full tokenized first significant word as company
        parts = [p for p in re.split(r"[\s\-]+", name) if p]
        empresa = parts[0] if parts else name
        return (empresa, 'ON', 3)
    
    def generate_ticker_heuristic(self, empresa: str, tipo: str, sufixo: Optional[int]) -> Optional[str]:
        """
        Gera ticker usando heurísticas simples
        
        Regras:
        - Pegue as primeiras 4 letras da empresa (ou ajuste conforme caso especial)
        - Adicione sufixo (3=ON, 4/5=PN, etc)
        
        Exemplos:
        - "Embraer" + ON → "EMBR3"
        - "Suzano" + ON → "SUZB3"
        - "Ultrapar" + ON → "UGPA3"
        """
        if not sufixo:
            return None
        
        empresa_upper = empresa.upper()

        # Casos especiais conhecidos (principais companies da B3)
        especiais = {
            'EMBRAER': ('EMBR', 3),
            'ULTRAPAR': ('UGPA', 3),
            'SUZANO': ('SUZB', 3),
            'BRASKEN': ('BRKM', 5),
            'BRASKEM': ('BRKM', 5),
            'PETROBRAS': ('PETR', 3),
            'VALE': ('VALE', 3),
            'COSAN': ('CSAN', 3),
            'CESP': ('CESP', 6),
            'BANCO DO BRASIL': ('BBAS', 3),
            'B2W': ('BTOW', 3),
            'B2W DIGITAL': ('BTOW', 3),
            'BRADESPAR': ('BRAP', 4),
            'BRF': ('BRFS', 3),
            'CCR': ('CCRO', 3),
            'CEMIG': ('CMIG', 4),
            'CIELO': ('CIEL', 3),
            'COPEL': ('CPLE', 3),
            'CVC': ('CVCB', 3),
            'CVC BRASIL': ('CVCB', 3),
            'ECORODOVIAS': ('ECOR', 3),
            'ELETROBRAS': ('ELET', 3),
            'ENERGIAS': ('ENER', 3),
            'FLEURY': ('FLRY', 3),
            'FORJA TAURUS': ('FORJ', 3),
            'GERDAU': ('GGBR', 4),
            'GERDAU MET': ('GOAU', 4),
            'GOL': ('GOLL', 4),
            'HYPERA': ('HYPE', 3),
            'JBS': ('JBSS', 3),
            'KROTON': ('KROT', 3),
            'LOG COM PROP': ('LOGG', 3),
            'LOJAS RENNER': ('LREN', 3),
            'MAGAZ LUIZA': ('MGLU', 3),
            'MARFRIG': ('MBRF', 3),
            'MRV': ('MRVE', 3),
            'QUALICORP': ('QUAL', 3),
            'RAIADROGASIL': ('RADL', 3),
            'SABESP': ('SBSP', 3),
            'SID NACIONAL': ('CSNA', 3),
            'SMILES': ('SMIL', 3),
            'TELEF BRASIL': ('VIVT', 3),
            'VIAVAREJO': ('VIAV', 3),
            'USIMINAS': ('USIM', 3),
            'ALUPAR': ('ALUP', 3),
            'AMBEV': ('ABEV', 3),
            'ITAÚ': ('ITUB', 4),
            'ITAÚSA': ('ITSA', 4),
            'NATURA': ('NTCO', 4),
            'ODONTOPREV': ('ODNT', 3),
        }
        
        # Tenta encontrar nos especiais
        for empresa_chave, (prefixo, sufixo_correto) in especiais.items():
            if empresa_upper.startswith(empresa_chave.split()[0]):
                return f"{prefixo}{sufixo_correto}"
        
        # Heurística: construir prefixo a partir das palavras significativas
        # Remove palavras genéricas
        stopwords = {'DO', 'DA', 'DE', 'E', 'S', 'A', 'SA', 'S/A', 'ON', 'PN', 'PNA', 'PNB', 'DR', 'NM', 'N1', 'N2'}
        words = [w for w in re.split(r"\s+", empresa_upper) if w and w not in stopwords]
        join = ''.join(words)
        if not join:
            join = re.sub(r'[^A-Z0-9]', '', empresa_upper)
        prefixo = (join[:4] if len(join) >= 4 else (join.ljust(4, 'X')))
        return f"{prefixo}{sufixo}"
    
    def search_b3_api(self, empresa: str) -> Optional[str]:
        """
        Tenta buscar ticker via API pública ou web scraping da B3
        
        TODO: Implementar integração com:
        - B3 Dados (https://www.b3.com.br)
        - Yahoo Finance Brasil
        - Fundamentus
        """
        empresa_q = empresa.strip()
        if not empresa_q:
            return None

        if requests is None:
            return None

        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; ExtratorNotas/1.0; +https://github.com/pedropk)'
        }

        # 1) Tentar Yahoo Finance search API
        try:
            q = requests.utils.requote_uri(empresa_q)
            url = f'https://query2.finance.yahoo.com/v1/finance/search?q={q}&quotesCount=10&newsCount=0'
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    quotes = data.get('quotes', [])
                    for item in quotes:
                        symbol = item.get('symbol', '')
                        exch = item.get('exchange', '')
                        if symbol.endswith('.SA'):
                            return symbol.replace('.SA', '')
                        if exch and 'SA' in exch.upper() and re.search(r'[A-Z]{1,5}\d', symbol):
                            return symbol
                except Exception:
                    pass
        except Exception:
            pass

        # 2) Tentar Fundamentus
        try:
            f_q = requests.utils.requote_uri(empresa_q)
            funda_url = f'https://fundamentus.com.br/busca.php?search={f_q}'
            r = requests.get(funda_url, headers=headers, timeout=8)
            if r.status_code == 200 and 'html' in r.headers.get('Content-Type', ''):
                m = re.search(r'([A-Z]{3,5}\d)', r.text)
                if m:
                    return m.group(1)
        except Exception:
            pass

        return None
    
    def load_existing_mapping(self):
        """Carrega mapeamento existente do arquivo e normaliza tickers"""
        if os.path.exists(self.mapping_file):
            try:
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            desc, ticker = line.split('=', 1)
                            desc = desc.strip()
                            ticker = ticker.strip()
                            # Normaliza ticker ao carregar
                            ticker = self._normalize_ticker(ticker, desc)
                            self.mapping[desc] = ticker
                print(f"✓ Carregados {len(self.mapping)} mapeamentos existentes")
            except Exception as e:
                print(f"⚠️  Erro ao carregar tickerMapping.properties: {str(e)}")
    
    def _normalize_ticker(self, ticker: str, asset_description: str) -> str:
        """
        Normaliza ticker aplicando regras B3:
        1. Remove sufixo F (mercado fracionário)
        2. ON deve terminar em 3; se terminar em 4, corrige
        3. PN deve terminar em 4; se terminar em 3, corrige
        
        Args:
            ticker: Ticker B3 original
            asset_description: Descrição do ativo (usado para detectar ON/PN)
        
        Returns:
            Ticker normalizado
        """
        if not ticker:
            return ticker
        
        # Remove F do final (fracionário)
        if ticker.endswith('F'):
            ticker = ticker[:-1]
        
        # Detecta tipo (ON, PN) da descrição
        desc_upper = asset_description.upper()
        is_on = ' ON' in desc_upper
        is_pn = ' PN' in desc_upper
        
        # ON deve terminar em 3
        if is_on and ticker.endswith('4'):
            ticker = ticker[:-1] + '3'
        
        # PN deve terminar em 4; se terminar em 3, corrige
        if is_pn and ticker.endswith('3'):
            ticker = ticker[:-1] + '4'
        
        return ticker
    
    
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
        4. Normaliza ticker (remove F, corrige ON/PN)
        """
        # 1. Verifica cache
        if asset_description in self.mapping:
            return self.mapping[asset_description]
        
        # 2. Parseia nome
        empresa, tipo, sufixo = self.parse_asset_name(asset_description)
        
        # 3. Tenta web scraping
        ticker = self.search_b3_api(empresa)
        
        # 4. USA heurística como fallback
        if not ticker:
            ticker = self.generate_ticker_heuristic(empresa, tipo, sufixo)
        
        # 5. Normaliza ticker
        if ticker:
            ticker = self._normalize_ticker(ticker, asset_description)
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
    import argparse

    print("\n🚀 Gerador de Mapeamento de Tickers B3\n")

    parser = argparse.ArgumentParser(description='Gerador de mapeamento de tickers')
    parser.add_argument('--from-pdf', action='store_true', help='Coleta descrições a partir das Notas (PDFs) antes de gerar o mapping')
    parser.add_argument('--year', '-y', type=int, default=None, help='Filtrar por ano ao coletar descrições das Notas')
    parser.add_argument('--output', '-o', type=str, default=None, help='Arquivo de saída (opcional)')
    args = parser.parse_args()

    mapper = TickerMapper()

    if args.from_pdf:
        # Importa coletor reutilizável
        try:
            src_dir = os.path.dirname(__file__)
            if src_dir not in sys.path:
                sys.path.insert(0, src_dir)
            from collect_asset_descriptions import collect_descriptions_from_path
        except Exception:
            print('✗ Não foi possível importar collect_asset_descriptions.')
            print('  Dica: instale dependências com: python3 -m pip install -r resouces/requirements.txt')
            sys.exit(1)
        print(f"📄 Coletando descrições a partir das Notas (ano={args.year})...")

        # Verifica dependências essenciais
        try:
            import pdfplumber  # type: ignore
        except Exception:
            print('✗ Dependência ausente: pdfplumber.')
            sys.exit(1)
        try:
            descricoes = collect_descriptions_from_path(year=args.year)
        except Exception as e:
            print(f"✗ Erro ao coletar descrições: {e}")
            sys.exit(1)

        if not descricoes:
            print('⚠️  Nenhuma descrição encontrada nas Notas para o filtro especificado')
            sys.exit(0)

        # Gera mapeamento
        mapper.generate_from_pdf_descriptions(descricoes)

        # Salva descrições coletadas
        if args.output:
            out = args.output
        else:
            cfg = get_config()
            outfolder = cfg.resolve_path('resouces')
            os.makedirs(outfolder, exist_ok=True)
            out = os.path.join(outfolder, f"ticker_candidates_{args.year or 'all'}.txt")

        with open(out, 'w', encoding='utf-8') as f:
            for d in descricoes:
                f.write(d + '\n')

        print(f"✓ Descrições salvas em: {out}")
        return

    # Default: exemplos embutidos
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


if __name__ == '__main__':
    main()
