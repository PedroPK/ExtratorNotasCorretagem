"""
Exemplo de Novo Teste - Template para adicionar cenários de teste

Este arquivo demostra como adicionar novos testes à suite automatizada.
Siga o padrão AAA (Arrange, Act, Assert) para melhor legibilidade.
"""

import pytest
import pandas as pd


class TestExemploNovoScenario:
    """
    Template para nova funcionalidade a testar
    
    Use esta classe como base para adicionar novos testes.
    Cada método deve testar um único comportamento.
    """
    
    def test_comportamento_positivo(self):
        """
        Teste o comportamento esperado / caminho feliz
        
        Padrão:
        1. Arrange: preparar dados/estado
        2. Act: executar a ação
        3. Assert: verificar resultado
        """
        # 1. Arrange - Preparar dados
        valor_entrada = 100
        valor_esperado = 100
        
        # 2. Act - Executar ação
        resultado = valor_entrada
        
        # 3. Assert - Verificar resultado
        assert resultado == valor_esperado, \
            f"Esperava {valor_esperado}, mas obtive {resultado}"
    
    def test_comportamento_negativo(self):
        """Teste tratamento de erro/entrada inválida"""
        # Arrange
        lista_vazia = []
        
        # Act & Assert - Tenta acessar índice que não existe
        with pytest.raises(IndexError):
            valor = lista_vazia[0]
    
    def test_edge_case(self):
        """Teste caso limite/exceção"""
        # Teste com valores vazios, nulos, máximos, etc
        test_cases = [
            ("", False),        # Vazio
            (None, False),      # Nulo
            ("valor", True),    # Normal
        ]
        
        for entrada, esperado in test_cases:
            resultado = bool(entrada)
            assert resultado == esperado, \
                f"Falhou para entrada: {entrada}"


class TestExemploComFixture:
    """Exemplo usando fixtures do conftest.py"""
    
    def test_usar_sample_dataframe(self, sample_dataframe):
        """
        Usa fixture compartilhada: sample_dataframe
        
        Fixtures disponíveis:
        - sample_dataframe: DataFrame com dados de teste
        - sample_unsorted_dataframe: DataFrame desordenado
        - ticker_mapping_dict: Dicionário de mapeamento
        - de_para_tickers_dict: Dicionário hardcoded
        - output_dir: Diretório temporário
        """
        # Arrange
        numero_linhas_esperado = 4
        
        # Act
        numero_linhas = len(sample_dataframe)
        
        # Assert
        assert numero_linhas == numero_linhas_esperado
    
    def test_usar_ticker_mapping(self, ticker_mapping_dict):
        """Usa fixture de mapeamento de tickers"""
        # Verifica que o mapeamento está disponível
        assert 'PETROBRAS PN EJ N2' in ticker_mapping_dict
        assert ticker_mapping_dict['PETROBRAS PN EJ N2'] == 'PETR4'


class TestExemploParametrizado:
    """
    Teste parametrizado: executa mesma lógica com múltiphos inputs
    
    Útil para testar múltiplos casos similar em um teste
    """
    
    @pytest.mark.parametrize("entrada,esperado", [
        ("24.20", "24,20"),
        ("5.02", "5,02"),
        ("44.00", "44,00"),
        ("0.50", "0,50"),
    ])
    def test_formato_preco(self, entrada, esperado):
        """Testa formatação de preço com múltiplas entradas"""
        # Arrange - já feito pelo parametrize
        
        # Act
        resultado = entrada.replace('.', ',')
        
        # Assert
        assert resultado == esperado


# ============================================================================
# COMO ADICIONAR NOVO TESTE
# ============================================================================

"""
1. Crie um novo arquivo em tests/test_nova_funcionalidade.py

2. Use o template abaixo:

    from conftest import *  # ou importe fixtures específicas
    
    class TestMinhaNovaFuncionalidade:
        def test_caso_1(self, sample_dataframe):
            # Seu teste aqui
            pass
        
        def test_caso_2(self):
            # Teste sem fixture
            pass

3. Execute o novo teste:
    pytest tests/test_nova_funcionalidade.py -v

4. Adicione ao README.md em tests/

5. Commit com mensagem descritiva

6. Execute suite completa:
    pytest tests/ -v
"""

# ============================================================================
# FIXTURES DISPONÍVEIS (definidas em conftest.py)
# ============================================================================

"""
@pytest.fixture
def config():
    # Carrega configuração da aplicação
    
@pytest.fixture
def sample_data_dir():
    # Diretório com PDFs de teste
    
@pytest.fixture
def output_dir(tmp_path):
    # Diretório temporário para outputs
    
@pytest.fixture
def sample_dataframe():
    # DataFrame com dados de teste
    # Colunas: Data, Ticker, Operação, Quantidade, Preço
    
@pytest.fixture
def sample_unsorted_dataframe():
    # DataFrame desordenado para testar sorting
    
@pytest.fixture
def ticker_mapping_dict():
    # Dicionário de mapeamento de tickers
    
@pytest.fixture
def de_para_tickers_dict():
    # Dicionário hardcoded (fallback)
"""

# ============================================================================
# MARCADORES DISPONÍVEIS
# ============================================================================

"""
Use @pytest.mark.XXX para categorizar testes:

@pytest.mark.unit
def test_coisa():
    pass

@pytest.mark.slow
def test_coisa_lenta():
    pass

Executar apenas unit tests:
    pytest tests/ -m unit

Marcadores definidos em pytest.ini:
- unit: Testes unitários rápidos
- integration: Testes de integração com PDFs reais
- slow: Testes que levam mais tempo
- formatting: Testes de formatação
- extraction: Testes de extração
- mapping: Testes de mapeamento
- sorting: Testes de ordenação
"""

# ============================================================================
# EXEMPLO COMPLETO
# ============================================================================

"""
Imagine que você quer testar uma função nova: calcular_media_preca()

1. Crie tests/test_calculos.py:

    import pytest
    from meu_modulo import calcular_media_preco
    
    class TestCalculoDeMedia:
        
        def test_media_simples(self):
            # Arrange
            precos = [10.0, 20.0, 30.0]
            esperado = 20.0
            
            # Act
            resultado = calcular_media_preco(precos)
            
            # Assert
            assert resultado == esperado
        
        @pytest.mark.parametrize("precos,esperado", [
            ([10.0], 10.0),
            ([10.0, 20.0], 15.0),
            ([10.0, 20.0, 30.0], 20.0),
        ])
        def test_media_com_diferentes_tamanhos(self, precos, esperado):
            resultado = calcular_media_preco(precos)
            assert resultado == esperado
        
        def test_lista_vazia(self):
            with pytest.raises(ValueError):
                calcular_media_preco([])

2. Execute:
    pytest tests/test_calculos.py -v

3. Adicione ao README:
    ## calcular_media_preco()
    
    Valida cálculo de média de preços.
    - 3 testes, todos passando

4. Done! ✅
"""
