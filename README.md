# 📊 Extrator Notas Corretagem

Um script Python para extrair dados de notas de negociação de PDFs de educação da Bolsa de Valores Brasileira.

## 🎯 Funcionalidades

- **Extração automática** de notas de negociação de PDFs
- **Suporte a múltiplos formatos** (pasta de PDFs, arquivos ZIP, PDFs individuais)
- **Tratamento de PDFs protegidos** com senha
- **Progresso visual** com barra de progresso
- **Mapeamento de ativos** para tickers B3
- **Log detalhado** de operações
- **Exportação em múltiplos formatos** (CSV, Excel, JSON)

## 📋 Requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)

## 🚀 Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/ExtratorNotasCorretagem.git
cd ExtratorNotasCorretagem
```

### 2. Crie um ambiente virtual

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

## ⚙️ Configuração

### application.properties

O arquivo `application.properties` contém as configurações da aplicação:

```properties
# Senha para PDFs protegidos (deixe vazio se não houver)
pdf.password=sua_senha_aqui

# Nível de log (DEBUG, INFO, WARNING, ERROR)
logging.level=INFO

# Formato de saída (csv, excel, json)
output.format=csv

# Pasta de entrada com os PDFs
input.folder=../resouces/inputNotasCorretagem

# Pasta de saída dos dados extraídos
output.folder=../output
```

## 📂 Estrutura do Projeto

```
ExtratorNotasCorretagem/
├── src/
│   └── extratorNotasCorretagem.py      # Script principal
├── resouces/
│   └── inputNotasCorretagem/           # Pasta com PDFs/ZIPs de entrada
├── output/                              # Pasta de saída (criada automaticamente)
├── application.properties               # Arquivo de configuração
├── requirements.txt                     # Dependências Python
├── .gitignore                          # Arquivos ignorados pelo Git
└── README.md                           # Este arquivo
```

## 💻 Como Usar

### 1. Adicione seus PDFs

Coloque seus arquivos PDF ou ZIP na pasta `resouces/inputNotasCorretagem/`

```bash
# Exemplo: Adicione um ZIP com notas de negociação
cp notas_corretagem.zip resouces/inputNotasCorretagem/
```

### 2. Execute o script

```bash
cd src
python extratorNotasCorretagem.py
```

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

## 🔒 PDFs Protegidos

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
