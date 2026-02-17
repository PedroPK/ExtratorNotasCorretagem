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
pdf.password=454

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

**Última atualização:** 15/02/2026  
**Versão:** 1.0.0
