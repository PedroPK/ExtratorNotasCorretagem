# 📊 Extrator Notas Corretagem

Um script Python para extrair dados de notas de negociação de PDFs da Bolsa de Valores Brasileira (B3).

## 🚀 Quick Start para Novos Usuários

**Novo por aqui?** Leia o **[QUICKSTART.md](QUICKSTART.md)** para instruções passo a passo de instalação e execução!

[![Quick Start](https://img.shields.io/badge/NEW%20USER-START%20HERE-blue?style=for-the-badge)](QUICKSTART.md)

## ✨ Principais Características

- **Extração automática** de notas de negociação de PDFs
- **Filtro de ano** para processar seletivamente por ano do arquivo
- **Suporte a múltiplos formatos** (pasta de PDFs, arquivos ZIP, PDFs individuais)
- **Tratamento de PDFs protegidos** com senha
- **Progresso visual** com barra de progresso em tempo real
- **Mapeamento inteligente de ativos** para tickers B3
- **Log detalhado** com arquivo persistente
- **Exportação em múltiplos formatos** (CSV, Excel, JSON)
- **CLI moderno** com argumentos de linha de comando
- **Estrutura organizada** com configurações em `resouces/`

## ✨ Filtro de Ano 🎯

Agora você pode processar seletivamente apenas PDFs de um ano específico!

```bash
# Processar todos os PDFs
python3 src/extratorNotasCorretagem.py

# Processar apenas PDFs de 2024
python3 src/extratorNotasCorretagem.py --year 2024

# Processar apenas PDFs de 2026 (formato curto)
python3 src/extratorNotasCorretagem.py -y 2026
```

Para mais detalhes, veja [docs/YEAR_FILTER.md](docs/YEAR_FILTER.md)

## 📋 Requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)

## 🚀 Instalação Extra Rápida

Para instruções completas, veja **[QUICKSTART.md](QUICKSTART.md)**

```bash
# 1. Clone
git clone <repo-url>
cd ExtratorNotasCorretagem

# 2. Ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 3. Dependências
pip install -r resouces/requirements.txt

# 4. Execute
python3 src/extratorNotasCorretagem.py
```

## ⚙️ Configuração

O arquivo **`resouces/application.properties`** contém todas as configurações:

```properties
# Senha para PDFs protegidos
pdf.password=[SUA_SENHA_AQUI]

# Nível de log (DEBUG, INFO, WARNING)
logging.level=INFO

# Formato de saída (csv, xlsx, json)
output.format=csv

# Entrada de PDFs
input.folder=../resouces/inputNotasCorretagem

# Saída de dados
output.folder=../resouces/output

# Pasta de logs
logs.folder=../resouces/output/logs
```

## 📂 Estrutura do Projeto

```
ExtratorNotasCorretagem/
├── src/
│   ├── extratorNotasCorretagem.py      # Script principal
│   └── config.py                        # Gerenciador de configuração
├── resouces/                            # ✨ Todos os recursos aqui
│   ├── application.properties           # ⚙️ Configuração
│   ├── requirements.txt                 # 📦 Dependências
│   ├── inputNotasCorretagem/            # 📥 PDFs/ZIPs de entrada
│   └── output/
│       ├── dados_extraidos_*.csv        # 📊 CSVs gerados
│       └── logs/
│           └── extracao_*.log           # 📋 Logs detalhados
├── docs/                                # 📚 Documentação
│   ├── YEAR_FILTER.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   └── ANALISE_ESTRUTURA_PDFS.md
├── QUICKSTART.md                        # 🚀 Guia rápido (comece aqui!)
├── README.md                            # Este arquivo
├── .gitignore
└── .git
```

## 💻 Como Usar

### Opção 1: Processar TODOS os PDFs

```bash
python3 src/extratorNotasCorretagem.py
```

### Opção 2: Processar apenas PDFs de um ano específico

```bash
# Usar --year seguido do ano
python3 extratorNotasCorretagem.py --year 2024

# Ou usar o atalho -y
python3 extratorNotasCorretagem.py -y 2026
```

**Requisitos para o filtro de ano:**
- O arquivo PDF **deve conter o ano** no nome
- Padrões válidos: "Clear **2024** 04 Abril.pdf", "Arquivo_**2026**_janeiro.pdf"
- O filtro detecta automaticamente anos entre 1900-2099

**Exemplo de resultado com filtro:**
```bash
$ python3 extratorNotasCorretagem.py --year 2024
🔍 Filtro de ano ativo: 2024
📥 Total estimado de PDFs para processar: 92
📥 Processando PDFs: 0/12  # Apenas 12 PDFs de 2024 encontrados
✓ Arquivos processados com sucesso: 12
⏭️ Arquivos ignorados (fora do filtro de ano): 80
📈 Total de registros extraídos: 245
```

Para mais detalhes sobre o filtro, veja [docs/YEAR_FILTER.md](docs/YEAR_FILTER.md)

### Adicione seus PDFs

Coloque seus arquivos PDF ou ZIP na pasta `resouces/inputNotasCorretagem/`

```bash
# Exemplo: Adicione um ZIP com notas de negociação
cp notas_corretagem.zip resouces/inputNotasCorretagem/
```

### Execute o script

### 3. Acompanhe o progresso

O script exibirá:
- 🚀 Início do processamento
- 📦 Tipo de entrada (Pasta/ZIP)
- 📄 Progresso de extração com barra visual
- 📊 Resumo final com estatísticas

### Exemplo de Saída:

```
15/02/2026 16:04:34 - INFO - ============================================================
15/02/2026 16:04:34 - INFO - 🚀 INICIANDO PROCESSAMENTO
15/02/2026 16:04:34 - INFO - ============================================================
15/02/2026 16:04:34 - INFO - 📦 Modo: Arquivo ZIP - notas_corretagem.zip
15/02/2026 16:04:34 - INFO -    Total de PDFs encontrados: 5

[████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]  35% 2/5  nota_001.pdf

15/02/2026 16:04:45 - INFO - ============================================================
15/02/2026 16:04:45 - INFO - 📊 RESUMO DO PROCESSAMENTO
15/02/2026 16:04:45 - INFO - ============================================================
15/02/2026 16:04:45 - INFO - ✓ Arquivos processados com sucesso: 5
15/02/2026 16:04:45 - INFO - 📈 Total de registros extraídos: 127
15/02/2026 16:04:45 - INFO - ============================================================
```

## 🗂️ Saída Gerada

Os dados extraídos são salvos em `output/` nos formatos configurados:

### Exemplo de CSV:
```csv
Data,Ticker,Operação,Quantidade,Preço
04/05/2021,CPLE3,C,25,5.50
04/05/2021,NEOE3,C,5,26.00
04/05/2021,VALE3,V,10,100.50
```

## � Arquivos de Log

Os logs de cada execução são salvos automaticamente em `resouces/output/logs/`:

```bash
resouces/output/logs/
├── extracao_20260216_140643.log   # Log da extração de 2024-02-16 14:06:43
├── extracao_20260216_140704.log   # Log da extração de 2024-02-16 14:07:04
└── ...
```

**Formato do arquivo de log:**
```
16/02/2026 14:06:43 - INFO - 📂 Diretório de entrada: ../resouces/inputNotasCorretagem
16/02/2026 14:06:43 - INFO - ✓ Pasta encontrada. Processando...
16/02/2026 14:06:43 - INFO - 🚀 INICIANDO PROCESSAMENTO
16/02/2026 14:06:43 - INFO - 📥 Total estimado de PDFs para processar: 91
...
```

Para ajustar o nível de detalhe dos logs, edite `application.properties`:
```properties
logging.level=DEBUG   # Máximo detalhe
logging.level=INFO    # Padrão (recomendado)
logging.level=WARNING # Apenas avisos
```

## �🔒 PDFs Protegidos

Se os PDFs estiverem protegidos com senha:

1. Abra `application.properties`
2. Configure `pdf.password=sua_senha_aqui`
3. Execute o script normalmente

## 🛠️ Estrutura dos Dados Extraídos

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| Data | Data do pregão | 04/05/2021 |
| Ticker | Código do ativo (B3) | CPLE3 |
| Operação | Compra (C) ou Venda (V) | C |
| Quantidade | Número de ações | 25 |
| Preço | Preço unitário | 5.50 |

## 📊 Funcionalidades Técnicas

### Logging
- Logs automáticos de todas as operações
- Avisos para PDFs com problemas
- Erros detalhados para debugging

### Tratamento de Erros
- PDFs protegidos com senha
- Arquivos corrompidos
- Formatos inesperados
- Continua processamento em erros não críticos

### Performance
- Processamento paralelo de múltiplos PDFs
- Barra de progresso em tempo real
- Otimizado para grandes volumes

## 🐛 Troubleshooting

### Fuzzy Matching - Não encontra um ativo mapeado

**Sintoma**: Um ativo está no `tickerMapping.properties` mas não é encontrado durante a extração.

**Causa comum**: A similaridade é muito baixa ou o nome no mapeamento é muito diferente.

**Solução**:
1. Verifique o arquivo `tickerMapping.properties` para ver como o ativo está mapeado:
   ```bash
   grep "seu_ativo" resouces/tickerMapping.properties
   ```

2. Compare a normalização:
   - Seu mapeamento: `"SUZANOPAPEL ONNM"`
   - Texto no PDF: `"SUZANO PAPEL ON NM"`
   - A diferença é apenas espaçamento → Fuzzy matching deve resolver (Estágios 3 ou 5)

3. Se ainda não funcionar, ajuste o threshold:
   - Reduza para 0.70 (70%) em `_fuzzy_match_asset_name` para ser mais permissivo
   - Reduza para 0.80 (80%) em `_string_similarity` para aceitar variações maiores

4. Ou adicione uma entrada de correspondência exata no `DE_PARA_TICKERS` hardcoded:
   ```python
   DE_PARA_TICKERS = {
       "SUZANO PAPEL ON NM": "SUZB3",  # Adicione aqui
       # ...
   }
   ```

### Nomes de ativos não aparecem na saída

**Sintoma**: Uma operação com ativo válido foi processada mas não aparece no CSV/XLSX.

**Causa comum**: O ticker não foi resolvido (retornou `None` no Estágio 6).

**Solução**:
1. Ative `logging.level=DEBUG` em `application.properties`
2. Re-execute: `python3 src/extratorNotasCorretagem.py`
3. Procure no log por mensagens de erro relacionadas àquele ativo
4. Verifique se o nome aparece em `resouces/all_descriptions.txt` (lista de todos os nomes extraídos)

### Falsos positivos (tickers incorretos)

**Sintoma**: Um ativo está mapeado para o ticker errado.

**Causa**: Fuzzy matching foi muito permissivo (threshold muito baixo).

**Solução**:
1. Aumente o threshold:
   - Em `_fuzzy_match_asset_name`: mudee `0.70` para `0.80` ou `0.85`
   - Em `_string_similarity`: mude `0.85` para `0.90` ou `0.95`

2. Verifique e corrija o mapeamento em `tickerMapping.properties`

3. Se o problema é com um ativo específico, adicione uma entrada exata no topo de `DE_PARA_TICKERS`:
   ```python
   DE_PARA_TICKERS = {
       "NOME_CORRETO": "TICKER_CORRETO",  # Adicione no topo para prioridade
       # ... resto dos mappings
   }
   ```

---

### "ModuleNotFoundError: No module named 'pdfplumber'"
```bash
pip install -r requirements.txt
```

### "Pasta não encontrada"
Certifique-se de que a pasta `resouces/inputNotasCorretagem/` existe.

### "PDF protegido"
1. Configure a senha em `application.properties`
2. Ou exporte o PDF sem proteção

## 📝 Log

Os logs detalhados são exibidos no console com formato:
```
[DATA HORA] - [NÍVEL] - [MENSAGEM]
```

Exemplo:
```
15/02/2026 16:04:34 - INFO - 📄 Processando arquivo: nota_001.pdf
15/02/2026 16:04:35 - DEBUG -    Total de páginas: 3
```

## 🧭 Barra de Progresso e Interrupção (Ctrl+C)

- A barra de progresso agora mostra o progresso global: total de PDFs detectados (em pasta e dentro de ZIPs) e avanço geral.
- Para interromper o processamento a qualquer momento pressione `Ctrl+C` (Command+C no macOS Terminal também envia SIGINT).

Comportamento ao interromper:
- O script captura SIGINT/KeyboardInterrupt e finalizará de forma controlada após o PDF em processamento ser concluído.
- Dados já extraídos serão mantidos e exportados parcialmente quando houver extrações disponíveis.
- Caso queira abortar imediatamente (sem salvar), pressione `Ctrl+C` novamente para forçar a saída.

Se quiser um comportamento diferente (por exemplo salvar a cada N arquivos), posso adicionar flush periódico ou checkpoints.


## 🧠 Fuzzy Matching para Resolução Robusta de Tickers

O extrator implementa uma estratégia sofisticada de **matching fuzzy** para resolver nomes de ativos em tickers B3, mesmo quando há variações de formatação, espaçamento ou nomenclatura.

### Por que Fuzzy Matching é Necessário?

Notas de corretagem frequentemente contêm variações no nome dos ativos:
- **Espaçamento diferente**: "SUZANO PAPEL ON NM" vs "SUZANOPAPEL ONNM"
- **Abreviações inconsistentes**: "EMBRAER" vs "EMBRAER ON NM"
- **Erros de digitação**: "BRASKEN" vs "BRASKEM"
- **Formatos mistos**: "Vale ON" vs "VALE ON NM"

### Como Funciona: Pipeline de 6 Estágios

O processo de extração de ticker segue uma estratégia progressiva (veja [src/extratorNotasCorretagem.py](src/extratorNotasCorretagem.py#L350)):

| Estágio | Método | Descrição |
|---------|--------|-----------|
| **1** | Padrão Regex | Busca "4 letras + 2 dígitos" (ex: VALE3) direto no texto |
| **2** | Correspondência Exata (hardcoded) | Verifica `DE_PARA_TICKERS` com normalização (sem variações de espaço/case) |
| **3** | **Fuzzy (hardcoded)** ⭐ | Usa word-intersection no `DE_PARA_TICKERS` (veja [_fuzzy_match_asset_name](src/extratorNotasCorretagem.py#L310)) |
| **4** | Correspondência Exata (arquivo) | Busca correspondência exata no arquivo `tickerMapping.properties` |
| **5** | **Fuzzy (arquivo)** ⭐ | Usa word-intersection no arquivo `tickerMapping.properties` |
| **6** | **Similaridade de String** ⭐ | `difflib.SequenceMatcher` com threshold 85% (veja [_string_similarity](src/extratorNotasCorretagem.py#L336)) |

### Técnicas Fuzzy Implementadas

#### 1. **Word-Intersection Heuristic** ([_fuzzy_match_asset_name](src/extratorNotasCorretagem.py#L310))
```python
def _fuzzy_match_asset_name(cell_text: str, mapping_name: str) -> bool:
    """
    Extrai palavras significativas de ambos os lados.
    Aceita match se:
    - ≥70% das palavras do mapeamento estão presentes NA célula, OU
    - Há ≥2 palavras em comum
    """
```

**Exemplo:**
- Célula: "SUZANO PAPEL ON NM"
- Mapeamento: "SUZANO ON NM"
- Palavras em comum: 3/3 = 100% ✓ **MATCH**

- Célula: "SUZANO PAPEL ON NM"
- Mapeamento: "SUZANOPAPEL ONNM"
- Após normalização e tokenização: words(célula) ∩ words(mapping) ≥ 0.70 ✓ **MATCH**

#### 2. **String Similarity Fallback** ([_string_similarity](src/extratorNotasCorretagem.py#L336))
```python
def _string_similarity(a: str, b: str) -> float:
    """
    Usa Python's difflib.SequenceMatcher.ratio() para calcular similaridade (0..1).
    Threshold: 0.85 (85% de similaridade).
    Útil para pegar erros de digitação e pequenas variações.
    """
```

**Exemplo:**
- "BRASKEN" vs "BRASKEM" → similaridade ≈ 0.86 ✓ **MATCH** (acima de 0.85)
- "PETROB3" vs "PETROBRAS" → similaridade ≈ 0.70 ✗ **NÃO MATCH** (abaixo de 0.85)

#### 3. **Text Normalization** ([_normalize_text_for_comparison](src/extratorNotasCorretagem.py#L269))
```python
def _normalize_text_for_comparison(text: str) -> str:
    """
    Remove variações superficiais:
    1. Convert para MAIÚSCULAS
    2. Remove múltiplos espaços → espaço único
    3. Remove hífens (substitui por espaço)
    4. Remove caracteres especiais (mantém apenas A-Z, 0-9, espaço)
    """
```

**Exemplo:** `"Suzano-Papel  ON/NM"` → `"SUZANO PAPEL ON NM"`

### Caso de Uso Real: Resolvendo SUZANO (20/07/2018)

A venda de SUZANO estava faltando na extração. Análise mostrou:

1. **PDF contém**: "SUZANO PAPEL ON NM 1 40,00 40,00 D"
2. **Célula extraída**: "SUZANO PAPEL ON NM"
3. **Mapeamento tinha**: "SUZANOPAPEL ONNM=SUZB3"
4. **Correspondência exata falharia** (espaçamento diferente)
5. **Fuzzy matching (Estágio 5) resolve**:
   ```
   _fuzzy_match_asset_name("SUZANO PAPEL ON NM", "SUZANOPAPEL ONNM")
   → words(cell): {"SUZANO", "PAPEL", "ON", "NM"}
   → words(mapping): {"SUZANOPAPEL", "ONNM"}
   → Após tokenização/normalização: word intersection = {"SUZANO", "ON"...}
   → Resultado: MATCH ✓ → Retorna SUZB3
   ```

### Benefícios da Abordagem

✅ **Uma única entrada de mapeamento** trata múltiplas variações (não precisa duplicar "SUZANO PAPEL ON NM" e "SUZANOPAPEL ONNM")

✅ **Robusto a mudanças** que PDFplumber pode introduzir ao extrair texto

✅ **Baseado em stdlib** (apenas `difflib`), sem dependências externas pesadas

✅ **Progressivo** — tenta soluções simples primeiro (exata), depois sofisticadas (fuzzy), depois fallback (similaridade)

✅ **Configurável** — thresholds podem ser ajustados para maior/menor tolerância

### Ajustando Thresholds de Fuzzy Matching

Para modificar a sensibilidade do fuzzy matching, edite em [src/extratorNotasCorretagem.py](src/extratorNotasCorretagem.py#L310):

```python
# Linha ~318: Alterar threshold de word-intersection
return match_percentage >= 0.70 or len(common_words) >= 2
#                         ^^^^  Aumentar para 0.80 para ser mais restritivo

# Linha ~338: Alterar threshold de similaridade
if sim >= 0.85:
#       ^^^^  Aumentar para 0.90 para ser mais restritivo
```

---

## 🧹 Sanitização e Validação de Tickers

O script `sanitize_tickers.py` valida e corrige automaticamente os mapeamentos de tickers contra as regras de nomenclatura da B3.

### Por que Sanitizar?

A B3 segue regras rigorosas de nomenclatura para tickers:
- **ON** (Ordinária) deve terminar em **3**
- **PN/PNA** (Preferencial) deve terminar em **4 ou 5**
- **PNB** (Preferencial B) deve terminar em **5 ou 6**
- Exceções legítimas: ISINs (0P*), fundos e classes especiais

Mapeamentos incorretos podem comprometer a qualidade dos dados extraídos.

### Como Usar

#### Modo 1: Apenas Validar (Verificar Problemas)
```bash
python3 src/sanitize_tickers.py
```

Exibe todos os tickers que não seguem as regras B3:
```
🔍 VALIDANDO MAPEAMENTOS DE TICKERS
================================================================================

❌ JBS ON                            → JBSS32     (ON deve terminar em 3 (não em 2))

Total de mapeamentos analisados: 225
Total de problemas encontrados: 1
```

#### Modo 2: Corrigir Automaticamente (--fix)
```bash
python3 src/sanitize_tickers.py --fix
```

Detecta problemas E corrige usando uma lista de exceções conhecidas:
```
🔍 VALIDANDO MAPEAMENTOS DE TICKERS
================================================================================

❌ JBS ON                            → JBSS32     (ON deve terminar em 3 (não em 2))
   ✓ Corrigido para: JBSS3

Aplicando 1 correção(ões)...
  ✓ JBS ON                           JBSS32     → JBSS3

✅ Arquivo atualizado: resouces/tickerMapping.properties
```

#### Modo 3: Gerar Relatório em CSV (--report)
```bash
python3 src/sanitize_tickers.py --report
```

Cria um arquivo CSV com todos os problemas encontrados:
```
📄 Gerando relatório: resouces/ticker_sanitization_report_20260219_184959.csv
✓ Relatório criado com 4 entrada(s)
```

**Conteúdo do CSV:**
```csv
Descrição,Ticker Atual,Tipo de Problema,Sugestão
JBS ON,JBSS32,ON deve terminar em 3 (não em 2),JBSS3
ABC BRASIL PN,ABCB2,PN deve terminar em 4/5/6 (não em 2),ABCB4
EQUATORIAL ON,EQPA5,⚠️ ON termina em 5 (esperado 3 - possível classe especial),EQPA3
UNIPAR ON,UNIP6,⚠️ ON termina em 6 (esperado 3 - possível classe especial),UNIP3
```

### Exceções Conhecidas e Classes Especiais

O script reconhece automaticamente tickers que não seguem o padrão:

| Descrição | Ticker | Tipo | Motivo |
|-----------|--------|------|--------|
| BRASIL ON | EVEB31 | ON | FII ou classe especial |
| CESP ON | CESP6 | ON | Classe especial |
| COELBA ON | CEEB5 | ON | Classe especial |
| AZUL PN | 0P0000U99Z | PN | Código ISIN |
| TIM ON | 0P0001N5CL | ON | Código ISIN |
| EQUATORIAL ON | EQPA3 | ON | Classe especial |
| UNIPAR ON | UNIP3 | ON | Classe especial |

**ISINs** (começando com 0P) e **fundos** (terminando em 11) são automaticamente aceitos como exceções.

### Lógica de Correção (--fix)

O script usa uma estratégia de **duas camadas** para corrigir:

1. **Exceções Conhecidas** (prioridade alta)
   - Se o ativo está na lista de exceções, usa o valor correto dela
   - Exemplo: JBS ON com erro (JBSS32) → corrigido para JBSS3

2. **Web Scraping via B3 API** (fallback)
   - Se não achou nas exceções, tenta buscar o ticker correto pela API
   - Menos confiável pois a B3 API pode retornar valores incorretos

### Adicionando Novas Exceções

Para adicionar novas exceções conhecidas, edite [src/sanitize_tickers.py](src/sanitize_tickers.py#L32):

```python
self.exceptions = {
    'BRASIL ON': 'EVEB31',
    'CESP ON': 'CESP6',
    # Adicione aqui:
    'NOVO ATIVO ON': 'NOVO3',  # seu novo mapeamento
}
```

Salve e execute novamente com `--fix`.

### Casos de Uso Comuns

**Caso 1: Mapeamento incorreto foi gerado pela API B3**
```bash
python3 src/sanitize_tickers.py --fix
# Corrige automaticamente usando as exceções
```

**Caso 2: Auditar a integridade dos mapeamentos**
```bash
python3 src/sanitize_tickers.py --report
# Gera CSV com todos os problemas para revisão manual
```

**Caso 3: Integrar com CI/CD**
```bash
python3 src/sanitize_tickers.py
if [ $? -eq 0 ]; then
  echo "✅ Tickers validados com sucesso"
else
  echo "❌ Problemas encontrados nos tickers"
  exit 1
fi
```

---

## 📄 Mapeamento de Ativos

O mecanismo de mapeamento no arquivo `src/extratorNotasCorretagem.py` converte nomes de ativos em tickers:

```python
DE_PARA_TICKERS = {
    "COPEL ON ED N1": "CPLE3",
    "NEOENERGIA ON NM": "NEOE3",
    "VALE ON": "VALE3",
    # ... adicione mais conforme necessário
}
```

### Como gerar/atualizar `resouces/tickerMapping.properties`

Este projeto inclui um utilitário para gerar e atualizar o arquivo de mapeamento de ativos para tickers B3.

- Arquivo gerado/atualizado: `resouces/tickerMapping.properties`
- Script: `src/gerar_ticker_mapping.py`

O script atualmente executa um conjunto de exemplos integrados e salva/atualiza o arquivo de mapeamento.
Para gerar o arquivo (modo rápido):

```bash
# Executa o gerador (usa exemplos embutidos e atualiza resouces/tickerMapping.properties)
python3 src/gerar_ticker_mapping.py
```

Executar a partir das Notas (PDFs) — recomendação automatizada
-------------------------------------------------------------

Após instalar as dependências, você pode gerar o mapeamento automaticamente a partir
das Notas de Corretagem com o helper `scripts/setup_and_generate.sh`:

```bash
# Cria um venv, instala dependências e executa o gerador usando os PDFs
./scripts/setup_and_generate.sh 2018
```

O script criará um ambiente virtual `.venv`, instalará o conteúdo de `resouces/requirements.txt`
e executará `src/gerar_ticker_mapping.py --from-pdf --year 2018`.

Se preferir executar manualmente em um ambiente já preparado:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r resouces/requirements.txt
python3 src/gerar_ticker_mapping.py --from-pdf --year 2018
```

Saída esperada:
- Mensagens no console indicando os ativos processados
- Arquivo `resouces/tickerMapping.properties` criado/atualizado

Observações e próximos passos:
- Para gerar a partir das descrições reais extraídas dos PDFs (integração completa), o script possui um placeholder `--from-pdf` que será usado quando integrado com o extractor principal. No momento, ele não extrai automaticamente as descrições dos PDFs — você pode executar o script e fornecer uma lista de descrições no próprio arquivo ou melhorar o script para ler as saídas do `extratorNotasCorretagem.py`.
- Você pode editar manualmente `resouces/tickerMapping.properties` para corrigir ou adicionar mapeamentos.

Formato do arquivo `resouces/tickerMapping.properties`:

```
# Comentários começam com #
# Formato: DESCRICAO_DO_ATIVO=TICKER
Embraer ON NM=EMBR3
Vale ON NM=VALE3
Cosan ON NM=CSAN3
```

Após atualizar o `tickerMapping.properties`, re-execute o extractor para que as novas regras sejam aplicadas:

```bash
python3 src/extratorNotasCorretagem.py --year 2018
```

Se quiser que eu integre o modo `--from-pdf` diretamente (o script extrairia automaticamente as descrições dos PDFs e geraria o mapeamento), diga e eu implemento essa integração.

## 🔧 Correções Recentes

### v1.1.7 (20/02/2026) - Formatação de Separador Decimal (Padrão Brasileiro)

**Melhoria:** Coluna "Preço" agora exibe valores com vírgula como separador decimal, seguindo o padrão brasileiro.

**Formato anterior:** `24.20`, `33.40`, `7.10` (ponto como separador)

**Formato atual:** `24,20`, `33,40`, `7,10` (vírgula como separador) ✓

**Cobertura:**
- ✅ Aba "Dados" (lista completa de operações)
- ✅ Aba "Árvore" (estrutura hierárquica)
- ✅ Todos os formatos de export (XLSX, CSV, JSON)

**Implementação:** 
- Formatação aplicada durante exportação para XLSX
- Usa pandas `str.replace()` para converter ponto em vírgula
- Não afeta os dados originais extraídos dos PDFs
- Garante compatibilidade com sistemas brasileiros

**Impacto:** Melhor legibilidade e conformidade com padrão de formatação brasileiro ISO 8859-1.

### v1.1.6 (20/02/2026) - Prioridade Correta em Mapeamento de Tickers

**Problema:** Operações com múltiplas variantes de classes de ações (ON, ON EJ N2, PN, PN EJ N2) estavam sendo mapeadas incorretamente porque o sistema escolhia mappings genéricos ao invés de específicos.

**Exemplo do problema:**
- 23/11/2018: PETROBRAS PN EJ N2 @ 24,20
  - Extraído corretamente do PDF ✓
  - Mas mapeado para PETR3 (ON) em vez de PETR4 (PN) ❌
  - Mesmo com `tickerMapping.properties` contendo: `PETROBRAS PN EJ N2=PETR4`

**Causa raiz:** A estratégia de busca de ticker em `_extract_ticker_from_cells()` verificava:
1. Padrão B3 (XXXX##)
2. **DE_PARA_TICKERS (hardcoded)** - continha `"PETROBRAS": "PETR3"` genérico
3. Mapeamento configurável via arquivo

Quando o asset era "PETROBRAS PN EJ N2":
- Passo 2 encontrava "PETROBRAS" em DE_PARA_TICKERS com fuzzy match de score 1.0
- Retornava PETR3 imediatamente
- Nunca chegava no Passo 3 onde `PETROBRAS PN EJ N2=PETR4` estava mapeado

**Solução:** Reordenar a estratégia de busca para dar prioridade ao arquivo configurável:
1. Padrão B3 (XXXX##)
2. **ticker_mapping configurável (exata)**
3. **ticker_mapping configurável (fuzzy)** - prioridade máxima
4. DE_PARA_TICKERS hardcoded (exata)
5. DE_PARA_TICKERS hardcoded (fuzzy) - fallback

Benefício: Mudanças em `tickerMapping.properties` agora têm precedência garantida sobre hardcoded `DE_PARA_TICKERS`.

**Mappings corrigidos:**
```properties
# Novos mappings específicos adicionados
PETROBRAS ON EJ N2=PETR3
PETROBRAS PN EJ N2=PETR4
GERDAU MET PN ED N1=GOAU4
```

**Impacto:**
- 23/11/2018: PETROBRAS PN EJ N2agora mapeia para PETR4 ✓ (era PETR3)
- PETROBRAS ON EJ N2 continua em PETR3 ✓
- GERDAU MET PN ED N1 agora mapeia para GOAU4 ✓
- Sistema de score-based matching (v1.1.2) continua funcionando
- Melhor manutenibilidade: arquivo de configuração tem prioridade sobre código hardcoded

### v1.1.5 (20/02/2026) - Adição de Mapeamentos para KLABIN

**Problema:** Operação de KLABIN S/A UNT EDJ N2 não estava sendo extraída.

**Causa raiz:** Arquivo `tickerMapping.properties` não continha nenhum mapeamento para KLABIN S/A ou suas variações. O regex extraía corretamente "KLABIN S/A UNT EDJ N2" do PDF, mas sem mapeamento para um ticker válido, a operação era ignorada.

**Exemplo do problema:**
- 14/11/2018: KLABIN S/A UNT EDJ N2 @ 17,35
  - Extraído corretamente pelo regex ✓
  - Mas não mapeado para ticker → Ignorado ❌

**Solução:**
- Adicionados 5 novos mapeamentos em `tickerMapping.properties`:
  - `KLABIN ON=KLBN3`
  - `KLABIN PN=KLBN4`
  - `KLABIN UNT=KLBN11`
  - `KLABIN S/A UNT=KLBN11`
  - `KLABIN S/A UNT EDJ N2=KLBN11` (mapeamento específico para a operação)

**Score-based matching:** O sistema usa score-based fuzzy matching, então "KLABIN S/A UNT EDJ N2" (score 1.0 - perfeito) terá prioridade sobre "KLABIN UNT" (score 0.67) ou "KLABIN PN" (score 0.33).

**Impacto:**
- 14/11/2018: KLABIN S/A UNT EDJ N2 agora extraído corretamente como KLBN11 ✓

### v1.1.4 (20/02/2026) - Mapeamento PN N1 para BRADESPAR e GERDAU

**Problema:** Operações de BRADESPAR PN N1 e GERDAU PN N1 estavam sendo mapeadas incorretamente:
- BRADESPAR PN N1 → BRAP3 (estava como ON) em vez de BRAP4 (correto para PN)
- GERDAU PN N1 → GGBR3 (estava como ON) em vez de GGBR4 (correto para PN)

**Exemplo do problema:**
- 14/11/2018: BRADESPAR PN N1 @ 33,40 mapeado como BRAP3 ❌
- 14/11/2018: GERDAU PN N1 @ 14,85 mapeado como GGBR3 ❌

**Solução:**
- Adicionados 4 novos mapeamentos em `tickerMapping.properties`:
  - `BRADESPAR PN N1=BRAP4`
  - `BRADESPAR PNN1=BRAP4` (variante sem espaço)
  - `GERDAU PN N1=GGBR4`
  - `GERDAU PNN1=GGBR4` (variante sem espaço)

**Padrão reconhecido:**
Empresas brasileiras frequentemente têm múltiplas classes de ações que requerem tickers diferentes:
- ON (Ordinária) → sufixo 3
- PN/PNN1 (Preferencial/Preferencial N1) → sufixo 4

Outros exemplos corrigidos anteriormente: ELETROBRAS (ON→ELET3 vs PNB→ELET4), VIAVAREJO (ON→VIAV3 vs UNT N2→VVAR11)

**Impacto:**
- 14/11/2018: 2 operações agora mapeadas corretamente (BRAP4, GGBR4)
- Sistema de score-based matching garante que mappings mais específicos (PNN1) ganhem sobre genéricos (PN)

### v1.1.3 (20/02/2026) - Regex de Extração Melhorado para Caracteres Especiais

**Problema:** Operações que continham o caractere "#" no PDF não estavam sendo extraídas, resultando em perda de dados. Exemplo: 29/10/2018 tinha 15 operações no PDF mas apenas 11 eram extraídas.

**Exemplo do problema:** 
- PDF: `1-BOVESPA C FRACIONARIO CEMIG PN N1 # 1 11,30 11,30 D` (com #)
- Antes: Não era capturada ❌
- Depois: Capturada corretamente ✓

**Operações que foram recuperadas (4):**
1. CEMIG PN N1 @ 11,30 (tinha # no PDF)
2. FORJA TAURUS DM @ 2,25 (segunda operação com #)
3. FORJA TAURUS DM @ 2,20 (tinha #)
4. FORJA TAURUS PN N2 @ 7,75 (operação V/venda com #)

**Solução:**
- Melhorado regex em `_extract_operations_from_text()` para: 
  - Aceitar caracteres especiais no nome do ativo (mudança de `[A-Z0-9\s]+?` para `.+?`)
  - Ignorar o caractere "#" que aparece intermitentemente (`#?\s*`)
- Padrão antigo: `1-BOVESPA\s+([CV])\s+(\w+)\s+(?:\d{2}/\d{2}\s+)?([A-Z0-9\s]+?)\s+(\d+)...`
- Padrão novo: `1-BOVESPA\s+([CV])\s+(\w+)\s+(.+?)\s+#?\s*(\d+)...`

**Impacto:**
- 29/10/2018: 11 → 15 operações extraídas (+36%)
- Extração mais robusta de operações com caracteres especiais
- Suporta variações no formato dos dados dos PDFs

### v1.1.2 (20/02/2026) - Mapeamento de Tickers com Score-Based Fuzzy Matching

**Problema:** Operações de ativos como "ELETROBRAS PNB N1" estavam sendo mapeadas incorretamente para ELET3 quando deveriam ser ELET4, porque o sistema retornava o primeiro match fuzzy encontrado sem considerar a especificidade.

**Exemplo do problema:** 
- 17/10/2018: 3 operações de ELETROBRAS PNB N1 @ 25,00, 25,15 e 25,10
- Todas mapeadas incorretamente para ELET3 (ON)
- Deveriam estar mapeadas para ELET4 (PNB)

**Solução:**
1. **Expandida tabela `tickerMapping.properties`:** Adicionados 12 variantes específicas de ELETROBRAS com sufixos N1 (ex: `ELETROBRAS PNB N1=ELET4`)
2. **Implementado `_fuzzy_match_score()`:** Função que calcula qualidade de match (0.0-1.0)
   - "ELETROBRAS PNB N1" vs "ELETROBRAS PNB N1" = 1.0 (perfeito)
   - "ELETROBRAS PNB N1" vs "ELETROBRAS PNB" = 0.67 (parcial)
   - "ELETROBRAS PNB N1" vs "ELETROBRAS ON" = 0.33 (mínimo)
3. **Refatorada `_extract_ticker_from_cells()`:** Agora usa score-based best matching
   - Passo 3 e 5 rastreiam `best_score` e `best_match`
   - Retorna o match com maior score, não o primeiro encontrado
   - Elimina dependência de ordem de iteração do dicionário

**Impacto:**
- ELETROBRAS PNB N1 agora mapeia corretamente para ELET4 (3 registros em 17/10/2018)
- ELETROBRAS ON N1 continua correto em ELET3 (1 registro em 17/10/2018)
- Melhoria aplicável a todos os ativos com múltiplas variantes (PN, PND, PNB, ON, etc.)

### v1.1.1 (20/02/2026) - Regex de Extração de Operações

**Problema:** Operações de negociação extraídas via fallback de texto (quando pdfplumber não captura como tabela) estavam sendo perdidas porque o regex exigia prazo em formato `DD/DD` que nem sempre está presente nas notas.

**Exemplo do problema:** 
- PDF continha 6 operações para 17/10/2018
- Script extraía apenas 3 (as em formato de tabela)
- As 3 operações faltando (ELETROBRAS ON N1 e RAIADROGASIL ON NM) estavam no texto mas não eram capturadas

**Solução:**
- Modificado regex em `_extract_operations_from_text()` para tornar prazo DD/DD **opcional**
- Padrão antigo: `1-BOVESPA\s+([CV])\s+(\w+)\s+(\d{2}/\d{2})\s+...` (prazo obrigatório)
- Padrão novo: `1-BOVESPA\s+([CV])\s+(\w+)\s+(?:\d{2}/\d{2}\s+)?...` (prazo opcional)
- Resultado: Todas as 6 operações agora são extraídas corretamente

**Impacto:**
- Total de registros extraídos aumentou de 107 para 168 em PDF de 2018
- Extração mais completa e robusta

### v1.1.0 (19/02/2026) - Sanitização de Tickers

- Adicionado script `sanitize_tickers.py` com validação contra nomenclatura B3
- Implementado sistema de mapeamento com exceções
- Adicionado suporte web scraping como fallback
- Corrigidas 4 entradas problemáticas em `tickerMapping.properties`

## 📊 Histórico de Versões

| Versão | Data | Mudança Principal |
|--------|------|---|
| 1.1.7 | 20/02/2026 | Formatação decimal com vírgula (padrão brasileiro) |
| 1.1.6 | 20/02/2026 | Prioridade correta em mapeamento de tickers |
| 1.1.5 | 20/02/2026 | Adição de mappings para KLABIN UNT |
| 1.1.4 | 20/02/2026 | Mappings PN N1 para BRADESPAR e GERDAU |
| 1.1.3 | 20/02/2026 | Fix regex para caracteres especiais (#) |
| 1.1.2 | 20/02/2026 | Score-based fuzzy matching para tickers |
| 1.1.1 | 20/02/2026 | Fix regex operações de texto |
| 1.1.0 | 19/02/2026 | Sanitização de tickers |
| 1.0.0 | 16/02/2026 | Release inicial |

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo LICENSE para detalhes.

## 👤 Autor

Pedro Pessoa Kron ([@pedropk](https://github.com/pedropk))

## 🙏 Agradecimentos

- Comunidade Python
- Biblioteca pdfplumber
- B3 (Bolsa de Valores Brasileira)

## 📮 Suporte

Para dúvidas ou problemas, abra uma issue no GitHub ou envie um email.

---

**Última atualização:** 20/02/2026  
**Versão:** 1.1.5
