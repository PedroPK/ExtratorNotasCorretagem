#!/bin/bash
# Run all tests with coverage report
# Usage: ./run_tests.sh

cd "$(dirname "$0")" || exit 1

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
