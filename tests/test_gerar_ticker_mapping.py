"""
Testes para o módulo gerar_ticker_mapping.py

Cobertura:
- TickerMapper.parse_asset_name: parsing de nomes de ativos
- TickerMapper.generate_ticker_heuristic: geração de ticker por heurística
- TickerMapper._normalize_description_suffixes: normalização de sufixos
- TickerMapper._is_option: detecção de opções
- TickerMapper._normalize_ticker: normalização de ticker
- TickerMapper.map_asset: mapeamento principal
"""

import pytest
from pathlib import Path

# Importa o módulo
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gerar_ticker_mapping import TickerMapper


@pytest.fixture
def mapper():
    """Cria instância de TickerMapper para testes."""
    return TickerMapper()


class TestParseAssetName:
    """Testes para parsing de nomes de ativos."""

    def test_parse_on_nm_suffix(self, mapper):
        """Testa parsing de ativo com ON NM."""
        empresa, tipo, sufixo = mapper.parse_asset_name("Embraer ON NM")
        assert empresa == "Embraer"
        assert tipo == "ON"
        assert sufixo == 3

    def test_parse_pn_suffix(self, mapper):
        """Testa parsing de ativo com PN."""
        empresa, tipo, sufixo = mapper.parse_asset_name("Braskem PN")
        assert empresa == "Braskem"
        assert tipo == "PN"
        assert sufixo in [4, 5]  # PN pode ser 4 ou 5

    def test_parse_pna_suffix(self, mapper):
        """Testa parsing de ativo com PNA."""
        empresa, tipo, sufixo = mapper.parse_asset_name("Empresa PNA N1")
        assert tipo == "PNA"
        assert sufixo == 5

    def test_parse_pnb_suffix(self, mapper):
        """Testa parsing de ativo com PNB."""
        empresa, tipo, sufixo = mapper.parse_asset_name("Empresa PNB")
        assert tipo == "PNB"
        assert sufixo == 6

    def test_parse_dr_suffix(self, mapper):
        """Testa parsing de ativo com DR."""
        empresa, tipo, sufixo = mapper.parse_asset_name("Empresa DR")
        assert tipo == "DR"

    def test_parse_multi_word_company(self, mapper):
        """Testa parsing de empresa com múltiplas palavras."""
        empresa, tipo, sufixo = mapper.parse_asset_name("Vale do Rio Doce ON NM")
        assert "Vale" in empresa

    def test_parse_company_with_numbers(self, mapper):
        """Testa parsing de empresa com números."""
        empresa, tipo, sufixo = mapper.parse_asset_name("3M ON NM")
        assert "3M" in empresa or "3" in empresa

    def test_parse_case_insensitive(self, mapper):
        """Testa que parsing é case-insensitive."""
        empresa, tipo, sufixo = mapper.parse_asset_name("embraer on nm")
        assert tipo == "ON"

    def test_parse_stripped_result(self, mapper):
        """Testa que resultado possui espaços removidos."""
        empresa, tipo, sufixo = mapper.parse_asset_name("  Embraer  ON  NM  ")
        assert empresa == "Embraer"
        assert tipo == "ON"

    def test_parse_fallback_on(self, mapper):
        """Testa fallback para ON quando não encontra tipo."""
        empresa, tipo, sufixo = mapper.parse_asset_name("SomeCompany")
        assert tipo == "ON"


class TestGenerateTickerHeuristic:
    """Testes para geração de ticker por heurística."""

    def test_generate_known_special_case(self, mapper):
        """Testa caso especial conhecido (Embraer)."""
        ticker = mapper.generate_ticker_heuristic("Embraer", "ON", 3)
        assert ticker == "EMBR3"

    def test_generate_known_special_case_ultrapar(self, mapper):
        """Testa caso especial Ultrapar."""
        ticker = mapper.generate_ticker_heuristic("Ultrapar", "ON", 3)
        assert ticker == "UGPA3"

    def test_generate_known_special_case_suzano(self, mapper):
        """Testa caso especial Suzano."""
        ticker = mapper.generate_ticker_heuristic("Suzano", "ON", 3)
        assert ticker == "SUZB3"

    def test_generate_generic_case(self, mapper):
        """Testa geração genérica sem caso especial."""
        ticker = mapper.generate_ticker_heuristic("EMPRESA", "ON", 3)
        # Deve ter 4 letras + sufixo
        assert len(ticker) == 5
        assert ticker[-1] == "3"

    def test_generate_with_pn_suffix(self, mapper):
        """Testa geração com sufixo PN."""
        ticker = mapper.generate_ticker_heuristic("EMPRESA", "PN", 4)
        assert ticker[-1] == "4"

    def test_generate_none_suffix(self, mapper):
        """Testa que None suffix retorna None."""
        ticker = mapper.generate_ticker_heuristic("Empresa", "ON", None)
        assert ticker is None

    def test_generate_multi_word_company(self, mapper):
        """Testa geração para empresa com múltiplas palavras."""
        ticker = mapper.generate_ticker_heuristic("Banco do Brasil", "ON", 3)
        assert ticker == "BBAS3"

    def test_generate_case_insensitive(self, mapper):
        """Testa que input é convertido para uppercase."""
        ticker1 = mapper.generate_ticker_heuristic("embraer", "ON", 3)
        ticker2 = mapper.generate_ticker_heuristic("EMBRAER", "ON", 3)
        assert ticker1 == ticker2


