#!/usr/bin/env python3
import pdfplumber

pdf_path = "/tmp/Clear 2018 10 Outubro - Notas Negociação Corretagem.pdf"

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[1]  # 04/10/2018
    
    # Teste 1: Padrão
    print("=" * 100)
    print("TESTE 1: Tabelas com parâmetros padrão")
    print("=" * 100)
    tables_default = page.extract_tables()
    print(f"Total: {len(tables_default)} tabelas")
    
    # Procura por tabelas com BRASKEM
    for idx, table in enumerate(tables_default):
        for row_idx, row in enumerate(table):
            row_str = ' '.join([str(c or '').strip() for c in row])
            if 'BRASKEM' in row_str.upper():
                print(f"\nTabela {idx}, Linha {row_idx}:")
                print(f"  {row}")
    
    # Teste 2: Com edge tolerance ajustado
    print("\n" + "=" * 100)
    print("TESTE 2: Tabelas com edge_min_length=None")
    print("=" * 100)
    try:
        tables_tol = page.extract_tables(table_settings={"edge_min_length": 1})
        print(f"Total: {len(tables_tol)} tabelas")
        
        for idx, table in enumerate(tables_tol):
            for row_idx, row in enumerate(table):
                row_str = ' '.join([str(c or '').strip() for c in row])
                if 'BRASKEM' in row_str.upper():
                    print(f"\nTabela {idx}, Linha {row_idx}:")
                    print(f"  {row}")
    except Exception as e:
        print(f"Erro: {e}")
    
    # Teste 3: Texto completo
    print("\n" + "=" * 100)
    print("TESTE 3: Buscar BRASKEM no texto completo")
    print("=" * 100)
    texto = page.extract_text()
    for i, linha in enumerate(texto.split('\n')):
        if 'BRASKEM' in linha.upper():
            print(f"  Linha {i}: {linha}")
