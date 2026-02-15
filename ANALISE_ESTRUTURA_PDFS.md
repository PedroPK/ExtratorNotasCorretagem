# 📊 ANÁLISE DE ESTRUTURA DOS PDFs - RESUMO

## Problemas Identificados

### 1. Alguns PDFs estão protegidos com senha ❌
- Primeiro PDF do ZIP: "Clear 2026 01 Janeiro - Notas Negociacao.pdf"
- **Solução**: Capturar `PdfminerException` e pular para o próximo

### 2. Estrutura de Tabelas Identificada ✓

#### TABELA DE NEGICIAÇÕES (11 colunas)
Encontrada como a **TABELA 3, 4, 5** no PDF (múltiplas linhas de negócios)

```
COL[0]  = [VAZIO]
COL[1]  = Tipo Mercado (ex: "1-BOVESPA")
COL[2]  = Operação (ex: "C" para Compra, "V" para Venda)
COL[3]  = Tipo (ex: "FRACIONARIO")
COL[4]  = [VAZIO]
COL[5]  = NOME DO ATIVO (ex: "COPEL ON ED N1", "NEOENERGIA ON NM")
COL[6]  = [VAZIO] ou "#" (código não claro)
COL[7]  = QUANTIDADE (ex: 25, 5, 15)
COL[8]  = PREÇO (ex: "5,50", "26,00")
COL[9]  = VALOR TOTAL (ex: "137,50", "130,00")
COL[10] = "D" (Debitado)
```

#### DATA PREGÃO
Localizada em: **TABELA 2 (tabela cabeçalho)**
- COL[8], Linha 0: "Data pregão"
- COL[8], Linha 1: "04/05/2021" ← **AQUI ESTÁ A DATA!**

#### TICKER
- Não há ticker direto, apenas nome do ativo
- Ex: "COPEL ON ED N1" → Precisa ser mapeado para "COPEL3"
- Ex: "NEOENERGIA ON NM" → Precisa ser mapeado para "NEOEN11"

## Exemplo de Dados Extraídos

```
Negociação 1:
- Data: 04/05/2021
- Ativo: COPEL ON ED N1 → COPEL3 (após mapeamento)
- Operação: C (Compra)
- Quantidade: 25
- Preço: 5,50
- Valor: 137,50

Negociação 2:
- Data: 04/05/2021
- Ativo: M.DIASBRANCO ON NM → ?
- Operação: C (Compra)
- Quantidade: 5
- Preço: 26,00
- Valor: 130,00
```

## Próximos Passos

1. **Ajustar mapeamento de data**: buscar na TABELA 2 (não na tabela de dados)
2. **Criar mapeamento de NOMES para TICKERS**: atualizar `DE_PARA_TICKERS`
3. **Iterar sobre múltiplas tabelas**: TABELA 3+ contêm os negócios
4. **Tratar PDFs protegidos**: capturar e pular com mensagem
