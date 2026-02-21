# 🧪 Suite de Testes Automatizados

Suite completa de testes para o **ExtratorNotasCorretagem**, cobrindo todos os cenários identificados nas conversas recentes.

## 📋 Conteúdo da Suite

### Arquivos de Teste

| Arquivo | Cobertura | Testes |
|---------|-----------|--------|
| `test_ticket_mapping.py` | Mapeamento de tickers (v1.1.6) | 15+ testes |
| `test_decimal_formatting.py` | Formatação decimal com vírgula (v1.1.7) | 18+ testes |
| `test_data_sorting.py` | Ordenação por Data + Ticker | 15+ testes |
| `test_export_formats.py` | CSV, XLSX, JSON | 18+ testes |
| `test_regex_patterns.py` | Padrões de extração | 20+ testes |
| `test_logging_output.py` | Formatação de logs | 17+ testes |

**Total: 100+ testes automatizados**

---

## 🚀 Instalação

### 1. Instalar pytest e dependências

```bash
pip install -r resouces/requirements.txt
```

Ou instalar apenas pytest:

```bash
pip install pytest pytest-cov
```

### 2. Confirmar instalação

```bash
pytest --version
# pytest 7.x.x -- Python ...
```

---

## ▶️ Como Executar os Testes

### Executar todas os testes

```bash
pytest
```

Com output verboso:

```bash
pytest -v
```

### Executar testes específicos

**Por arquivo:**
```bash
pytest tests/test_decimal_formatting.py -v
```

**Por classe:**
```bash
pytest tests/test_ticket_mapping.py::TestTickerMappingPriority -v
```

**Por função específica:**
```bash
pytest tests/test_decimal_formatting.py::TestDecimalFormatting::test_price_uses_comma_separator -v
```

### Executar com marcadores

**Testes unitários rápidos:**
```bash
pytest -m unit
```

**Testes de formatação:**
```bash
pytest -m formatting
```

**Testes de mapeamento:**
```bash
pytest -m mapping
```

### Gerar relatório de cobertura

```bash
pytest --cov=src --cov-report=html
# Abre resouces/htmlcov/index.html
```

Com relatório no terminal:

```bash
pytest --cov=src --cov-report=term-missing
```

---

## 📊 Cenários de Teste Cobertos

### ✅ v1.1.6 - Ticket Mapping Priority

**Problema:** PETROBRAS PN EJ N2 mapeava para PETR3 (genérico) em vez de PETR4 (específico)

**Testes:**
- `test_petrobras_pn_maps_to_petr4()` - Mapeia corretamente para PETR4
- `test_petrobras_on_maps_to_petr3()` - ON mapeia para PETR3
- `test_gerdau_met_pn_maps_to_goau4()` - Novos mappings adicionados
- `test_exact_match_in_ticker_mapping_beats_fuzzy()` - Prioridade respeitada
- Testes de score-based matching fuzzy

**Status:** ✅ 15+ testes

### ✅ v1.1.7 - Decimal Formatting (Padrão Brasileiro)

**Problema:** Preços formatados com ponto (24.20) em vez de vírgula (24,20)

**Testes:**
- `test_all_prices_have_comma_separator()` - Todos com vírgula
- `test_price_values_preserved_after_formatting()` - Valores preservados
- `test_format_in_dados_sheet()` - Formatação na aba Dados
- `test_format_in_arvore_sheet()` - Formatação na aba Árvore
- `test_brazilian_locale_formatting()` - Conformidade ISO 8859-1
- Testes de edge cases (preços vazios, inteiros, múltiplas casas)

**Status:** ✅ 18+ testes

### ✅ Secondary Sorting (Data + Ticker)

**Problema:** Dados ordenados apenas por Data, tickers dentro de mesma data em ordem aleatória

**Testes:**
- `test_data_sorted_ascending()` - Data em ordem ascendente
- `test_ticker_sorted_within_same_date()` - Tickers alfabéticos
- `test_sort_order_is_data_then_ticker()` - Combinação correta
- `test_large_dataset_sorting()` - Teste com 180+ registros
- `test_sorting_preserves_data()` - Sem perda de dados
- Testes de performance (sorting rápido)

**Status:** ✅ 15+ testes

### ✅ Export Formats (CSV, XLSX, JSON)

**Problema simulado:** Validar múltiplos formatos de exportação

**Testes:**
- `test_csv_export_creates_file()` - CSV criado
- `test_xlsx_multiple_sheets()` - Duas abas (Dados + Árvore)
- `test_xlsx_precio_has_comma_separator()` - Preços com vírgula em XLSX
- `test_json_preserves_data()` - Dados preservados em JSON
- `test_all_formats_export_same_data_volume()` - Consistência entre formatos
- Testes de encoding UTF-8

**Status:** ✅ 18+ testes

### ✅ Padrões Regex

**Cobertura:** Extração de operações, preços, tickers, datas, quantidades