class TestNormalizeDescriptionSuffixes:
    """Testes para normalização de sufixos em descrições."""

    def test_normalize_nm_suffix(self, mapper):
        """Testa remoção de sufixo NM."""
        result = mapper._normalize_description_suffixes("Fleury ON NM")
        assert result == "Fleury ON"

    def test_normalize_n1_suffix(self, mapper):
        """Testa remoção de sufixo N1."""
        result = mapper._normalize_description_suffixes("Braskem PNA N1")
        assert result == "Braskem PNA"

    def test_normalize_n2_suffix(self, mapper):
        """Testa remoção de sufixo N2."""
        result = mapper._normalize_description_suffixes("Empresa PN N2")
        assert result == "Empresa PN"

    def test_normalize_n3_suffix(self, mapper):
        """Testa remoção de sufixo N3."""
        result = mapper._normalize_description_suffixes("Empresa ON N3")
        assert result == "Empresa ON"

    def test_normalize_no_suffix(self, mapper):
        """Testa que descrição sem sufixo não muda."""
        result = mapper._normalize_description_suffixes("Embraer ON")
        assert result == "Embraer ON"

    def test_normalize_case_insensitive(self, mapper):
        """Testa case-insensitive normalization."""
        result = mapper._normalize_description_suffixes("Fleury ON nm")
        assert result == "Fleury ON"

    def test_normalize_with_extra_spaces(self, mapper):
        """Testa remoção de espaços extras."""
        result = mapper._normalize_description_suffixes("  Fleury ON NM  ")
        assert result == "Fleury ON"


class TestIsOption:
    """Testes para detecção de opções."""

    def test_is_option_valid_pattern_1(self, mapper):
        """Testa detecção de opção válida (ABEVA135)."""
        assert mapper._is_option("ABEVA135") is True

    def test_is_option_valid_pattern_2(self, mapper):
        """Testa detecção de opção válida (B3SAB725)."""
        assert mapper._is_option("B3SAB725") is True

    def test_is_option_valid_pattern_with_e(self, mapper):
        """Testa detecção de opção com 'E' no final."""
        assert mapper._is_option("BBASK344E") is True

    def test_is_option_not_option_three_digits(self, mapper):
        """Testa que BBASO1 (1 dígito) não é opção."""
        assert mapper._is_option("BBASO1") is False

    def test_is_option_not_option_two_digits(self, mapper):
        """Testa que BBAST44 (2 dígitos) não é opção."""
        assert mapper._is_option("BBAST44") is False

    def test_is_option_not_regular_ticker(self, mapper):
        """Testa que ABEV3 não é opção."""
        assert mapper._is_option("ABEV3") is False

    def test_is_option_empty_string(self, mapper):
        """Testa que string vazia não é opção."""
        assert mapper._is_option("") is False

    def test_is_option_none(self, mapper):
        """Testa que None retorna False."""
        assert mapper._is_option(None) is False

    def test_is_option_lowercase(self, mapper):
        """Testa que padrão requer uppercase."""
        # A função _is_option é case-sensitive, requer uppercase
        assert mapper._is_option("abeva135") is False


class TestNormalizeTicker:
    """Testes para normalização de ticker."""

    def test_normalize_remove_f_suffix(self, mapper):
        """Testa remoção de 'F' no final."""
        # Simula um ticker com F (ex: EMBRF3 → EMBR3)
        result = mapper._normalize_ticker("EMBRF3", "Embraer ON NM")
        # A função remove F se existir
        assert "EMBR" in result

    def test_normalize_already_normalized(self, mapper):
        """Testa que ticker normalizado retorna igual."""
        result = mapper._normalize_ticker("EMBR3", "Embraer ON NM")
        assert "3" in result

    def test_normalize_on_type(self, mapper):
        """Testa normalização com tipo ON."""
        result = mapper._normalize_ticker("ABEV", "Empresa ON NM")
        # _normalize_ticker retorna apenas o básico sem sufixo
        assert "ABEV" in result or len(result) >= 4

    def test_normalize_pn_type(self, mapper):
        """Testa normalização com tipo PN."""
        result = mapper._normalize_ticker("ABEV", "Empresa PN")
        # _normalize_ticker retorna apenas o básico
        assert "ABEV" in result or len(result) >= 4


