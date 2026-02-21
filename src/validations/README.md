# 📋 Scripts de Validação e Teste

Este diretório contém scripts auxiliares para validação, debugging e análise do extrator de notas de corretagem.

## 📁 Scripts por Categoria

### 🧪 Testes de Extração
- **test_extraction_fix.py** - Valida se as correções de regex funcionam corretamente
- **test_regex.py** - Testa padrões de regex para extração de operações
- **test_mapping.py** - Testa mapeamento de ativos para tickers

### 🔍 Debug de PDFs
- **debug_pdf.py** - Análise detalhada de conteúdo de PDF
- **debug_pdf_avancado.py** - Ferramentas avançadas de inspeção de PDFs
- **debug_simple.py** - Debug simples de arquivos PDF
- **dump_pdf_samples.py** - Extrai amostras de dados dos PDFs

### 📊 Análise de Dados
- **analisar_tabelas.py** - Analisa estrutura de tabelas extraídas
- **test_unmapped.py** - Identifica ativos não mapeados
- **test_mapping.py** - Valida tickers mapeados

### 🔧 Ferramentas de Validação
- **check_exports.py** - Valida exportações em XLSX
- **check_braskem_tickers.py** - Verifica mapeamento de tickers BRASKEM
- **debug_braskem.py** - Debug específico para empresa BRASKEM
- **separate_options.py** - Separa opções de ações do arquivo de mapeamento
- **teste_logging.py** - Testa sistema de logging

## 🚀 Uso Típico

```bash
# Testar extração de um PDF
python3 src/validations/debug_pdf.py <arquivo.pdf>

# Validar mapeamento de tickers
python3 src/validations/test_mapping.py

# Verificar dados exportados
python3 src/validations/check_exports.py
```

## 📝 Notas

- Esses scripts não são necessários para o funcionamento da aplicação principal
- Use-os para validar correções, investigar problemas ou analisar dados
- Mantenha a pasta `src/validations/` para organização do projeto
