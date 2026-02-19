#!/usr/bin/env python3
"""Extract and show 04/10/2018 operations"""

import openpyxl
from datetime import datetime
import os

# Find latest output file
output_dir = 'resouces/output'
latest_file = max(
    [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.xlsx')],
    key=os.path.getctime
)

# Load workbook
wb = openpyxl.load_workbook(latest_file)
ws = wb['Dados']

print(f"Arquivo: {os.path.basename(latest_file)}\n")
print("Registros de 04/10/2018:")
print("=" * 60)

target_date = datetime(2018, 10, 4).date()
count = 0

for row in ws.iter_rows(min_row=2, values_only=True):
    data_str = row[0]
    ticker = row[1]
    operacao = row[2]
    quantidade = row[3]
    preco = row[4]
    
    if data_str:
        if isinstance(data_str, str):
            data_obj = datetime.strptime(data_str, "%d/%m/%Y").date()
        else:
            data_obj = data_str.date()
        
        if data_obj == target_date:
            count += 1
            print(f"{count}. {data_str:12} {ticker:10} {operacao:3} {int(quantidade):5} {float(preco):8.2f}")

print("=" * 60)
print(f"Total de operacoes em 04/10/2018: {count}")