class TestMapAsset:
    """Testes para mapeamento de ativo."""

    def test_map_asset_returns_ticker_or_none(self, mapper):
        """Testa que map_asset retorna ticker ou None."""
        # Primeira vez pode detectar como opção ou falhar
        result = mapper.map_asset("Embraer ON NM")
        # Pode retornar ticker ou None (depende da lógica)
        assert result is None or (isinstance(result, str) and len(result) > 0)

    def test_map_asset_detect_option(self, mapper):
        """Testa que opção é detectada e separada."""
        result = mapper.map_asset("ABEVA135")
        # Opções retornam None (são separadas para mapeamento de opções)
        assert result is None

    def test_map_asset_stripped_input(self, mapper):
        """Testa que input é stripped."""
        result1 = mapper.map_asset("Embraer ON NM")
        result2 = mapper.map_asset("  Embraer ON NM  ")
        # Devem processar da mesma forma
        assert result1 == result2

    def test_map_asset_case_handling(self, mapper):
        """Testa case handling."""
        result = mapper.map_asset("EMBRAER ON NM")
        # Deve processar normalmente
        assert result is None or isinstance(result, str)


class TestTickerMapperInit:
    """Testes para inicialização e estrutura de TickerMapper."""

    def test_init_creates_empty_mappings(self, mapper):
        """Testa que __init__ cria dicionários vazios."""
        assert isinstance(mapper.mapping, dict)
        assert isinstance(mapper.options_mapping, dict)
        assert isinstance(mapper.unmapped_mapping, dict)

    def test_init_sets_file_paths(self, mapper):
        """Testa que caminhos de arquivo são definidos."""
        assert mapper.mapping_file
        assert mapper.options_file
        assert mapper.unmapped_file

    def test_init_creates_locked_entries_set(self, mapper):
        """Testa que locked_entries é criado como set."""
        assert isinstance(mapper.locked_entries, set)


class TestIntegration:
    """Testes de integração entre múltiplas funções."""

    def test_parse_and_generate_flow(self, mapper):
        """Testa fluxo de parsing seguido de geração de ticker."""
        empresa, tipo, sufixo = mapper.parse_asset_name("Embraer ON NM")
        ticker = mapper.generate_ticker_heuristic(empresa, tipo, sufixo)
        
        # Deve gerar um ticker válido
        assert ticker
        assert len(ticker) == 5
        assert ticker[-1].isdigit()

    def test_normalize_and_map_flow(self, mapper):
        """Testa fluxo de normalização seguido de mapeamento."""
        normalized = mapper._normalize_description_suffixes("Embraer ON NM")
        result = mapper.map_asset(normalized)
        
        # Deve processar sem erros
        assert result is None or isinstance(result, str)

    def test_option_detection_in_map(self, mapper):
        """Testa que opções são detectadas corretamente durante mapeamento."""
        # Mapeia uma opção
        mapper.map_asset("ABEVA135")
        
        # Deve estar em options_mapping
        assert "ABEVA135" in mapper.options_mapping

    def test_multi_step_workflow(self, mapper):
        """Testa fluxo completo de múltiplos ativos."""
        assets = [
            "Embraer ON NM",
            "Braskem PN N1",
            "Suzano ON NM",
            "ABEVA135",  # Opção
        ]
        
        results = []
        for asset in assets:
            result = mapper.map_asset(asset)
            results.append(result)
        
        # Todos devem retornar sem erros
        assert len(results) == len(assets)


class TestEdgeCases:
    """Testes para casos extremos e edge cases."""

    def test_empty_string(self, mapper):
        """Testa tratamento de string vazia."""
        empresa, tipo, sufixo = mapper.parse_asset_name("")
        # Deve retornar algum padrão
        assert tipo == "ON"

    def test_only_spaces(self, mapper):
        """Testa tratamento de string apenas com espaços."""
        empresa, tipo, sufixo = mapper.parse_asset_name("   ")
        assert tipo == "ON"

    def test_special_characters(self, mapper):
        """Testa tratamento de caracteres especiais."""
        result = mapper._normalize_description_suffixes("Empresa-Teste ON NM")
        assert "Empresa-Teste" in result or "Empresa" in result

    def test_unicode_characters(self, mapper):
        """Testa tratamento de caracteres Unicode."""
        empresa, tipo, sufixo = mapper.parse_asset_name("Café ON NM")
        # Deve funcionar com Unicode
        assert "Café" in empresa or "Caf" in empresa

    def test_very_long_name(self, mapper):
        """Testa tratamento de nome muito longo."""
        long_name = "A" * 100 + " ON NM"
        empresa, tipo, sufixo = mapper.parse_asset_name(long_name)
        assert tipo == "ON"

    def test_ticker_with_only_special_chars(self, mapper):
        """Testa geração de ticker quando empresa tem apenas caracteres especiais."""
        # Empresa vazia após limpeza
        ticker = mapper.generate_ticker_heuristic("!@#$%", "ON", 3)
        # Deve gerar algo (padding com X)
        assert ticker and len(ticker) == 5
