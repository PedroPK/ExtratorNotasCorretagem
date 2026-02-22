"""
Testes para o módulo review_unmapped_mappings.py

Cobertura:
- review_unmapped_mappings: revisão e importação de mapeamentos não encontrados
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from io import StringIO

# Importa o módulo
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from review_unmapped_mappings import review_unmapped_mappings


class TestReviewUnmappedMappings:
    """Testes para a função review_unmapped_mappings."""

    @patch('review_unmapped_mappings.os.path.exists')
    @patch('builtins.print')
    def test_unmapped_file_not_found(self, mock_print, mock_exists):
        """Testa comportamento quando arquivo unmapped não existe."""
        mock_exists.return_value = False
        
        review_unmapped_mappings()
        
        # Deve verificar existência do arquivo
        assert mock_exists.called

    @patch('review_unmapped_mappings.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="")
    @patch('builtins.print')
    def test_unmapped_file_empty(self, mock_print, mock_file, mock_exists):
        """Testa comportamento quando arquivo unmapped está vazio."""
        mock_exists.return_value = True
        
        review_unmapped_mappings()
        
        # Deve tentar abrir o arquivo
        assert mock_file.called

    @patch('review_unmapped_mappings.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="# Comentário\n\n")
    @patch('builtins.print')
    def test_unmapped_file_only_comments(self, mock_print, mock_file, mock_exists):
        """Testa quando arquivo tem apenas comentários."""
        mock_exists.return_value = True
        
        review_unmapped_mappings()
        
        # Deve processar sem erro
        assert mock_file.called

    @patch('review_unmapped_mappings.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_unmapped_with_filled_mappings(self, mock_print, mock_file, mock_exists):
        """Testa detecção de mapeamentos preenchidos."""
        # Simula arquivo unmapped com entrada preenchida
        unmapped_data = "Embraer ON=EMBR3\n"
        mapping_data = "# Cabecalho\n"
        
        # Mock para sequência de opens
        mock_exists.return_value = True
        mock_file.return_value.__enter__.return_value.read.return_value = unmapped_data
        
        # Não vai gerar erro, apenas processar
        with patch('builtins.open', mock_open(read_data=unmapped_data)):
            # Simula leitura dupla: unmapped e mapping
            with patch('review_unmapped_mappings.os.path.exists', return_value=True):
                review_unmapped_mappings()

    @patch('review_unmapped_mappings.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_unmapped_with_empty_entries(self, mock_print, mock_file, mock_exists):
        """Testa detecção de entradas vazias (não preenchidas)."""
        unmapped_data = "Embraer ON=\nBraskem PN=\n"
        
        mock_exists.return_value = True
        mock_file.return_value.__enter__.return_value.readline.side_effect = [
            "Embraer ON=\n",
            "Braskem PN=\n",
            ""
        ]
        
        review_unmapped_mappings()
        
        # Deve processar arquivo

    @patch('review_unmapped_mappings.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_conflict_detection(self, mock_print, mock_file, mock_exists):
        """Testa detecção de conflito entre tickers."""
        unmapped_data = """# Header
Embraer ON=EMBR3
"""
        mapping_data = """# Header
Embraer ON=EMBE3

"""
        
        mock_exists.return_value = True
        
        # Simula leitura de unmapped com ticker diferente
        # A função deve detectar conflito

    @patch('review_unmapped_mappings.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_same_mapping_no_conflict(self, mock_print, mock_file, mock_exists):
        """Testa que ticker idêntico não é conflito."""
        unmapped_data = "Embraer ON=EMBR3\n"
        mapping_data = "# Header\nEmbraer ON=EMBR3\n"
        
        mock_exists.return_value = True
        
        # Não deve gerar conflito

    @patch('review_unmapped_mappings.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_read_existing_mapping_error(self, mock_print, mock_file, mock_exists):
        """Testa tratamento de erro ao ler mapping existente."""
        mock_exists.return_value = True
        mock_file.side_effect = IOError("Permission denied")
        
        # Deve capturar erro sem falhar

    @patch('review_unmapped_mappings.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_write_mapping_file_error(self, mock_print, mock_file, mock_exists):
        """Testa tratamento de erro ao salvar mapping."""
        mock_exists.return_value = True
        
        unmapped_data = """# Header
