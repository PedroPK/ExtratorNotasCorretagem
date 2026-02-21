"""
Configurações compartilhadas para toda a suite de testes
Fixtures e setup para os testes automatizados
"""

import sys
import os
import pytest
import pandas as pd
from pathlib import Path

# Adiciona src ao path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from config import ConfigManager
    config_available = True
except ImportError:
    config_available = False


@pytest.fixture(scope="session")
def config():
    """Carrega configuração da aplicação"""
    if config_available:
        return ConfigManager()
    else:
        # Retorna mock se config não estiver disponível
        return None


@pytest.fixture(scope="session")
def sample_data_dir():
    """Retorna diretório com PDFs de teste"""
    return Path(__file__).parent.parent / "resouces" / "inputNotasCorretagem"


@pytest.fixture
def output_dir(tmp_path):
    """Diretório temporário para outputs de teste"""
    return tmp_path


@pytest.fixture
def sample_dataframe():
    """DataFrame de exemplo para testes de formatação e sorting"""
    data = {
        'Data': ['23/11/2018', '03/10/2018', '03/10/2018', '04/10/2018'],
        'Ticker': ['PETR4', 'FORJ3', 'SUZB3', 'BTOW3'],
        'Operação': ['C', 'C', 'C', 'C'],
        'Quantidade': [1, 20, 2, 2],
        'Preço': ['24.20', '5.02', '44.00', '28.90']
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_unsorted_dataframe():
    """DataFrame desordenado para testar função de sorting"""
    data = {
        'Data': ['04/10/2018', '23/11/2018', '03/10/2018', '03/10/2018'],
        'Ticker': ['BTOW3', 'PETR4', 'SUZB3', 'FORJ3'],
        'Operação': ['C', 'C', 'C', 'C'],
        'Quantidade': [2, 1, 2, 20],
        'Preço': ['28.90', '24.20', '44.00', '5.02']
    }
    return pd.DataFrame(data)


@pytest.fixture
def ticker_mapping_dict():
    """Dicionário de mapeamento de tickers para testes"""
    return {
        'PETROBRAS PN EJ N2': 'PETR4',
        'PETROBRAS ON EJ N2': 'PETR3',
        'GERDAU MET PN ED N1': 'GOAU4',
        'KLABIN S/A UNT EDJ N2': 'KLBN11',
        'B2W DIGITAL ON': 'BTOW3',
        'FLEURY ON': 'FLRY3',
        'BRADESPAR PN N1': 'BRAD2',
    }


@pytest.fixture
def de_para_tickers_dict():
    """Dicionário hardcoded de fallback (DE_PARA_TICKERS)"""
    return {
        'PETROBRAS': 'PETR3',
        'VALE': 'VALE3',
        'BRADESCO': 'BBDC4',
    }
