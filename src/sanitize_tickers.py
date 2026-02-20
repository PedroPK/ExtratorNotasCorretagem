#!/usr/bin/env python3
"""
Script para sanitizar e validar mapeamentos de tickers

Funcionalidades:
1. Valida regras de nomenclatura B3
2. Detecta exceções conhecidas e classes especiais
3. Modo --fix: Corrige automaticamente mapeamentos via web scraping
4. Modo --report: Gera relatório em CSV dos problemas encontrados

Valida regras de nomenclatura B3:
- Descrições terminando em ON → Ticker deve terminar em 3
- Descrições terminando em PN/PNA → Ticker deve terminar em 4/5
- Descrições terminando em PNB → Ticker deve terminar em 5
"""

import os
import re
import sys
import csv
from datetime import datetime
from collections import defaultdict

class TickerSanitizer:
    def __init__(self, mapping_file='resouces/tickerMapping.properties'):
        self.mapping_file = mapping_file
        self.mappings = {}
        self.issues = defaultdict(list)
        self.verified_tickers = {}  # Cache de tickers verificados
        self.fixed_entries = {}  # Entradas que foram corrigidas
        
        # Exceções conhecidas (tickers especiais que não seguem padrão)
        self.exceptions = {
            'BRASIL ON': 'EVEB31',  # FII ou classe especial
            'CESP ON': 'CESP6',  # Classe especial
            'CESP PNB': 'CESP6',
            'COELBA ON': 'CEEB5',  # Classe especial
            'TIM ON': '0P0001N5CL',  # ISIN/código alternativo
            'AZUL PN': '0P0000U99Z',  # ISIN/código alternativo
            'ABC BRASIL PN': 'ABCB4',  # Corrigido para 4 (PN)
            'JBS ON': 'JBSS3',  # Corrigido para 3 (ON)
            'EQUATORIAL ON': 'EQPA3',  # Corrigido para 3 (ON padrão)
            'UNIPAR ON': 'UNIP3',  # Corrigido para 3 (ON padrão)
        }
        
        self.load_mappings()
    
    def load_mappings(self):
        """Carrega mapeamentos do arquivo"""
        if os.path.exists(self.mapping_file):
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        desc, ticker = line.split('=', 1)
                        self.mappings[desc.strip()] = ticker.strip()
    
    def verify_ticker_with_web(self, company_name):
        """Verifica ticker via web scraping (com cache)"""
        if company_name in self.verified_tickers:
            return self.verified_tickers[company_name]
        
        try:
            sys.path.insert(0, 'src')
            from gerar_ticker_mapping import TickerMapper
            
            mapper = TickerMapper()
            ticker = mapper.search_b3_api(company_name)
            self.verified_tickers[company_name] = ticker
            return ticker
        except:
            return None
    
    def extract_company_name(self, desc):
        """Extrai nome da empresa da descrição"""
        # Remove sufixos como ON, PN, PNA, PNB, NM, N1, N2, N3
        company = re.sub(r'\s+(ON|PN|PNA|PNB|NM|N1|N2|N3).*$', '', desc.strip(), flags=re.IGNORECASE)
        return company.strip()
    
    def validate_mapping(self, desc, ticker):
        """Valida se o mapeamento está correto"""
        desc_upper = desc.upper().strip()
        ticker_upper = ticker.upper()
        
        # Se está na lista de exceções, não valida
        if desc_upper in self.exceptions and self.exceptions[desc_upper].upper() == ticker_upper:
            return True, "EXCEÇÃO CONHECIDA"
        
        # Se o ticker começa com 0P (ISIN), aceita (são códigos especiais da B3)
        if ticker_upper.startswith('0P'):
            return True, "ISIN/Código Especial"
        
        # Se é código de fundo (termina em 11), aceita variações
        if ticker_upper.endswith('11'):
            return True, "Fundo/Classes Especiais"
        
        # Regras padrão B3
        if desc_upper.endswith(' ON'):
            if not ticker_upper.endswith('3'):
                if ticker_upper[-1] not in ['3', '4', '5', '6', '7', '8', '9']:
                    return False, f"ON deve terminar em 3 (não em {ticker[-1]})"
                return False, f"⚠️ ON termina em {ticker[-1]} (esperado 3 - possível classe especial)"
        
        elif desc_upper.endswith(' PNB'):
            if not ticker_upper[-1] in ['4', '5', '6']:
                return False, f"PNB deve terminar em 4/5/6 (não em {ticker[-1]})"
        
        elif desc_upper.endswith(' PNA'):
            if not ticker_upper[-1] in ['4', '5']:
                return False, f"PNA deve terminar em 4/5 (não em {ticker[-1]})"
        
        elif desc_upper.endswith(' PN'):
            if not ticker_upper[-1] in ['4', '5', '6']:
                return False, f"PN deve terminar em 4/5/6 (não em {ticker[-1]})"
        
        elif ' ON ' in desc_upper:
            if not ticker_upper.endswith('3'):
                if ticker_upper[-1] not in ['3', '4', '5', '6', '7', '8', '9']:
                    return False, f"ON* deve terminar em 3 (não em {ticker[-1]})"
        
        elif ' PN ' in desc_upper:
            if not ticker_upper[-1] in ['4', '5', '6']:
                return False, f"PN* deve terminar em 4/5/6 (não em {ticker[-1]})"
        
        return True, "OK"
    
    def try_fix_mapping(self, desc, ticker):
        """Tenta corrigir mapeamento via exceções ou web scraping"""
        company = self.extract_company_name(desc)
        
        # Primeiro: verifica se está na lista de exceções
        if desc.upper() in self.exceptions:
            correct_ticker = self.exceptions[desc.upper()]
            if correct_ticker.upper() != ticker.upper():
                self.fixed_entries[desc] = (ticker, correct_ticker)
                return correct_ticker
        
        # Segundo: tenta web scraping como fallback
        correct_ticker = self.verify_ticker_with_web(company)
        
        if correct_ticker and correct_ticker.upper() != ticker.upper():
            self.fixed_entries[desc] = (ticker, correct_ticker)
            return correct_ticker
        
        return None
    
    def sanitize(self, fix=False):
        """Valida todos os mapeamentos e reporta issues"""
        print("=" * 100)
        print("🔍 VALIDANDO MAPEAMENTOS DE TICKERS")
        print("=" * 100)
        
        issues_found = 0
        fixed_count = 0
        
        for desc, ticker in sorted(self.mappings.items()):
            is_valid, msg = self.validate_mapping(desc, ticker)
            
            if not is_valid:
                self.issues[msg].append((desc, ticker))
                issues_found += 1
                
                print(f"\n❌ {desc:40} → {ticker:10} ({msg})")
                
                # Tenta corrigir em modo --fix
                if fix:
                    corrected = self.try_fix_mapping(desc, ticker)
                    if corrected:
                        print(f"   ✓ Corrigido para: {corrected}")
                        fixed_count += 1
        
        print("\n" + "=" * 100)
        print("📊 RESUMO")
        print("=" * 100)
        print(f"Total de mapeamentos analisados: {len(self.mappings)}")
        print(f"Total de problemas encontrados: {issues_found}")
        if fix:
            print(f"Total de correções aplicadas: {fixed_count}")
        
        if self.issues:
            print("\n📋 Problemas por tipo:\n")
            for issue_type, entries in sorted(self.issues.items()):
                print(f"  {issue_type}: {len(entries)} caso(s)")
                for desc, ticker in entries[:3]:
                    print(f"    - {desc:40} → {ticker}")
                if len(entries) > 3:
                    print(f"    ... e mais {len(entries) - 3}")
        
        return issues_found == 0
    
    def apply_fixes(self):
        """Aplica as correções ao arquivo"""
        if not self.fixed_entries:
            print("Nenhuma correção para aplicar.")
            return
        
        print(f"\nAplicando {len(self.fixed_entries)} correção(ões)...")
        
        # Lê o arquivo atual
        with open(self.mapping_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Aplica as correções
        new_lines = []
        for line in lines:
            if '=' in line and not line.startswith('#'):
                desc, ticker = line.split('=', 1)
                desc = desc.strip()
                
                if desc in self.fixed_entries:
                    old_ticker, new_ticker = self.fixed_entries[desc]
                    new_lines.append(f"{desc}={new_ticker}\n")
                    print(f"  ✓ {desc:40} {old_ticker:10} → {new_ticker}")
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Escreve o arquivo atualizado
        with open(self.mapping_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"\n✅ Arquivo atualizado: {self.mapping_file}")
    
    def generate_report(self, output_file=None):
        """Gera relatório em CSV com problemas encontrados"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"resouces/ticker_sanitization_report_{timestamp}.csv"
        
        if not self.issues:
            print("✅ Nenhum problema encontrado para reportar.")
            return
        
        print(f"\n📄 Gerando relatório: {output_file}")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Descrição', 'Ticker Atual', 'Tipo de Problema', 'Sugestão'])
            
            for issue_type, entries in sorted(self.issues.items()):
                for desc, ticker in entries:
                    # Prioriza exceções conhecidas para a sugestão
                    if desc.upper() in self.exceptions:
                        suggestion = self.exceptions[desc.upper()]
                    else:
                        # Fallback: tenta web scraping
                        suggestion = self.try_fix_mapping(desc, ticker) or "Revisão Manual"
                    writer.writerow([desc, ticker, issue_type, suggestion])
        
        print(f"✓ Relatório criado com {sum(len(e) for e in self.issues.values())} entrada(s)")
        
        return output_file


# Execução
if __name__ == '__main__':
    fix_mode = '--fix' in sys.argv
    report_mode = '--report' in sys.argv
    
    sanitizer = TickerSanitizer()
    
    # Modo normal: apenas valida (ou tenta corrigir se --fix)
    success = sanitizer.sanitize(fix=fix_mode)
    
    # Aplicar correções se modo --fix
    if fix_mode and sanitizer.fixed_entries:
        sanitizer.apply_fixes()
    
    # Gerar relatório se modo --report
    if report_mode:
        sanitizer.generate_report()
    
    # Status final
    print("\n" + "=" * 100)
    if success:
        print("✅ Todos os mapeamentos estão válidos!")
    else:
        print("⚠️  Foram encontrados problemas nos mapeamentos!")
        print("   Use: python3 sanitize_tickers.py --fix")
        print("        para corrigir automaticamente via web scraping")
        print("   Use: python3 sanitize_tickers.py --report")
        print("        para gerar relatório detalhado em CSV")
    print("=" * 100)

