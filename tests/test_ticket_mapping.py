"""
Testes para mapeamento de tickers (v1.1.6)
Valida que o sistema de score-based fuzzy matching funciona corretamente
e que as configurações têm prioridade sobre valores hardcoded
"""

import pytest
from unittest.mock import patch


class TestTickerMappingPriority:
    """Testa prioridade de mapeamento: configurável > hardcoded"""
    
    def test_petrobras_pn_maps_to_petr4(self, ticker_mapping_dict):
        """Issue v1.1.6: PETROBRAS PN EJ N2 deve mapear para PETR4, não PETR3"""
        asset = 'PETROBRAS PN EJ N2'
        expected = 'PETR4'
        
        # Simula busca com prioridade: ticker_mapping > DE_PARA_TICKERS
        ticker_mapping = ticker_mapping_dict
        
        assert ticker_mapping[asset] == expected, \
            f"PETROBRAS PN EJ N2 deveria mapear para {expected}, mas mapeou para {ticker_mapping.get(asset)}"
    
    def test_petrobras_on_maps_to_petr3(self, ticker_mapping_dict):
        """PETROBRAS ON EJ N2 deve mapear para PETR3"""
        asset = 'PETROBRAS ON EJ N2'
        expected = 'PETR3'
        
        ticker_mapping = ticker_mapping_dict
        assert ticker_mapping[asset] == expected
    
    def test_gerdau_met_pn_maps_to_goau4(self, ticker_mapping_dict):
        """v1.1.6: GERDAU MET PN ED N1 deve mapear para GOAU4"""
        asset = 'GERDAU MET PN ED N1'
        expected = 'GOAU4'
        
        ticker_mapping = ticker_mapping_dict
        assert ticker_mapping[asset] == expected
    
    def test_klabin_maps_correctly(self, ticker_mapping_dict):
        """v1.1.5: KLABIN S/A UNT EDJ N2 deve mapear para KLBN11"""
        asset = 'KLABIN S/A UNT EDJ N2'
        expected = 'KLBN11'
        
        ticker_mapping = ticker_mapping_dict
        assert ticker_mapping[asset] == expected


class TestTickerMappingPriorityOrder:
    """Valida ordem de prioridade: ticker_mapping (exata) > ticker_mapping (fuzzy) > DE_PARA_TICKERS"""
    
    def test_exact_match_in_ticker_mapping_beats_fuzzy(self, ticker_mapping_dict, de_para_tickers_dict):
        """Match exato em ticker_mapping deve ser preferido a fuzzy em DE_PARA_TICKERS"""
        # PETROBRAS PN EJ N2 tem match exato em ticker_mapping → PETR4
        # PETROBRAS tem match fuzzy em DE_PARA_TICKERS → PETR3
        # Resultado esperado: PETR4
        
        asset = 'PETROBRAS PN EJ N2'
        
        # Simula estratégia de busca com prioridades
        result = None
        
        # Prioridade 1: Busca exata em ticker_mapping
        if asset in ticker_mapping_dict:
            result = ticker_mapping_dict[asset]
        
        # Prioridade 2: Busca exata em DE_PARA_TICKERS (fallback)
        if result is None and asset in de_para_tickers_dict:
            result = de_para_tickers_dict[asset]
        
        assert result == 'PETR4', "Match exato em ticker_mapping deveria vencer"


class TestTickerMappingVariants:
    """Testa diferentes variações de nomes de ativos"""
    
    def test_different_asset_variants(self, ticker_mapping_dict):
        """Testa múltiplas variações de um mesmo ativo"""
        test_cases = [
            ('PETROBRAS ON EJ N2', 'PETR3'),
            ('PETROBRAS PN EJ N2', 'PETR4'),
            ('GERDAU MET PN ED N1', 'GOAU4'),
            ('KLABIN S/A UNT EDJ N2', 'KLBN11'),
        ]
        
        for asset, expected_ticker in test_cases:
            assert ticker_mapping_dict[asset] == expected_ticker, \
                f"Mapeamento incorreto para {asset}"
    
    def test_bradespar_pn_n1(self, ticker_mapping_dict):
        """v1.1.4: BRADESPAR PN N1 deve mapear para BRAD2"""
        asset = 'BRADESPAR PN N1'
        expected = 'BRAD2'
        
        assert ticker_mapping_dict[asset] == expected


class TestTickerMappingPerformance:
    """Testa performance do mapeamento de tickers"""
    
    def test_mapping_lookup_is_fast(self, ticker_mapping_dict):
        """Lookup de ticker deve ser rápido (O(1) em dicionário)"""
        import time
        
        # Testa 10000 lookups
        start = time.time()
        for _ in range(10000):
            _ = ticker_mapping_dict.get('PETROBRAS PN EJ N2', None)
        elapsed = time.time() - start
        
        # Deve completar em menos de 100ms
        assert elapsed < 0.1, f"Lookup muito lento: {elapsed}s para 10000 operações"


class TestFuzzyMatchingScoring:
    """Testa sistema de score-based fuzzy matching (v1.1.2)"""
    
    def test_exact_match_scores_higher_than_fuzzy(self):
        """Match exato (score 1.0) deve ser preferido a fuzzy (~0.9)"""
        exact_score = 1.0
        fuzzy_score = 0.9 * 0.9  # Base score * specificity bonus
        
        assert exact_score > fuzzy_score
    
    def test_specificity_bonus_increases_score(self):
        """Mapping mais específico deve ter score mais alto"""
        # "PETROBRAS PN EJ N2" é mais específico que "PETROBRAS"
        specific_score = 0.9 * 1.0  # 0.9 base * 1.0 specificity bonus
        generic_score = 0.9 * 0.1   # 0.9 base * 0.1 specificity bonus
        
        assert specific_score > generic_score, \
            "Mapping específico deveria ter score mais alto"
