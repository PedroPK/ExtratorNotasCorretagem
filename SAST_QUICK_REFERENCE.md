# SAST Quick Reference Guide

## 🚀 Quick Commands

### Run Complete SAST Analysis
```bash
python3 analyze_sast.py
```
*Outputs: Summary table + recommendations + exit code*

### Run Individual Tools

**Ruff Linting**
```bash
# Check for issues
ruff check src/

# Auto-fix issues
ruff check src/ --fix

# Check specific file
ruff check src/extratorNotasCorretagem.py

# Show specific rule codes
ruff check src/ --select E501  # Line too long
ruff check src/ --select F      # Undefined names
ruff check src/ --select I      # Import issues
```

**Black Formatting**
```bash
# Check formatting (no changes)
black --check src/

# Apply formatting
black src/

# Format single file
black src/extratorNotasCorretagem.py

# Check with diff
black --diff src/
```

**Bandit Security**
```bash
# Quick scan
bandit -r src/

# JSON output
bandit -r src/ -f json

# Only HIGH/CRITICAL
bandit -r src/ -ll

# Exclude test directories
bandit -r src/ --exclude tests
```

**mypy Type Checking**
```bash
# Basic check (may timeout)
mypy src/

# Check with ignore missing imports
mypy src/ --ignore-missing-imports

# Check single file
mypy src/extratorNotasCorretagem.py

# Quick check (no strict mode)
mypy src/ --no-strict --ignore-missing-imports
```

---

## 📊 Status Codes

### CLI Exit Codes

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | ✅ All checks passed | No action needed |
| 1 | ⚠️ Issues found | Review recommendations |
| 2 | ❌ Error during analysis | Check tool installation |

### Check Status Icons

| Icon | Status | Meaning |
|------|--------|---------|
| ✅ | PASS | Zero issues, fully compliant |
| ⚠️ | WARNING | Minor issues, review recommendations |
| ❌ | FAIL | Critical issues, action required |
| ⏱️ | TIMEOUT | Check timed out, may need optimization |

---

## 🔧 Configuration Reference

### Ruff Rules Selected
```
E   - pycodestyle errors
W   - pycodestyle warnings
F   - undefined names, unused imports
I   - import formatting
N   - naming conventions
UP  - Python version upgrades
B   - bugbear (additional checks)
```

### Ruff Rules Ignored
```
D   - docstring formatting (optional)
E501 - line too long (handled by Black)
W503 - line break before binary operator
```

### Black Settings
```
Line length: 100 characters
Target Python: 3.8+
Quote style: Double quotes
Indentation: 4 spaces
```

### mypy Settings
```
Strict mode: Enabled
Allow untyped defs: true
Ignore missing imports: true
Target directory: src/
```

### Bandit Settings
```
Severity level: -ll (HIGH/CRITICAL only)
Exclude: /test, /.venv
Include all security tests: true
```

---

## 🎯 Common Workflows

### Fix All Ruff Issues Automatically
```bash
ruff check src/ --fix
```

### Format Code + Check
```bash
black src/
python3 analyze_sast.py
```

### Check Before Commit
```bash
# Quick pre-commit check
ruff check src/extratorNotasCorretagem.py && \
black --check src/extratorNotasCorretagem.py && \
bandit -r src/
```

### Full Quality Assurance
```bash
# Run tests
pytest tests/

# Run SAST
python3 analyze_sast.py

# Commit if all pass
git add -A
git commit -m "chore: pass SAST analysis"
```

---

## 📈 Performance Notes

### Execution Times (Typical)
- Ruff: ~2 seconds
- Black: ~3 seconds
- Bandit: ~5 seconds
- mypy: ~30 seconds (or timeout at 30s limit)

### Optimization Tips
1. **Ruff**: Very fast, can run on every save
2. **Black**: Medium speed, run before commits
3. **Bandit**: Moderate speed, -ll flag for faster scanning
4. **mypy**: Slow, run occasionally or on specific files

### Timeout Handling
- If mypy times out: Use `--no-strict` or check individual files
- If Bandit times out: Use `-ll` flag to reduce rules
- If Black times out: Single file analysis is faster

---

## 🐛 Troubleshooting

### Issue: Tool not found
```bash
# Reinstall SAST tools
pip install ruff bandit mypy black --upgrade
```

### Issue: Permission denied
```bash
# Make scripts executable
chmod +x analyze_sast.py run_sast.sh
```

### Issue: Import errors in mypy
```bash
# Ignore missing imports (already configured)
mypy src/ --ignore-missing-imports
```

### Issue: Black formats differently than expected
```bash
# Check line length setting
black --check --diff src/extratorNotasCorretagem.py
```

---

## 📚 Integration Examples

### Pre-commit Hook (Optional)
Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
python3 analyze_sast.py
if [ $? -ne 0 ]; then
  echo "SAST check failed. Fix issues before committing."
  exit 1
fi
```

### GitHub Actions CI/CD (Optional)
```yaml
name: SAST Analysis
on: [push, pull_request]
jobs:
  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: python3 analyze_sast.py
```

---

## 📖 Reference Documentation

| File | Purpose |
|------|---------|
| `pyproject.toml` | Ruff, Black, mypy config |
| `.bandit` | Bandit security rules |
| `analyze_sast.py` | Python-based analysis runner |
| `run_sast.sh` | Bash-based analysis runner |
| `SAST_RESULTS.md` | Latest analysis results |
| `TESTING.md` | Test suite documentation |

---

## ✅ Latest Status

```
Date: 2024-02-15
Ruff:   ✅ 0 issues
Black:  ✅ Formatted (1 file fixed)
Bandit: ✅ 0 vulnerabilities
mypy:   ⚠️ Timeout (non-blocking)

Overall: ✅ COMPLIANT
```

---

*For detailed analysis results, see SAST_RESULTS.md*  
*For test suite info, see TESTING.md*