**Testes:**
- `test_extract_operation_buy/sell()` - Extrai C/V
- `test_extract_simple_price()` - Preços XX.XX
- `test_extract_4char_ticker()` - PETR4, VALE3
- `test_extract_5char_ticker()` - KLBN11
- `test_extract_date_ddmmyyyy()` - Data formato brasileiro
- Testes de caracteres especiais (#, S/A, etc)

**Status:** ✅ 20+ testes

### ✅ Formatação de Logs

**Problema anterior:** Progress bar criava espaçamento excessivo

**Testes:**
- `test_log_format_has_timestamp()` - Timestamp presente
- `test_log_no_excessive_spacing()` - Sem linhas vazias desnecessárias
- `test_log_no_progress_bar_artifacts()` - Sem artifacts de barra
- `test_file_processing_log_format()` - Logs de processamento corretos
- Testes de múltiplos níveis (INFO, WARNING, ERROR)
- Teste de performance (1000 logs rápido)

**Status:** ✅ 17+ testes

---

## 📈 Exemplos de Execução

### Teste apenas formatação decimal

```bash
pytest tests/test_decimal_formatting.py -v
```

**Output esperado:**
```
test_decimal_formatting.py::TestDecimalFormatting::test_price_uses_comma_separator PASSED
test_decimal_formatting.py::TestDecimalFormatting::test_all_prices_have_comma_separator PASSED
...
========================= 18 passed in 0.15s =========================
```

### Teste mapeamento de tickers com alta verbosidade

```bash
pytest tests/test_ticket_mapping.py -vv
```

### Teste com relatório de cobertura

```bash
pytest --cov=src --cov-report=term-missing tests/
```

**Output esperado:**
```
tests/test_decimal_formatting.py::TestDecimalFormatting ... PASSED        [8%]
tests/test_data_sorting.py::TestDataSorting ... PASSED                   [18%]
...
========================= 100 passed in 1.23s =========================

----------- coverage: ... -----------
src/extratorNotasCorretagem.py    85%
src/config.py                      92%
```

---

## 🛠️ Estrutura de Fixtures

O arquivo `conftest.py` fornece fixtures compartilhadas:

```python
@pytest.fixture
def sample_dataframe():
    """DataFrame de exemplo"""
    
@pytest.fixture
def sample_unsorted_dataframe():
    """DataFrame desordenado para testes"""
    
@pytest.fixture
def ticker_mapping_dict():
    """Dicionário de mapeamento"""
    
@pytest.fixture
def de_para_tickers_dict():
    """Dicionário hardcoded (fallback)"""
```

---

## 📝 Adicionando Novos Testes

### Template de Novo Teste

```python
def test_nova_funcionalidade(sample_dataframe):
    """Descrição do que está sendo testado"""
    # Arrange (preparar dados)
    expected = "valor_esperado"
    
    # Act (executar a ação)
    result = sample_dataframe['coluna'].values[0]
    
    # Assert (verificar resultado)
    assert result == expected, f"Falhou: {result} != {expected}"
```

### Template de Nova Classe de Testes

```python
class TestNovaFuncionalidade:
    """Agrupa testes relacionados"""
    
    def test_caso_positivo(self, sample_dataframe):
        """Testa comportamento esperado"""
        pass
    
    def test_caso_negativo(self):
        """Testa tratamento de erro"""
        pass
    
    def test_edge_case(self):
        """Testa casos limites"""
        pass
```

---

## 🎯 Roadmap de Testes Futuros

- [ ] Testes de integração com PDFs reais (2018, 2025)
- [ ] Testes de performance para datasets grandes (10k+ registros)
- [ ] Testes de concorrência (processar múltiplos PDFs em paralelo)
- [ ] Testes de PDF protegido com senha
- [ ] Testes de fallback quando regex falha
- [ ] Testes de atualização de tickerMapping.properties
- [ ] Testes de tratamento de erro (PDF corrompido, etc)

---

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'pytest'"

```bash
pip install pytest pytest-cov
```

### Erro: "No tests ran"

Verificar:
```bash
pytest tests/ --collect-only  # Lista todos os testes encontrados
```

### Testes muito lentos

```bash
pytest -v --durations=10  # Mostra 10 testes mais lentos
```

### Limpar cache pytest

```bash
rm -rf .pytest_cache __pycache__ tests/__pycache__
pytest --cache-clear
```

---

## 📊 Métricas de Cobertura Alvo

| Componente | Cobertura Alvo |
|------------|---|
| `extratorNotasCorretagem.py` | 85%+ |
| `config.py` | 90%+ |
| Regex patterns | 95%+ |
| Formatação | 100% |
| Mapeamento | 95%+ |

---

## 📞 Contato & Dúvidas

Para adicionar novos cenários de teste ou reportar bugs:
- Criar issue no GitHub
- Descrever o cenário que não está coberto
- Fornecer reprodutor se possível

---

**Última atualização:** 20/02/2026
**Versão:** 1.0.0
**Status:** ✅ Operacional - 100+ testes cobrindo v1.1.6 e v1.1.7
