# 🚀 Quick Start - Guia Rápido

Guia direto para instalar, configurar e executar a aplicação pela primeira vez.

## 1) Pré-requisitos

- Python 3.8+
- Git
- Terminal (macOS/Linux/Windows)

```bash
python3 --version
```

## 2) Instalação

```bash
# Clonar repositório
git clone <url-do-repositorio> ExtratorNotasCorretagem
cd ExtratorNotasCorretagem

# Criar ambiente virtual
python3 -m venv .venv

# Ativar ambiente (macOS/Linux)
source .venv/bin/activate

# Windows (PowerShell)
# .venv\Scripts\activate

# Instalar dependências
pip install -r resouces/requirements.txt
```

## 3) Configuração mínima

Edite `resouces/application.properties`:

```properties
pdf.password=
logging.level=INFO
output.format=csv
input.folder=../resouces/inputNotasCorretagem
output.folder=../resouces/output
logs.folder=../resouces/output/logs
```

## 4) Entrada de arquivos

Coloque seus PDFs (ou ZIPs com PDFs) em:

`resouces/inputNotasCorretagem/`

## 5) Execução

### Processar tudo

```bash
python3 src/extratorNotasCorretagem.py
```

### Processar por ano

```bash
python3 src/extratorNotasCorretagem.py --year 2024
# ou
python3 src/extratorNotasCorretagem.py -y 2024
```

### Processar por ticker

```bash
python3 src/extratorNotasCorretagem.py --ticker PSSA3
# ou
python3 src/extratorNotasCorretagem.py -t PSSA3
```

### Processar por ano e ticker

```bash
python3 src/extratorNotasCorretagem.py --year 2024 --ticker PSSA3
```

### Controlar a ordem de processamento dos arquivos

```bash
# Padrão: ordem alfabética pelo nome
python3 src/extratorNotasCorretagem.py

# Por data de modificação
python3 src/extratorNotasCorretagem.py --sort-by mtime

# Por data de criação (atalho -s)
python3 src/extratorNotasCorretagem.py -s ctime
```

### Ver ajuda da CLI

```bash
python3 src/extratorNotasCorretagem.py --help
```

## 6) Saídas

- Dados: `resouces/output/dados_extraidos_*.csv` (ou `xlsx/json`)
- Logs: `resouces/output/logs/extracao_*.log`

## 7) Troubleshooting rápido

### Erro de dependência (`ModuleNotFoundError`)

```bash
source .venv/bin/activate
pip install -r resouces/requirements.txt
```

### Pasta de entrada ausente

```bash
mkdir -p resouces/inputNotasCorretagem
```

### Nenhum registro extraído

- Verifique senha do PDF em `application.properties`
- Ajuste `logging.level=DEBUG` e revise os logs em `resouces/output/logs/`

## Leituras relacionadas

- Visão completa do projeto: [README.md](../README.md)
- Filtro de ano: [YEAR_FILTER.md](YEAR_FILTER.md)
- Histórico de correções: [RELEASE_NOTES.md](RELEASE_NOTES.md)
