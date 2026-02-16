# 📅 Filtro de Ano - Documentação

## Visão Geral
O filtro de ano permite processar seletivamente apenas PDFs de um ano específico, baseado no ano presente no nome do arquivo.

## Requisitos
- O arquivo PDF **deve conter o ano** no seu nome
- O padrão de detecção é: `\b(19|20)\d{2}\b` (qualquer string com formato de ano entre 1900-2099)
- Exemplos válidos: "Clear **2024** 04 Abril.pdf", "Arquivo_**2026**_janeiro.pdf"
- Exemplos inválidos: "Arquivo.pdf", "Clear_Jan.pdf" (sem ano no nome)

## Uso

### 1. Processar TODOS os PDFs (sem filtro)
```bash
python3 extratorNotasCorretagem.py
```

### 2. Processar apenas PDFs de um ano específico
```bash
# Usando --year
python3 extratorNotasCorretagem.py --year 2024

# Usando atalho -y
python3 extratorNotasCorretagem.py -y 2026
```

## Exemplos Práticos

### Exemplo 1: Extrair apenas dados de 2024
```bash
python3 extratorNotasCorretagem.py --year 2024
```

**Resultado esperado:**
```
🔍 Filtro de ano ativo: 2024
📥 Total estimado de PDFs para processar: 92
📥 Processando PDFs: 0/12  # Apenas 12 PDFs de 2024
✓ Arquivos processados com sucesso: 12
⏭️ Arquivos ignorados (fora do filtro de ano): 80
📈 Total de registros extraídos: 245
```

### Exemplo 2: Extrair apenas dados de 2026
```bash
python3 extratorNotasCorretagem.py -y 2026
```

**Resultado esperado:**
```
🔍 Filtro de ano ativo: 2026
📥 Total estimado de PDFs para processar: 92
📥 Processando PDFs: 0/1  # Apenas 1 PDF de 2026
✓ Arquivos processados com sucesso: 1
⏭️ Arquivos ignorados (fora do filtro de ano): 91
📈 Total de registros extraídos: 20
```

## Comportamento do Filtro

### Quando usar filtro
- ✅ Processar dados de um ano fiscal específico
- ✅ Validação incremental (processar por ano)
- ✅ Reduzir tempo de processamento
- ✅ Executar em paralelo (ano 2024 em um terminal, 2025 em outro)

### Quando não usar filtro
- Processar toda base de dados
- Validações globais que necessitam de todos os anos

## Funcionamento Interno

### Função: `_extract_year_from_filename()`
```python
def _extract_year_from_filename(filename: str) -> Optional[int]:
    """Extrai ano do nome do arquivo usando regex."""
    # Procura por padrão (19|20)YY
    # Retorna: int (ex: 2024) ou None se não encontrar
```

**Exemplos:**
| Filename | Resultado |
|----------|-----------|
| Clear 2024 04 Abril.pdf | 2024 |
| Clear 2026 01 Janeiro.pdf | 2026 |
| Clear 2018 2019 07 Julho.pdf | 2018 |
| Arquivo_sem_ano.pdf | None ❌ |

### Função: `_should_process_file()`
```python
def _should_process_file(filename: str, target_year: Optional[int]) -> bool:
    """Determina se arquivo deve ser processado."""
    # Se target_year=None: processa todos
    # Se target_year=2024: processa apenas se ano==2024
```

## Logging

O filtro gera logs informativos:

```
16/02/2026 13:55:16 - INFO - 🔍 Filtro de ano ativo: 2026
16/02/2026 13:55:16 - INFO - 📥 Total estimado de PDFs para processar: 92
...
16/02/2026 13:55:21 - INFO - ✓ Arquivos processados com sucesso: 1
16/02/2026 13:55:21 - INFO - ⏭️ Arquivos ignorados (fora do filtro de ano): 91
16/02/2026 13:55:21 - INFO - 📈 Total de registros extraídos: 20
```

### Aviso de Arquivo sem Ano
Se um arquivo não possur ano no nome:
```
⚠️ Não foi possível extrair ano de: Arquivo_sem_ano.pdf
```

## Status do Arquivo CSV

Os arquivos CSV exportados incluem um timestamp, independente do filtro:
```
dados_extraidos_20260216_135521.csv
```

O filtro de ano **não afeta** o nome do arquivo de saída.

## Performance

### Tempo de processamento comparativo
| Filtro | PDFs | Tempo Estimado |
|--------|------|----------------|
| Nenhum (todos) | 92 | ~20-25 minutos |
| --year 2024 | 12 | ~2-3 minutos |
| --year 2026 | 1 | ~5 segundos |

## Contribuição e Melhorias Futuras

Ideias para expandir o filtro:
- [ ] Filtro por intervalo de anos: `--year-from 2023 --year-to 2025`
- [ ] Filtro por mês: `--year 2024 --month 03`
- [ ] Múltiplos anos: `--years 2024,2025,2026`
- [ ] Padrão customizável de nome de arquivo

## Perguntas Frequentes

### P: Posso usar sem especificar ano?
**R:** Sim! Se não usar `--year`, todos os PDFs serão processados normalmente.

### P: E se um PDF tem dois anos no nome?
**R:** O filtro pega o **primeiro** ano encontrado. Ex: "Clear 2018 2019 07 Julho.pdf" → 2018

### P: Posso processar múltiplos anos?
**R:** Atualmente não. Execute o comando separadamente ou sem filtro.

### P: Onde é definido o padrão de ano?
**R:** No regex `\b(19|20)\d{2}\b` dentro de `_extract_year_from_filename()`
