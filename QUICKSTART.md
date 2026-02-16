# 🚀 Quick Start - Instruções de Instalação e Execução

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Git
- Terminal/CMD (macOS, Linux ou Windows)

**Verificar versão do Python:**
```bash
python3 --version
# Esperado: Python 3.8.0 ou maior
```

## 📥 1. Clonar o Repositório

```bash
# Clonar o projeto
git clone <url-do-repositorio> ExtratorNotasCorretagem
cd ExtratorNotasCorretagem
```

## 🔧 2. Criar Ambiente Virtual

### macOS / Linux
```bash
# Criar ambiente virtual
python3 -m venv .venv

# Ativar ambiente virtual
source .venv/bin/activate

# Você deve ver (.venv) no início da linha de comando
```

### Windows
```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
.venv\Scripts\activate

# Você deve ver (.venv) no início da linha de comando
```

## 📦 3. Instalar Dependências

Todas as dependências estão listadas em `resouces/requirements.txt`

```bash
# Instalar pacotes
pip install -r resouces/requirements.txt
```

**Pacotes que serão instalados:**
- `pdfplumber>=0.11.0` - Leitura de PDFs
- `pandas>=3.0.0` - Manipulação de dados
- `cryptography` - Suporte a PDFs criptografados
- `tqdm>=4.66.0` - Barras de progresso

## 📂 3. Adicionar PDFs para Processar

Os PDFs devem ser colocados em: `resouces/inputNotasCorretagem/`

```bash
# Exemplo: Copiar seus PDFs para a pasta de entrada
cp seus_pdfs/*.pdf resouces/inputNotasCorretagem/

# Ou organizar em subpastas mantendo a estrutura
cp -r seus_arquivos/* resouces/inputNotasCorretagem/
```

## ⚙️ 4. Configurar (Opcional)

O arquivo `resouces/application.properties` contém configurações:

```properties
# PDF com senha?
pdf.password=454

# Nível de detalhe dos logs (DEBUG, INFO, WARNING)
logging.level=INFO

# Formato de saída (csv, xlsx, json)
output.format=csv
```

**Editar configurações:**
```bash
nano resouces/application.properties  # macOS/Linux
notepad resouces/application.properties  # Windows
```

## 🚀 5. Executar o Extrator

### Processar TODOS os PDFs
```bash
python3 src/extratorNotasCorretagem.py
```

### Processar apenas um ano específico
```bash
# Apenas 2024
python3 src/extratorNotasCorretagem.py --year 2024

# Apenas 2026 (forma curta)
python3 src/extratorNotasCorretagem.py -y 2026
```

### Ver opções disponíveis
```bash
python3 src/extratorNotasCorretagem.py --help
```

## 📊 6. Onde Estão os Resultados?

Após a execução, você encontrará:

**CSVs gerados:**
```
resouces/output/dados_extraidos_YYYYMMDD_HHMMSS.csv
```

**Logs detalhados:**
```
resouces/output/logs/extracao_YYYYMMDD_HHMMSS.log
```

**Exemplo de saída:**
```
resouces/
├── inputNotasCorretagem/           (entrada)
│   └── *.pdf
└── output/                         (saída)
    ├── dados_extraidos_*.csv       (resultados)
    └── logs/
        └── extracao_*.log          (logs)
```

## 📘 Estrutura de Dados Extraídos

O CSV gerado possui as colunas:

| Coluna | Descrição | Exemplo |
|--------|-----------|---------|
| Data | Data da negociação | 08/01/2026 |
| Ticker | Código do ativo B3 | GARE11 |
| Operação | C (Compra) ou V (Venda) | C |
| Quantidade | Número de ações | 50 |
| Preço | Preço unitário | 8.98 |

**Exemplo de dados:**
```csv
Data,Ticker,Operação,Quantidade,Preço
08/01/2026,GARE11,C,50,8.98
08/01/2026,PLAG11,C,4,50.58
08/01/2026,PORD11,C,100,8.06
```

## 🔍 7. Exemplos de Uso

### Exemplo 1: Extrair eatos de 2024
```bash
# Executar
python3 src/extratorNotasCorretagem.py --year 2024

# Resultado esperado
📥 Total estimado de PDFs para processar: 92
📥 Processar apenas PDFs de 2024: 12 encontrados
✓ Arquivos processados com sucesso: 12
⏭️ Arquivos ignorados: 80
📈 Total de registros extraídos: 245

# Saída: resouces/output/dados_extraidos_YYYYMMDD_HHMMSS.csv
```

### Exemplo 2: Extrair todos (sem filtro)
```bash
# Executar
python3 src/extratorNotasCorretagem.py

# Resultado esperado
📥 Total estimado de PDFs para processar: 92
📥 Processando todos os PDFs
✓ Arquivos processados com sucesso: 92
📈 Total de registros extraídos: 1933

# Saída: resouces/output/dados_extraidos_YYYYMMDD_HHMMSS.csv
```

## ❓ Troubleshooting

### "ModuleNotFoundError: No module named 'pdfplumber'"
```bash
# Solução: Ativar .venv e reinstalar dependências
source .venv/bin/activate  # macOS/Linux
pip install -r resouces/requirements.txt
```

### "Pasta inputNotasCorretagem não encontrada"
```bash
# Solução: Criar a pasta e adicionar PDFs
mkdir -p resouces/inputNotasCorretagem
cp seus_pdfs/*.pdf resouces/inputNotasCorretagem/
```

### "Nenhum registro foi extraído"
- Verifique se os PDFs têm o formato esperado (Clear Corretora)
- Confira se a senha está correta em `resouces/application.properties`
- Veja os logs em `resouces/output/logs/extracao_*.log`

### Os logs não aparecem no console
- Aumentar nível de logging em `resouces/application.properties`:
  ```properties
  logging.level=DEBUG
  ```

## 📚 Documentação Adicional

Para mais detalhes, veja:
- **README.md** - Documentação completa do projeto
- **docs/YEAR_FILTER.md** - Detalhe sobre filtro de ano
- **docs/IMPLEMENTATION_SUMMARY.md** - Resumo técnico
- **resouces/application.properties** - Configurações disponíveis

## 💡 Dicas

1. **Primeiro uso:** Execute sem filtro (`python3 src/extratorNotasCorretagem.py`) para testar
2. **Verificar logs:** Abra `resouces/output/logs/` para ver detalhes de cada execução
3. **Processar por ano:** Use `--year` para dividir em menores chunks (mais rápido)
4. **Integração:** O CSV segue formato padrão, fácil de importar em Excel/Sheets

## 🎯 Próximos Passos

Após a primeira execução bem-sucedida:

1. ✅ Validar dados no CSV (colunas, formato)
2. ✅ Importar em suas ferramentas favoritas (Excel, Python, etc.)
3. ✅ Agendar execuções periódicas se necessário
4. ✅ Verificar logs para troubleshooting

---

**Dúvidas ou problemas?** Consulte a documentação completa em `docs/` ou revise os logs em `resouces/output/logs/`

**Versão:** 2.2.0  
**Data:** 16/02/2026
