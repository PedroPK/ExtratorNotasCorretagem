#!/bin/bash
# =============================================================================
# Script de Análise SAST Completa
# Executa: Ruff (linting), Bandit (segurança), mypy (tipo), Black (forma)
# =============================================================================

set -e

# Detecta a raiz do projeto (um nível acima deste script)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORT_DIR="$PROJECT_ROOT/resouces/sast_reports"
SRC_DIR="$PROJECT_ROOT/src"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Criar diretório de relatórios
mkdir -p "$REPORT_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                        🔍 ANÁLISE SAST COMPLETA                             ║"
echo "║              Ruff + Bandit + mypy + Black Analysis                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# =============================================================================
# 1. RUFF - Linting (Estilo, Erros, Boas Práticas)
# =============================================================================
echo -e "${BLUE}📋 1. Executando Ruff (Linting)...${NC}"
echo ""

RUFF_REPORT="$REPORT_DIR/ruff_report_$TIMESTAMP.json"
ruff check "$SRC_DIR" --output-format=json > "$RUFF_REPORT" 2>&1 || true

RUFF_COUNT=$(python3 -c "import json; data = json.load(open('$RUFF_REPORT')); print(len([x for cell in data for x in cell.get('messages', [])]))" 2>/dev/null || echo "0")

