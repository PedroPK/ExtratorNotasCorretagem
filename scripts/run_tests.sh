#!/bin/bash
# Run all tests with coverage report
# Usage: ./scripts/run_tests.sh or bash scripts/run_tests.sh

# Vai para a raiz do projeto (um nível acima)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

echo "🧪 ExtratorNotasCorretagem - Suite de Testes Automatizados"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Install dependencies if needed
if ! command -v pytest &> /dev/null; then
    echo "📦 Instalando pytest..."
    pip install pytest pytest-cov -q
fi

echo "▶️  Executando testes..."
echo ""

# Run tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "📊 Relatório de cobertura gerado em: htmlcov/index.html"
echo "═══════════════════════════════════════════════════════════"
