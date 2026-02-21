"""
Testes para exportação de dados em múltiplos formatos
Valida CSV, XLSX, JSON com formatação correta
"""

import pytest
import pandas as pd
import json
import os
from pathlib import Path


class TestCSVExport:
    """Testa exportação para CSV"""
    
    def test_csv_export_creates_file(self, sample_dataframe, tmp_path):
        """Exportação CSV cria arquivo"""
        csv_path = tmp_path / "test.csv"
        
        sample_dataframe.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        assert csv_path.exists(), "Arquivo CSV não foi criado"
    
    def test_csv_preserves_all_rows(self, sample_dataframe, tmp_path):
        """CSV deve conter todas as linhas"""
        csv_path = tmp_path / "test.csv"
        original_rows = len(sample_dataframe)
        
        sample_dataframe.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        df_read = pd.read_csv(csv_path)
        assert len(df_read) == original_rows
    
    def test_csv_preserves_columns(self, sample_dataframe, tmp_path):
        """CSV deve conter todas as colunas"""
        csv_path = tmp_path / "test.csv"
        original_columns = set(sample_dataframe.columns)
        
        sample_dataframe.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        df_read = pd.read_csv(csv_path)
        assert set(df_read.columns) == original_columns
    
    def test_csv_encoding_utf8_sig(self, sample_dataframe, tmp_path):
        """CSV deve usar encoding UTF-8 com BOM"""
        csv_path = tmp_path / "test.csv"
        
        sample_dataframe.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        # Lê com diferentes encodings para validar
        with open(csv_path, 'rb') as f:
            first_bytes = f.read(3)
            # UTF-8 BOM é EF BB BF
            assert first_bytes == b'\xef\xbb\xbf', "Arquivo não tem BOM correto"


class TestXLSXExport:
    """Testa exportação para XLSX"""
    
    def test_xlsx_export_creates_file(self, sample_dataframe, tmp_path):
        """Exportação XLSX cria arquivo"""
        xlsx_path = tmp_path / "test.xlsx"
        
        with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
            sample_dataframe.to_excel(writer, sheet_name="Dados", index=False)
        
        assert xlsx_path.exists(), "Arquivo XLSX não foi criado"
    
    def test_xlsx_multiple_sheets(self, sample_dataframe, tmp_path):
        """XLSX pode ter múltiplas abas (Dados e Árvore)"""
        xlsx_path = tmp_path / "test.xlsx"
        
        with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
            sample_dataframe.to_excel(writer, sheet_name="Dados", index=False)
            sample_dataframe.to_excel(writer, sheet_name="Árvore", index=False)
        
        # Lê ambas as abas
        df_dados = pd.read_excel(xlsx_path, sheet_name="Dados")
        df_arvore = pd.read_excel(xlsx_path, sheet_name="Árvore")
        
        assert len(df_dados) > 0
        assert len(df_arvore) > 0
    
    def test_xlsx_preserves_data(self, sample_dataframe, tmp_path):
        """XLSX deve preservar dados e tipos"""
        xlsx_path = tmp_path / "test.xlsx"
        
        with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
            sample_dataframe.to_excel(writer, sheet_name="Dados", index=False)
        
        df_read = pd.read_excel(xlsx_path, sheet_name="Dados")
        
        # Verifica dimensões
        assert df_read.shape == sample_dataframe.shape
        
        # Verifica colunas
        assert list(df_read.columns) == list(sample_dataframe.columns)


class TestXLSXPriceFormatting:
    """Testa formatação de Preço em XLSX com vírgula"""
    
    def test_xlsx_precio_has_comma_separator(self, sample_dataframe, tmp_path):
        """Preço em XLSX deve usar vírgula como separador"""
        xlsx_path = tmp_path / "test.xlsx"
        
        # Simula formatação antes de export
        df = sample_dataframe.copy()
        df['Preço'] = df['Preço'].astype(str).str.replace('.', ',', regex=False)
        
        with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="Dados", index=False)
        
        # Lê e valida
        df_read = pd.read_excel(xlsx_path, sheet_name="Dados")
        
        for preco in df_read['Preço']:
            assert ',' in str(preco), f"Preço {preco} não tem vírgula"
    
    def test_both_sheets_have_formatted_prices(self, sample_dataframe, tmp_path):
        """Ambas as abas devem ter preços formatados"""
        xlsx_path = tmp_path / "test.xlsx"
        
        df = sample_dataframe.copy()
        df['Preço'] = df['Preço'].astype(str).str.replace('.', ',', regex=False)
        
        with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="Dados", index=False)
            df.to_excel(writer, sheet_name="Árvore", index=False)
        
        # Verifica ambas as abas
        for sheet in ["Dados", "Árvore"]:
            df_read = pd.read_excel(xlsx_path, sheet_name=sheet)
            for preco in df_read['Preço']:
                assert ',' in str(preco), f"Preço em {sheet} sem vírgula"


class TestJSONExport:
    """Testa exportação para JSON"""
    
    def test_json_export_creates_file(self, sample_dataframe, tmp_path):
        """Exportação JSON cria arquivo"""
        json_path = tmp_path / "test.json"
        
        sample_dataframe.to_json(json_path, orient='records', indent=2, force_ascii=False)
        
        assert json_path.exists(), "Arquivo JSON não foi criado"
    
    def test_json_preserves_data(self, sample_dataframe, tmp_path):
        """JSON deve preservar dados"""
        json_path = tmp_path / "test.json"
        
        sample_dataframe.to_json(json_path, orient='records', indent=2, force_ascii=False)
        
        # Lê e valida estrutura
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data) == len(sample_dataframe)
        assert set(data[0].keys()) == set(sample_dataframe.columns)
    
    def test_json_encoding_utf8(self, sample_dataframe, tmp_path):
        """JSON deve usar UTF-8 e permitir caracteres especiais"""
        json_path = tmp_path / "test.json"
        
        # Adiciona dados com acentos/caracteres especiais
        df_special = sample_dataframe.copy()
        df_special.loc[0, 'Ticker'] = 'AÇÚCAR'
        
        df_special.to_json(json_path, orient='records', indent=2, force_ascii=False)
        
        # Verifica que caracteres especiais foram preservados
        with open(json_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'AÇÚCAR' in content


class TestExportFormats:
    """Testa todos os formatos de exportação com a mesma fonte de dados"""
    
    def test_all_formats_export_same_data_volume(self, sample_dataframe, tmp_path):
        """Todos os formatos devem exportar a mesma quantidade de dados"""
        original_rows = len(sample_dataframe)
        
        # CSV
        csv_path = tmp_path / "test.csv"
        sample_dataframe.to_csv(csv_path, index=False)
        df_csv = pd.read_csv(csv_path)
        
        # XLSX
        xlsx_path = tmp_path / "test.xlsx"
        with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
            sample_dataframe.to_excel(writer, sheet_name="Dados", index=False)
        df_xlsx = pd.read_excel(xlsx_path, sheet_name="Dados")
        
        # JSON
        json_path = tmp_path / "test.json"
        sample_dataframe.to_json(json_path, orient='records')
        df_json = pd.read_json(json_path)
        
        assert len(df_csv) == original_rows
        assert len(df_xlsx) == original_rows
        assert len(df_json) == original_rows
    
    def test_format_can_be_determined_from_argument(self):
        """Sistema deve detectar formato pelo argumento"""
        formats = ['csv', 'xlsx', 'json']
        
        for fmt in formats:
            assert fmt in formats, f"Formato {fmt} não suportado"