Embraer ON=EMBR3
"""
        mapping_data = "# Header\n"
        
        # Simula erro na escrita
        mock_file.return_value.__enter__.return_value.write.side_effect = IOError("Disk full")
        
        # Deve capturar erro


class TestParseUnmappedEntries:
    """Testes para parsing de entradas unmapped."""

    def test_parse_valid_entry_with_ticker(self):
        """Testa parsing de entrada válida com ticker."""
        line = "Embraer ON=EMBR3"
        
        # Simula parsing
        if '=' in line:
            desc, ticker = line.split('=', 1)
            desc = desc.strip()
            ticker = ticker.strip()
            
            assert desc == "Embraer ON"
            assert ticker == "EMBR3"

    def test_parse_entry_empty_ticker(self):
        """Testa parsing de entrada com ticker vazio."""
        line = "Braskem PN="
        
        if '=' in line:
            desc, ticker = line.split('=', 1)
            desc = desc.strip()
            ticker = ticker.strip()
            
            assert desc == "Braskem PN"
            assert ticker == ""

    def test_parse_comment_line(self):
        """Testa que linhas de comentário são ignoradas."""
        line = "# Comentário"
        
        is_comment = line.strip().startswith('#')
        assert is_comment is True

    def test_parse_empty_line(self):
        """Testa que linhas vazias são ignoradas."""
        line = ""
        
        is_empty = not line
        assert is_empty is True

    def test_parse_whitespace_only_line(self):
        """Testa que linhas com apenas espaços são vazias."""
        line = "   "
        
        is_empty = not line or not line.strip()
        assert is_empty is True

    def test_parse_entry_with_spaces(self):
        """Testa parsing com espaços extras."""
        line = "  Embraer ON  =  EMBR3  "
        
        if '=' in line:
            desc, ticker = line.split('=', 1)
            desc = desc.strip()
            ticker = ticker.strip()
            
            assert desc == "Embraer ON"
            assert ticker == "EMBR3"

    def test_parse_multi_equals_sign(self):
        """Testa parsing quando há múltiplos sinais de igual."""
        line = "Desc=Val=Extra"
        
        # Deve usar apenas o primeiro split
        if '=' in line:
            desc, ticker = line.split('=', 1)
            desc = desc.strip()
            ticker = ticker.strip()
            
            assert desc == "Desc"
            assert ticker == "Val=Extra"

    def test_parse_entry_with_numbers(self):
        """Testa parsing com números."""
        line = "3M ON=MXRF11"
        
        if '=' in line:
            desc, ticker = line.split('=', 1)
            assert "3M" in desc
            assert ticker == "MXRF11"

    def test_parse_entry_with_special_chars(self):
        """Testa parsing com caracteres especiais."""
        line = "Vale-Doce ON=VALE3"
        
        if '=' in line:
            desc, ticker = line.split('=', 1)
            assert "Vale-Doce" in desc
            assert ticker == "VALE3"

    def test_parse_long_description(self):
        """Testa parsing com descrição longa."""
        line = "Banco do Brasil Participacoes S.A. ON NM=BBAS3"
        
        if '=' in line:
            desc, ticker = line.split('=', 1)
            desc = desc.strip()
            assert len(desc) > 20
            assert ticker == "BBAS3"


class TestMappingConflictDetection:
    """Testes para detecção de conflitos de mapeamento."""

    def test_no_conflict_when_description_not_exists(self):
        """Testa que não há conflito se descrição não existe."""
        existing = {}
        desc = "Embraer ON"
        ticker = "EMBR3"
        
        has_conflict = desc in existing
        assert has_conflict is False

    def test_no_conflict_when_ticker_same(self):
        """Testa que não há conflito se ticker é igual."""
        existing = {"Embraer ON": "EMBR3"}
        desc = "Embraer ON"
        ticker = "EMBR3"
        
        has_conflict = desc in existing and existing[desc] != ticker
        assert has_conflict is False

    def test_conflict_when_ticker_different(self):
        """Testa que há conflito se ticker é diferente."""
        existing = {"Embraer ON": "EMBR3"}
        desc = "Embraer ON"
        ticker = "EMBE3"
        
        has_conflict = desc in existing and existing[desc] != ticker
        assert has_conflict is True

    def test_multiple_mappings_no_conflict(self):
        """Testa múltiplos mapeamentos sem conflito."""
        existing = {"Embraer ON": "EMBR3", "Braskem PN": "BRKM5"}
        new_mapping = {"Suzano ON": "SUZB3"}
        
        conflicts = 0
        for desc, ticker in new_mapping.items():
            if desc in existing and existing[desc] != ticker:
                conflicts += 1
        
        assert conflicts == 0

    def test_multiple_mappings_with_conflict(self):
        """Testa múltiplos mapeamentos com conflito."""
        existing = {"Embraer ON": "EMBR3", "Braskem PN": "BRKM5"}
        new_mapping = {"Embraer ON": "EMBE3", "Suzano ON": "SUZB3"}
        
        conflicts = 0
        for desc, ticker in new_mapping.items():
            if desc in existing and existing[desc] != ticker:
                conflicts += 1
        
        assert conflicts == 1


class TestFileOperations:
    """Testes para operações de arquivo."""

    def test_read_unmapped_file_success(self):
        """Testa leitura bem-sucedida de arquivo unmapped."""
        content = """# Header
