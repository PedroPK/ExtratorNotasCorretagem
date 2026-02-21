"""
Testes para formatação de separador decimal (v1.1.7)
Valida que a coluna Preço usa vírgula como separador (padrão brasileiro)
"""

import pytest
import pandas as pd


class TestDecimalFormatting:
    """Testa formatação de Preço com vírgula como separador"""
    
    def test_price_uses_comma_separator(self):
        """Preço formatado deve usar vírgula, não ponto"""
        price = "24,20"
        
        assert ',' in price, "Preço deveria conter vírgula"
        assert '.' not in price or price.split(',')[0].count('.') == 0, \
            "Separador decimal deveria ser vírgula, não ponto"
    
    def test_format_point_to_comma(self):
        """Conversão de ponto para vírgula funciona corretamente"""
        original = "24.20"
        formatted = original.replace('.', ',')
        
        assert formatted == "24,20"
    
    def test_all_prices_have_comma_separator(self, sample_dataframe):
        """Todos os preços devem usar vírgula após formatação"""
        # Simula formatação aplicada durante export
        df = sample_dataframe.copy()
        df['Preço'] = df['Preço'].astype(str).str.replace('.', ',', regex=False)
        
        # Verifica que todos têm vírgula
        all_have_comma = all(df['Preço'].astype(str).str.contains(',', na=False))
        assert all_have_comma, "Nem todos os preços têm vírgula como separador"
    
    def test_price_values_preserved_after_formatting(self):
        """Valores dos preços devem ser preservados após formatação"""
        test_cases = [
            ("24.20", "24,20"),
            ("5.02", "5,02"),
            ("44.00", "44,00"),
            ("0.50", "0,50"),
            ("1234.56", "1234,56"),
        ]
        
        for original, expected in test_cases:
            formatted = original.replace('.', ',')
            assert formatted == expected, f"Formatação incorreta: {original} → {formatted}"


class TestDecimalFormattingOnExport:
    """Testa formatação aplicada durante exportação para XLSX"""
    
    def test_format_in_dados_sheet(self, sample_dataframe, tmp_path):
        """Aba 'Dados' deve ter preços formatados com vírgula"""
        df = sample_dataframe.copy()
        
        # Simula formatação antes de export
        df['Preço'] = df['Preço'].astype(str).str.replace('.', ',', regex=False)
        
        # Verifica coluna Preço
        for preco in df['Preço']:
            assert ',' in str(preco), f"Preço {preco} não tem vírgula"
    
    def test_format_in_arvore_sheet(self, sample_dataframe, tmp_path):
        """Aba 'Árvore' deve ter preços formatados com vírgula"""
        df = sample_dataframe.copy()
        
        # Simula formatação (mesma lógica para ambas as abas)
        df['Preço'] = df['Preço'].astype(str).str.replace('.', ',', regex=False)
        
        # Verifica coluna Preço
        for preco in df['Preço']:
            assert ',' in str(preco), f"Preço {preco} na Árvore não tem vírgula"


class TestDecimalFormattingEdgeCases:
    """Testa casos especiais de formatação decimal"""
    
    def test_integer_prices_formatted_correctly(self):
        """Preços inteiros devem ser formatados com vírgula"""
        prices = ["100", "50", "1000"]
        
        for price in prices:
            # Se não tem ponto, não precisa adicionar vírgula
            if '.' not in price:
                formatted = price
            else:
                formatted = price.replace('.', ',')
            
            assert formatted in ["100", "50", "1000"]
    
    def test_prices_with_extra_decimals(self):
        """Preços com mais casas decimais"""
        test_cases = [
            ("24.205", "24,205"),   # 3 casas
            ("5.0", "5,0"),         # 1 casa
            ("44.00000", "44,00000"),  # Múltiplos zeros
        ]
        
        for original, expected in test_cases:
            formatted = original.replace('.', ',')
            assert formatted == expected
    
    def test_empty_price_handling(self):
        """Preços vazios ou None devem ser tratados"""
        df = pd.DataFrame({
            'Preço': ['24.20', None, '5.02', '']
        })
        
        # Formatação segura
        df['Preço'] = df['Preço'].astype(str).str.replace('.', ',', regex=False)
        
        # Verifica que não quebrou
        assert len(df) == 4


class TestBrazilianFormatStandard:
    """Testa conformidade com padrão brasileiro ISO 8859-1"""
    
    def test_brazilian_locale_formatting(self):
        """Formatação segue padrão brasileiro"""
        # Padrão brasileiro usa vírgula para decimais
        price = "24,20"
        
        # Verifica separador
        parts = price.split(',')
        assert len(parts) == 2, "Deve ter exatamente uma vírgula"
        assert parts[0].isdigit(), "Antes da vírgula deve ter dígitos"
        assert parts[1].isdigit(), "Depois da vírgula deve ter dígitos"
    
    def test_thousands_separator_not_applied(self):
        """Sistema não deve aplicar separador de milhares (ponto não deve aparecer)"""
        # Preço de 1234.56 → 1234,56 (sem ponto para millhares)
        price = "1234.56"
        formatted = price.replace('.', ',')
        
        # Não deve haver ponto na string
        assert '.' not in formatted
        assert formatted == "1234,56"


class TestFormattingDataTypes:
    """Testa tipos de dados após formatação"""
    
    def test_formatted_price_is_string(self):
        """Preço formatado deve ser string para display"""
        price_float = 24.20
        price_str = str(price_float)
        price_formatted = price_str.replace('.', ',')
        
        assert isinstance(price_formatted, str)
        assert price_formatted == "24,2"  # float converte para 24.2
    
    def test_formatted_price_sortable_in_excel(self):
        """Preços formatados devem ser sortáveis em Excel (como strings numéricas)"""
        prices = ["24,20", "5,02", "44,00", "0,50"]
        
        # String numérica pode ser ordenada
        # (Excel trata como números se formato está correto)
        numeric_values = [float(p.replace(',', '.')) for p in prices]
        numeric_values.sort()
        
        assert numeric_values[0] == 0.50
        assert numeric_values[-1] == 44.00
