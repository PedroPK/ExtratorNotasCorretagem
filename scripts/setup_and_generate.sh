#!/usr/bin/env bash
set -euo pipefail

# Script helper: cria venv, instala requirements e executa o gerador de tickers
# Uso: ./scripts/setup_and_generate.sh [--year YEAR]

YEAR=${1:-}
ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

# 1) Criar/ativar venv
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

# Ativa o venv nesta sessão
# shellcheck disable=SC1091
source .venv/bin/activate

# 2) Instalar dependências
pip install --upgrade pip
pip install -r resouces/requirements.txt

# 3) Executar gerador a partir dos PDFs
if [ -n "$YEAR" ]; then
  python3 src/gerar_ticker_mapping.py --from-pdf --year "$YEAR"
else
  python3 src/gerar_ticker_mapping.py --from-pdf
fi
