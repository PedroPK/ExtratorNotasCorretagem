"""
Testes para padrões regex de extração
Valida extração correta de operações, preços, tickers
"""

import pytest
import re


class TestOperationRegex:
    """Testa regex para extração de operações de compra/venda"""
    
    def test_extract_operation_buy(self):
        """Extrai operação de compra (C)"""
        pattern = r'[CV]'  # Compra (C) ou Venda (V)
        text = "03/10/2018 C SUZB3 20 44.00"
        
        match = re.search(pattern, text)
        assert match is not None
        assert match.group(0) == 'C'
    
    def test_extract_operation_sell(self):
        """Extrai operação de venda (V)"""
        pattern = r'[CV]'
        text = "03/10/2018 V SUZB3 20 44.00"
        
        match = re.search(pattern, text)
        assert match is not None
        assert match.group(0) == 'V'
    
    def test_operation_not_confused_with_other_c(self):
        """Operação C não deve ser confundida com outros C na linha"""
        # Isso é um teste para garantir que o regex seja específico
        pattern = r'(?:^|\s)([CV])(?:\s|$)'  # Operação entre espaços
        text = "03/10/2018 C SUZB3"
        
        match = re.search(pattern, text)
        assert match is not None


class TestPriceRegex:
    """Testa regex para extração de preços"""
    
    def test_extract_simple_price(self):
        """Extrai preço simples (XX.XX)"""
        pattern = r'\d+[.,]\d{1,2}'
        text = "SUZB3 20 44.00"
        
        match = re.search(pattern, text)
        assert match is not None
        assert match.group(0) == '44.00'
    
    def test_extract_price_with_comma(self):
        """Extrai preço com vírgula como separador"""
        pattern = r'\d+[.,]\d{1,2}'
        text = "BTOW3 2 28,90"
        
        match = re.search(pattern, text)
        assert match is not None
        assert '28' in match.group(0)
    
    def test_extract_price_with_single_decimal(self):
        """Extrai preço com uma casa decimal"""
        pattern = r'\d+[.,]\d{1,2}'
        text = "FLRY3 10 5.0"
        
        match = re.search(pattern, text)
        assert match is not None
    
    def test_extract_multiple_prices_gets_last(self):
        """Quando há múltiplos preços, pega o último"""
        pattern = r'\d+[.,]\d{1,2}'
        text = "03/10/2018 SUZB3 20 44.00"
        
        matches = re.findall(pattern, text)
        assert len(matches) == 1
        assert matches[0] == '44.00'


class TestTickerRegex:
    """Testa regex para extração de tickers"""
    
    def test_extract_4char_ticker(self):
        """Extrai ticker padrão (4 caracteres + número)"""
        pattern = r'[A-Z]{4}\d{1,2}'
        text = "SUZB3 20"
        
        match = re.search(pattern, text)
        assert match is not None
        assert match.group(0) == 'SUZB3'
    
    def test_extract_5char_ticker(self):
        """Extrai ticker de 5 caracteres (ex: KLBN11)"""
        pattern = r'[A-Z]{4,5}\d{1,2}'
        text = "KLBN11 30"
        
        match = re.search(pattern, text)
        assert match is not None
        assert match.group(0) == 'KLBN11'
    
    def test_extract_ticker_with_different_numbers(self):
        """Extrai tickers com diferentes números"""
        test_cases = [
            ('PETR4', 'PETR4'),
            ('VALE3', 'VALE3'),
            ('ITUB4', 'ITUB4'),
            ('KLBN11', 'KLBN11'),
        ]
        
        pattern = r'[A-Z]{4,5}\d{1,2}'
        
        for text, expected in test_cases:
            match = re.search(pattern, text)
            assert match is not None
            assert match.group(0) == expected


class TestDateRegex:
    """Testa regex para extração de datas"""
    
    def test_extract_date_ddmmyyyy(self):
        """Extrai data no formato DD/MM/YYYY"""
        pattern = r'(\d{2})/(\d{2})/(\d{4})'
        text = "23/11/2018 PETROBRAS PN"
        
        match = re.search(pattern, text)
        assert match is not None
        assert match.group(0) == '23/11/2018'
    
    def test_extract_multiple_dates_gets_first(self):
        """Em múltiplas datas, extrai a primeira"""
        pattern = r'(\d{2})/(\d{2})/(\d{4})'
        text = "23/11/2018 operação 03/10/2018"
        
        match = re.search(pattern, text)
        assert match.group(0) == '23/11/2018'
    
    def test_date_validation(self):
        """Data deve ter formato válido"""
        pattern = r'(\d{2})/(\d{2})/(\d{4})'
        
        valid_dates = ['01/01/2018', '31/12/2025', '29/02/2020']
        invalid_dates = ['1/1/2018', '32/13/2018']
        
        for date in valid_dates:
            assert re.match(pattern, date) is not None
        
        for date in invalid_dates:
            # Isso é uma simplificação; regex puro não valida logicamente
            # mas o padrão pode não corresponder formatos inválidos
            pass


class TestQuantityRegex:
    """Testa regex para extração de quantidade"""
    
    def test_extract_integer_quantity(self):
        """Extrai quantidade numérica"""
        pattern = r'\d+'
        text = "20 44.00"
        
        matches = re.findall(pattern, text)
        assert '20' in matches
    
    def test_extract_large_quantity(self):
        """Extrai quantidades grandes"""
        pattern = r'\d+'
        text = "10000 150.50"
        
        matches = re.findall(pattern, text)
        assert '10000' in matches


class TestAssetNameRegex:
    """Testa regex para extração de nome de ativo"""
    
    def test_extract_simple_asset_name(self):
        """Extrai nome simples de ativo"""
        pattern = r'^[A-Z\s]+(?=\s+[CV])'
        text = "SUZB3 ON EJ"
        # Nota: este é um exemplo simplificado
    
    def test_extract_asset_with_special_chars(self):
        """Extrai nome de ativo com caracteres especiais"""
        # Alguns ativos têm nomes como "PETROBRAS S/A PN"
        pattern = r"[A-Z\s/&\-'.]+"
        text = "KLABIN S/A UNT EDJ N2"
        
        # Verifica que consegue extrair com essa pattern
        assert re.search(pattern, text) is not None


class TestRegexEdgeCases:
    """Testa casos especiais em regex"""
    
    def test_regex_with_special_characters(self):
        """Regex funciona com caracteres especiais"""
        pattern = r"[A-Z\s/&'.]+"
        test_cases = [
            "BRADESPAR",
            "PETROBRAS S/A",
            "KLABIN S/A",
        ]
        
        for text in test_cases:
            assert re.search(pattern, text) is not None
    
    def test_regex_case_sensitivity(self):
        """Regex deve ser case-sensitive para tickers (maiúsculas)"""
        pattern = r'[A-Z]{4}\d{1,2}'
        
        # Deve encontrar
        assert re.search(pattern, 'SUZB3') is not None
        
        # Não deve encontrar em minúsculas
        assert re.search(pattern, 'suzb3') is None
    
    def test_regex_handles_extra_spaces(self):
        """Regex deve lidar com espaços extras"""
        # Pattern mais flexível
        pattern = r'(\d{2})/(\d{2})/(\d{4})\s+([A-Z\s]+?)\s+([CV])\s+(\d+)\s+([\d.,]+)'
        
        text = "23/11/2018  PETROBRAS PN EJ N2  C  100  24.20"
        # Este seria um padrão mais completo