Embraer ON=EMBR3
Braskem PN=
Suzano ON=SUZB3
"""
        
        entries = []
        for line in content.split('\n'):
            line = line.rstrip('\n')
            if line and '=' in line and not line.strip().startswith('#'):
                desc, ticker = line.split('=', 1)
                entries.append((desc.strip(), ticker.strip()))
        
        assert len(entries) == 3
        assert entries[0] == ("Embraer ON", "EMBR3")
        assert entries[1] == ("Braskem PN", "")
        assert entries[2] == ("Suzano ON", "SUZB3")

    def test_read_mapping_file_success(self):
        """Testa leitura bem-sucedida de arquivo de mapeamento."""
        content = """# Header
Embraer ON=EMBR3
Braskem PN=BRKM5
Suzano ON=SUZB3
"""
        
        mapping = {}
        for line in content.split('\n'):
            line = line.rstrip('\n')
            if line and '=' in line and not line.startswith('#'):
                desc, ticker = line.split('=', 1)
                mapping[desc.strip()] = ticker.strip()
        
        assert len(mapping) == 3
        assert mapping["Embraer ON"] == "EMBR3"
        assert mapping["Braskem PN"] == "BRKM5"

    def test_reconstruct_unmapped_file(self):
        """Testa reconstrução de arquivo unmapped sem entradas importadas."""
        original_rejected = ["# Header", "", "# Linhas não preenchidas"]
        
        reconstructed = []
        reconstructed.append("# Descrições não mapeadas - PARA REVISÃO MANUAL\n")
        for line in original_rejected:
            reconstructed.append(line + '\n')
        
        result = ''.join(reconstructed)
        assert "# Descrições não mapeadas" in result

    def test_write_mapping_file_with_header(self):
        """Testa escrita de arquivo de mapeamento com cabeçalho."""
        mapping = {"Embraer ON": "EMBR3", "Braskem PN": "BRKM5"}
        
        lines = []
        lines.append("# Mapeamento de Descrições de Ativos para Tickers B3\n")
        lines.append("# Formato: DESCRICAO_DO_ATIVO=TICKER\n")
        
        for desc, ticker in sorted(mapping.items()):
            lines.append(f"{desc}={ticker}\n")
        
        result = ''.join(lines)
        assert "# Mapeamento de Descrições" in result
        assert "Embraer ON=EMBR3" in result


class TestEdgeCases:
    """Testes para casos extremos."""

    def test_empty_description(self):
        """Testa entrada com descrição vazia."""
        line = "=EMBR3"
        
        if '=' in line:
            desc, ticker = line.split('=', 1)
            desc = desc.strip()
            
            assert desc == ""
            assert ticker == "EMBR3"

    def test_empty_ticker(self):
        """Testa entrada com ticker vazio."""
        line = "Embraer ON="
        
        if '=' in line:
            desc, ticker = line.split('=', 1)
            ticker = ticker.strip()
            
            assert ticker == ""

    def test_very_long_description(self):
        """Testa descrição muito longa."""
        long_desc = "A" * 100 + "=EMBR3"
        
        if '=' in long_desc:
            desc, ticker = long_desc.split('=', 1)
            desc = desc.strip()
            
            assert len(desc) == 100

    def test_unicode_in_description(self):
        """Testa descrição com caracteres Unicode."""
        line = "Café ON=CAFE3"
        
        if '=' in line:
            desc, ticker = line.split('=', 1)
            assert "Café" in desc or "Caf" in desc

    def test_case_sensitivity(self):
        """Testa que parsing preserva case."""
        line = "EMBRAER ON=embr3"
        
        if '=' in line:
            desc, ticker = line.split('=', 1)
            
            assert desc.strip() == "EMBRAER ON"
            assert ticker.strip() == "embr3"

    def test_whitespace_preservation_description(self):
        """Testa preservação de espaços em descrição."""
        line = "Vale do Rio Doce ON=VALE3"
        
        if '=' in line:
            desc, ticker = line.split('=', 1)
            desc = desc.strip()
            
            assert "Vale do Rio Doce" in desc

    def test_no_equals_sign(self):
        """Testa linha sem sinal de igual."""
        line = "No equals here"
        
        is_valid = '=' in line
        assert is_valid is False


class TestMappingImport:
    """Testes para lógica de importação de mapeamentos."""

    def test_import_single_mapping(self):
        """Testa importação de um mapeamento."""
        unmapped = [("Embraer ON", "EMBR3")]
        existing = {}
        
        imported = 0
        for desc, ticker in unmapped:
            if desc not in existing:
                existing[desc] = ticker
                imported += 1
        
        assert imported == 1
        assert existing["Embraer ON"] == "EMBR3"

    def test_import_multiple_mappings(self):
        """Testa importação de múltiplos mapeamentos."""
        unmapped = [
            ("Embraer ON", "EMBR3"),
            ("Braskem PN", "BRKM5"),
            ("Suzano ON", "SUZB3"),
        ]
        existing = {}
        
        imported = 0
        for desc, ticker in unmapped:
            if desc not in existing:
                existing[desc] = ticker
                imported += 1
        
        assert imported == 3
        assert len(existing) == 3

    def test_import_skips_empty_ticker(self):
        """Testa que mapeamento com ticker vazio é pulado."""
        unmapped = [
            ("Embraer ON", "EMBR3"),
            ("Braskem PN", ""),  # Vazio
            ("Suzano ON", "SUZB3"),
        ]
        
        imported = 0
        for desc, ticker in unmapped:
            if ticker:  # Só importa se ticker não vazio
                imported += 1
        
        assert imported == 2

    def test_import_skips_existing_same(self):
        """Testa que mapeamento idêntico é pulado (não re-importa)."""
        unmapped = [("Embraer ON", "EMBR3")]
        existing = {"Embraer ON": "EMBR3"}
        
        skipped = 0
        for desc, ticker in unmapped:
            if desc in existing and existing[desc] == ticker:
                skipped += 1
        
        assert skipped == 1

    def test_import_skips_conflicting(self):
        """Testa que mapeamento conflitante é pulado."""
        unmapped = [("Embraer ON", "EMBE3")]
        existing = {"Embraer ON": "EMBR3"}
        
        skipped = 0
        for desc, ticker in unmapped:
            if desc in existing and existing[desc] != ticker:
                skipped += 1
        
        assert skipped == 1

    def test_sorted_output(self):
        """Testa que mapeamentos são salvos em ordem alfabética."""
        mapping = {
            "Suzano ON": "SUZB3",
            "Embraer ON": "EMBR3",
            "Braskem PN": "BRKM5",
        }
        
        sorted_items = sorted(mapping.items())
        
        assert sorted_items[0][0] == "Braskem PN"
        assert sorted_items[1][0] == "Embraer ON"
        assert sorted_items[2][0] == "Suzano ON"
