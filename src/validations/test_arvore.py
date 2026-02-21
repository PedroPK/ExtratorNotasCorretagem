import pandas as pd
import glob

files = glob.glob('/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/resouces/output/dados_extraidos_*.xlsx')
latest = sorted(files)[-1]
df = pd.read_excel(latest, sheet_name='Árvore')

print('ESTRUTURA DE ARVORE (primeiras 25 linhas):')
print('Ano  Mes Dia Data       Ticker  Op  Qtd   Preco')
print('-' * 65)

for idx in range(min(25, len(df))):
    row = df.iloc[idx]
    
    ano_val = row['Ano']
    ano_str = str(int(ano_val)) if pd.notna(ano_val) and ano_val != '' else '   '
    
    mes_val = row['Mes']
    mes_str = str(int(mes_val)).zfill(2) if pd.notna(mes_val) and mes_val != '' else '  '
    
    dia_val = row['Dia']
    dia_str = str(int(dia_val)).zfill(2) if pd.notna(dia_val) and dia_val != '' else '  '
    
    data = str(row['Data'])
    ticker = str(row['Ticker'])
    op = str(row['Operação'])
    qty = int(row['Quantidade'])
    preco = "{:.2f}".format(row['Preço'])
    
    linha = "{    linha = "{    linha = "{    linha 4} {    linha = "{    tr    linha  dia_str, data, ticker, op, qty, preco)
    print(linha)