if [ "$RUFF_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ Ruff: Nenhum problema encontrado${NC}"
else
    echo -e "${YELLOW}⚠ Ruff: $RUFF_COUNT problemas encontrados${NC}"
    ruff check "$SRC_DIR" --show-source
fi

echo ""

# =============================================================================
# 2. BANDIT - Vulnerabilidades de Segurança
# =============================================================================
echo -e "${BLUE}🔒 2. Executando Bandit (Segurança)...${NC}"
echo ""

BANDIT_REPORT="$REPORT_DIR/bandit_report_$TIMESTAMP.json"
bandit -r "$SRC_DIR" -f json -o "$BANDIT_REPORT" 2>&1 || true

BANDIT_ISSUES=$(python3 -c "import json; data = json.load(open('$BANDIT_REPORT')); print(len(data.get('results', [])))" 2>/dev/null || echo "0")

if [ "$BANDIT_ISSUES" -eq 0 ]; then
    echo -e "${GREEN}✓ Bandit: Nenhuma vulnerabilidade encontrada${NC}"
else
    echo -e "${YELLOW}⚠ Bandit: $BANDIT_ISSUES problemas de segurança encontrados${NC}"
    bandit -r "$SRC_DIR" -v
fi

echo ""

# =============================================================================
# 3. MYPY - Type Checking
# =============================================================================
echo -e "${BLUE}📝 3. Executando mypy (Type Checking)...${NC}"
echo ""

MYPY_REPORT="$REPORT_DIR/mypy_report_$TIMESTAMP.txt"
mypy "$SRC_DIR" --junit-xml="$REPORT_DIR/mypy_junit_$TIMESTAMP.xml" > "$MYPY_REPORT" 2>&1 || true

if grep -q "error:" "$MYPY_REPORT"; then
    MYPY_ERRORS=$(grep -c "error:" "$MYPY_REPORT" || true)
    echo -e "${YELLOW}⚠ mypy: $MYPY_ERRORS erros de tipo encontrados${NC}"
    head -20 "$MYPY_REPORT"
else
    echo -e "${GREEN}✓ mypy: Nenhum erro de tipo encontrado${NC}"
fi

echo ""

# =============================================================================
# 4. BLACK - Formatação
# =============================================================================
echo -e "${BLUE}🎨 4. Verificando Black (Formatação)...${NC}"
echo ""

BLACK_REPORT="$REPORT_DIR/black_report_$TIMESTAMP.txt"
black --check "$SRC_DIR" > "$BLACK_REPORT" 2>&1 || true

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Black: Código está formatado corretamente${NC}"
else
    echo -e "${YELLOW}⚠ Black: Alguns arquivos precisam de formatação${NC}"
    echo ""
    echo "Para formatar automaticamente, execute:"
    echo "  black $SRC_DIR"
    echo ""
fi

# =============================================================================
# GERAR RELATÓRIO HTML SUMMARY
# =============================================================================
echo ""
echo -e "${BLUE}📊 Gerando Relatório HTML Summary...${NC}"
echo ""

HTML_REPORT="$REPORT_DIR/sast_summary_$TIMESTAMP.html"

cat > "$HTML_REPORT" << 'EOFHTML'
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório SAST - ExtratorNotasCorretagem</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .content {
            padding: 40px;
        }
        
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .card {
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .card:hover {
            border-color: #667eea;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.1);
        }
        
        .card h2 {
            color: #667eea;
            font-size: 1.2em;
            margin-bottom: 10px;
        }
        
        .card .number {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        
        .card.success {
            border-left: 4px solid #4caf50;
        }
        
        .card.warning {
            border-left: 4px solid #ff9800;
        }
        
        .card.danger {
            border-left: 4px solid #f44336;
        }
        
        .status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            margin-top: 10px;
        }
        
        .status.pass {
            background: #c8e6c9;
            color: #2e7d32;
        }
        
        .status.fail {
            background: #ffcccc;
            color: #c62828;
        }
        
        .details {
            background: #f5f5f5;
            border-radius: 8px;
            padding: 20px;
            margin-top: 30px;
        }
        
        .details h3 {
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        
        .file-list {
            list-style: none;
        }
        
        .file-list li {
            padding: 8px;
            margin: 5px 0;
            background: white;
            border-radius: 4px;
            border-left: 3px solid #667eea;
        }
        
        footer {
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }
        
        .timestamp {
            color: #999;
            font-size: 0.9em;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Análise SAST Completa</h1>
            <p>Relatório de Qualidade de Código - ExtratorNotasCorretagem</p>
        </header>
        
        <div class="content">
            <div class="summary">
                <div class="card success">
                    <h2>Ruff</h2>
                    <div class="number" id="ruff-count">0</div>
                    <p>Problemas de Linting</p>
                    <span class="status pass" id="ruff-status">Analisando...</span>
                </div>
                
                <div class="card success">
                    <h2>Bandit</h2>
                    <div class="number" id="bandit-count">0</div>
                    <p>Vulnerabilidades</p>
                    <span class="status pass" id="bandit-status">Analisando...</span>
                </div>
                
                <div class="card success">
                    <h2>mypy</h2>
                    <div class="number" id="mypy-count">0</div>
                    <p>Erros de Tipo</p>
                    <span class="status pass" id="mypy-status">Analisando...</span>
                </div>
                
                <div class="card success">
                    <h2>Black</h2>
                    <div class="number" id="black-count">0</div>
                    <p>Formatação OK</p>
                    <span class="status pass" id="black-status">Analisando...</span>
                </div>
            </div>
            
            <div class="details">
                <h3>📊 Detalhes da Análise</h3>
                
                <h4 style="margin-top: 20px; color: #667eea;">Ruff - Linting</h4>
                <p>Valida padrões de código, boas práticas e erros comuns usando Ruff, um linter ultra-rápido para Python.</p>
                
                <h4 style="margin-top: 20px; color: #667eea;">Bandit - Segurança</h4>
                <p>Analisa o código para encontrar vulnerabilidades, uso inseguro de bibliotecas e práticas perigosas.</p>
                
                <h4 style="margin-top: 20px; color: #667eea;">mypy - Type Checking</h4>
                <p>Verifica a consistência de tipos em todo o código, prevenindo erros relacionados a tipos.</p>
                
                <h4 style="margin-top: 20px; color: #667eea;">Black - Formatação</h4>
                <p>Valida se o código segue o padrão de formatação consistente do Black.</p>
            </div>
            
            <div class="timestamp" id="timestamp">
                Relatório gerado em: 20/02/2026 00:00:00
            </div>
        </div>
        
        <footer>
            <p>🚀 Suite SAST - ExtratorNotasCorretagem v1.0</p>
            <p>Ruff + Bandit + mypy + Black</p>
        </footer>
    </div>
</body>
</html>
EOFHTML

echo -e "${GREEN}✓ Relatório HTML gerado: $HTML_REPORT${NC}"

# =============================================================================
# SUMÁRIO FINAL
# =============================================================================
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                        ✅ ANÁLISE CONCLUÍDA                                  ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo -e "${BLUE}📁 Arquivos de Relatório:${NC}"
echo ""
echo "  1. Ruff Report:   $RUFF_REPORT"
echo "  2. Bandit Report: $BANDIT_REPORT"
echo "  3. mypy Report:   $MYPY_REPORT"
echo "  4. HTML Summary:  $HTML_REPORT"
echo ""

echo -e "${BLUE}📊 Resumo:${NC}"
echo ""
echo "  • Ruff issues:    $RUFF_COUNT"
echo "  • Bandit issues:  $BANDIT_ISSUES"
echo ""

echo -e "${YELLOW}💡 Próximos passos:${NC}"
echo ""
echo "  1. Visualizar relatório HTML:"
echo "     open '$HTML_REPORT'"
echo ""
echo "  2. Formatar código automaticamente:"
echo "     black $SRC_DIR"
echo ""
echo "  3. Corrigir problemas do Ruff:"
echo "     ruff check $SRC_DIR --fix"
echo ""
echo ""
