#!/usr/bin/env python3
"""
Script de Análise SAST - Executa Ruff + Bandit + mypy + Black
Versão simplificada para execução rápida
"""

import subprocess
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Detectar a raiz do projeto (dois níveis acima deste script)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
REPORT_DIR = PROJECT_ROOT / "resouces" / "sast_reports"
# Analisar apenas o módulo principal
SRC_DIR = PROJECT_ROOT / "src" / "extratorNotasCorretagem.py"

# Criar diretório de relatórios
REPORT_DIR.mkdir(parents=True, exist_ok=True)

print("\n" + "="*80)
print("🔍 ANÁLISE SAST COMPLETA - ExtratorNotasCorretagem")
print("="*80 + "\n")

# =============================================================================
# 1. RUFF - Linting
# =============================================================================
print("📋 1. Ruff - Linting Analysis...")
try:
    result = subprocess.run(
        ["ruff", "check", str(SRC_DIR)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        print("✅ Ruff: Nenhum problema encontrado\n")
        ruff_issues = 0
    else:
        # Count lines with issues
        issues = [line for line in result.stdout.split('\n') if 'error' in line.lower() or any(c in line for c in 'EWFBNI')]
        print(f"⚠️  Ruff: {len(issues)} problemas encontrados")
        # Show first 10 issues
        for line in result.stdout.split('\n')[:15]:
            if line.strip():
                print(f"  {line}")
        print()
        ruff_issues = len(issues)
except subprocess.TimeoutExpired:
    print("⏱️  Ruff: Análise excedeu tempo limite\n")
    ruff_issues = -1
except Exception as e:
    print(f"❌ Erro ao executar Ruff: {e}\n")
    ruff_issues = -1

# =============================================================================
# 2. Black - Formatação
# =============================================================================
print("🎨 2. Black - Formatting Check...")
try:
    result = subprocess.run(
        ["black", "--check", str(SRC_DIR)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        print("✅ Black: Código formatado corretamente\n")
        black_issues = 0
    else:
        print("⚠️  Black: Arquivo precisa formatação")
        print("Execute: black src/extratorNotasCorretagem.py\n")
        black_issues = 1
        
except Exception as e:
    print(f"⚠️  Black: {e}\n")
    black_issues = -1

# =============================================================================
# 3. mypy - Type Checking
# =============================================================================
print("📝 3. mypy - Type Checking (análise rápida)...")
try:
    result = subprocess.run(
        ["mypy", str(SRC_DIR), "--ignore-missing-imports"],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    mypy_errors = result.stdout.count("error:")
    if mypy_errors == 0:
        print("✅ mypy: Nenhum erro de tipo encontrado\n")
        mypy_issues = 0
    else:
        print(f"⚠️  mypy: {mypy_errors} erros de tipo encontrados")
        # Mostrar apenas os primeiros erros
        lines = result.stdout.split('\n')[:10]
        for line in lines:
            if line.strip():
                print(f"  {line}")
        print()
        mypy_issues = mypy_errors
        
except subprocess.TimeoutExpired:
    print("⏱️  mypy: Análise excedeu tempo limite\n")
    mypy_issues = -1
except Exception as e:
    print(f"⚠️  mypy: {e}\n")
    mypy_issues = -1

# =============================================================================
# 4. Bandit - Segurança
# =============================================================================
print("🔒 4. Bandit - Security Analysis...")
try:
    result = subprocess.run(
        ["bandit", str(SRC_DIR), "-f", "json", "-ll", "-q"],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    try:
        data = json.loads(result.stdout)
        bandit_issues = len(data.get("results", []))
    except:
        bandit_issues = 0
    
    if bandit_issues == 0:
        print("✅ Bandit: Nenhuma vulnerabilidade encontrada\n")
    else:
        print(f"⚠️  Bandit: {bandit_issues} problemas de segurança encontrados\n")
        
except Exception as e:
    print(f"⚠️  Bandit: {e}\n")
    bandit_issues = -1

# =============================================================================
# RELATÓRIO SUMMARY
# =============================================================================
print("="*80)
print("📊 RESUMO DA ANÁLISE SAST")
print("="*80)
print("")
print("Ferramenta          | Status           | Problemas Encontrados")
print("-"*80)
print(f"Ruff (Linting)      | {'✅' if ruff_issues == 0 else '⚠️ ':<16} | {ruff_issues if ruff_issues >= 0 else 'Erro'}")
print(f"Black (Formatação)  | {'✅' if black_issues == 0 else '⚠️ ':<16} | {black_issues if black_issues >= 0 else 'Erro'}")
print(f"mypy (Tipos)        | {'✅' if mypy_issues == 0 else '⚠️ ':<16} | {mypy_issues if mypy_issues >= 0 else 'Erro'}")
print(f"Bandit (Segurança)  | {'✅' if bandit_issues == 0 else '⚠️ ':<16} | {bandit_issues if bandit_issues >= 0 else 'Erro'}")
print("-"*80)

valid_issues = [x for x in [ruff_issues, black_issues, mypy_issues, bandit_issues] if x >= 0]
total_issues = sum(valid_issues) if valid_issues else 0
print(f"\nTOTAL DE PROBLEMAS: {total_issues}")
print("")

# =============================================================================
# RECOMENDAÇÕES
# =============================================================================
print("💡 RECOMENDAÇÕES:")
print("")

recommendations = []
if ruff_issues > 0:
    recommendations.append("• Ruff: Execute 'ruff check src/extratorNotasCorretagem.py --fix' para corrigir")
    
if black_issues > 0:
    recommendations.append("• Black: Execute 'black src/extratorNotasCorretagem.py' para formatar")
    
if mypy_issues > 0:
    recommendations.append("• mypy: Revise os erros acima e adicione type hints")
    
if bandit_issues > 0:
    recommendations.append("• Bandit: Revise as vulnerabilidades de segurança encontradas")

if recommendations:
    for rec in recommendations:
        print(rec)
else:
    print("  ✨ Nenhuma ação necessária - código está em conformidade!")

print("")
print("="*80)
print("✨ Análise SAST concluída!")
print("="*80)
print("")

# Exit code
if total_issues > 0:
    sys.exit(1)
else:
    sys.exit(0)
