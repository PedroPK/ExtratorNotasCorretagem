#!/usr/bin/env python3
"""
Coleta descrições de ativos a partir das Notas de Corretagem (PDFs).

Este módulo é pensado para ser reutilizado:
- Pode ser chamado diretamente para gerar uma lista de descrições
- Pode ser importado por `gerar_ticker_mapping.py` para gerar mapeamentos
"""

import re
import os
import zipfile
from typing import List, Set, Optional
from pathlib import Path
from config import get_config


def normalize_description(desc: str) -> str:
    """Normaliza uma descrição bruta extraída de PDF.

    Objetivos:
    - Remover prefixos numéricos e tokens de mercado/operação
    - Remover "C FRACIONARIO", "C VISTA", "V FRACIONARIO", "V VISTA", "RV LISTADO"
    - Remover sufixos com anotações e colunas numéricas
    - Colapsar espaços e limpar pontuação redundante
    - Preservar sufixos de série como ON/PN/PNA/PNB/DR e opcionalmente NM
    """
    if not desc:
        return desc

    s = desc.strip()

    # Normaliza espaços
    s = re.sub(r"\s+", " ", s)

    # Remove prefixos numéricos tipo '1-' ou '01 -'
    s = re.sub(r"^\s*\d+[\-\s]*", "", s)

    # Remove prefixos de operação e tipo que não são parte do ativo
    # Padrões mais robustos para capturar variações:
    # - "NB3 RV LISTADO C FRACIONARIO" etc
    # - "RV LISTADO V VISTA", "RV LISTADO V FRACIONARIO"
    # - "RV LISTADO C FRACIONARIO"
    # - "C FRACIONARIO", "C VISTA"
    # - "V FRACIONARIO", "V VISTA"
    # - "RV LISTADO"
    operation_patterns = [
        r"^NB3\s+RV\s+LISTADO\s+C\s+FRACIONARIO\s+",  # NB3 RV LISTADO C FRACIONARIO
        r"^RV\s+LISTADO\s+V\s+VISTA\s+",               # RV LISTADO V VISTA
        r"^RV\s+LISTADO\s+V\s+FRACIONARIO\s+",         # RV LISTADO V FRACIONARIO
        r"^RV\s+LISTADO\s+C\s+FRACIONARIO\s+",         # RV LISTADO C FRACIONARIO
        r"^C\s+FRACIONARIO\s+",                         # C FRACIONARIO (remove também o espaço)
        r"^C\s+VISTA\s+",                               # C VISTA (remove também o espaço)
        r"^V\s+FRACIONARIO\s+",                         # V FRACIONARIO (remove também o espaço)
        r"^V\s+VISTA\s+",                               # V VISTA (remove também o espaço)
        r"^RV\s+LISTADO\s+",                            # RV LISTADO (remove também o espaço)
    ]
    for pattern in operation_patterns:
        s = re.sub(pattern, "", s, flags=re.IGNORECASE)

    # Remove outros tokens de mercado comuns
    prefix_tokens = [
        r"BOVESPA",
        r"B3",
        r"FRACIONARIO",
        r"FRACIONÁRIO",
        r"VISTA",
        r"C/V",
        r"NEGOCIAÇÃO",
        r"NEGOCIACAO",
        r"COTACAO",
    ]
    prefix_re = re.compile(r"^(?:" + r"|".join(prefix_tokens) + r")\b[\s\-]*", re.IGNORECASE)
    # Aplicar repetidamente para remover sequências
    prev = None
    while prev != s:
        prev = s
        s = prefix_re.sub("", s)

    # Remove sufixos com símbolos estranhos (ex: @#) e colunas numéricas ao final
    s = re.sub(r"[\@\#\*\|]+", "", s)
    # Remove trailing sequences: ' 1 48,82 48,82 D'
    s = re.sub(r"\s+\d+[\d\s,\.\-\/]*[A-Za-z]?$", "", s)

    # Remove leading/trailing punctuation and extra spaces
    s = s.strip(r" \t\n\r\x0b\f\-\.,;:()")
    s = re.sub(r"\s+", " ", s)

    return s


def _extract_description_from_row(cells: List[str]) -> Optional[str]:
    """Tenta extrair a descrição do ativo a partir de uma linha (lista de células).

    Heurísticas:
    - Se a tabela for do tipo negociação, a especificação costuma estar na coluna 5
    - Caso contrário, busca por padrões como 'NOME ON', 'NOME PN', 'NOME ON NM'
    """
    if not cells:
        return None

    # Tenta coluna 5 (índice 5)
    if len(cells) > 5 and cells[5] and re.search(r'[A-Za-zÀ-ÿ]', cells[5]):
        desc = cells[5].strip()
        return normalize_description(desc)

    # Busca por padrões em todas as células
    row_text = ' '.join([str(c or '') for c in cells])
    # Padrão: palavra(s) + (ON|PN|PNA|PNB|DR) opcionalmente seguido de NM, N1, N2, etc
    match = re.search(r"([A-Za-zÀ-ÿ0-9\.\-\s]{2,60}?)\s+(ON|PN|PNA|PNB|DR)(?:\s+(NM|N1|N2|N3))?", row_text, re.IGNORECASE)
    if match:
        empresa = match.group(1).strip()
        tipo = match.group(2).upper()
        sufixo = match.group(3).upper() if match.group(3) else None
        # Reconstrói com todos os componentes
        if sufixo:
            desc_result = f"{empresa} {tipo} {sufixo}"
        else:
            desc_result = f"{empresa} {tipo}"
        return normalize_description(desc_result)

    # Fallback: procura por palavras com mais de 3 letras juntas (possível nome do ativo)
    match2 = re.search(r"([A-Za-zÀ-ÿ]{3,}(?:\s+[A-Za-zÀ-ÿ]{2,}){0,3})", row_text)
    if match2:
        candidate = match2.group(1).strip()
        # filtra palavras muito genéricas
        if len(candidate) > 3:
            return normalize_description(candidate)

    return None


def collect_descriptions_from_path(input_path: Optional[str] = None, year: Optional[int] = None) -> List[str]:
    """Percorre `input_path` (pasta ou arquivo ZIP) e devolve descrições únicas encontradas.

    Se `input_path` for None, usa a configuração em `application.properties`.
    """
    cfg = get_config()

    if input_path is None:
        input_folder = cfg.get_input_folder()
    else:
        input_folder = input_path

    resolved = cfg.resolve_path(input_folder)
    if not os.path.exists(resolved):
        raise FileNotFoundError(f"Caminho não encontrado: {resolved}")

    descriptions: Set[str] = set()
    failed_files: Set[str] = set()

    # prepara arquivo de log para erros do gerador de tickers
    try:
        logs_folder = cfg.resolve_path(cfg.get_logs_folder())
        os.makedirs(logs_folder, exist_ok=True)
        error_log_path = os.path.join(logs_folder, 'tickergen_errors.log')
    except Exception:
        error_log_path = os.path.join(os.path.dirname(resolved), 'tickergen_errors.log')

    def _process_pdf_bytes(content_bytes, name="pdf"):
        try:
            # Importa pdfplumber apenas quando necessário (evita erro de importação em ambientes sem dependência)
            try:
                import pdfplumber
                from pdfplumber.utils import PdfminerException
            except Exception:
                return

            # Se recebemos bytes, converte para BytesIO; se for path, usa diretamente
            from io import BytesIO
            target = content_bytes
            if isinstance(content_bytes, (bytes, bytearray)):
                target = BytesIO(content_bytes)

            # Tenta abrir; se houver PDF protegido, tenta com senha da config
            try:
                pdf = pdfplumber.open(target)
            except PdfminerException:
                # Tenta com senha da configuração
                try:
                    senha = get_config().get_pdf_password()
                except Exception:
                    senha = None
                if senha:
                    try:
                        # precisa recriar BytesIO se já foi consumido
                        if isinstance(target, BytesIO):
                            target.seek(0)
                        pdf = pdfplumber.open(target, password=senha)
                    except Exception:
                        return
                else:
                    return

            with pdf:
                for page in pdf.pages:
                    try:
                        tables = page.extract_tables()
                        for table in tables:
                            if not table:
                                continue
                            for row in table:
                                if not row or all(not (str(c).strip()) for c in row):
                                    continue
                                cells = [(c or '').strip() for c in row]
                                desc = _extract_description_from_row(cells)
                                if desc:
                                    descriptions.add(desc)
                    except Exception:
                        continue
                    # Além da extração por tabelas, sempre tenta buscar padrões no texto da página
                    try:
                        texto = page.extract_text() or ''
                        for m in re.finditer(r"([A-Za-zÀ-ÿ0-9\.\- ]{2,60}?)\s+(ON|PN|PNA|PNB|DR)\b(?:\s+NM|\s+N1|\s+N2)?", texto, re.IGNORECASE):
                            descriptions.add(normalize_description(m.group(0).strip()))
                    except Exception:
                        continue
        except Exception:
            return

    # Processa arquivos na pasta
    if os.path.isdir(resolved):
        # PDFs diretos
        for f in os.listdir(resolved):
            pathf = os.path.join(resolved, f)
            if f.endswith('.pdf'):
                # Filtra por ano se necessário
                if year is not None:
                    m = re.search(r'\b(19|20)\d{2}\b', f)
                    if not m or int(m.group(0)) != year:
                        continue
                try:
                    _process_pdf_bytes(pathf, f)
                except Exception as e:
                    failed_files.add(f)
                    try:
                        with open(error_log_path, 'a', encoding='utf-8') as lf:
                            lf.write(f"{f}: {repr(e)}\n")
                    except Exception:
                        pass
                    continue

        # PDFs dentro de ZIPs
        for zf in [x for x in os.listdir(resolved) if x.endswith('.zip')]:
            try:
                with zipfile.ZipFile(os.path.join(resolved, zf), 'r') as z:
                    for entry in z.namelist():
                        if not entry.endswith('.pdf'):
                            continue
                        if year is not None:
                            m = re.search(r'\b(19|20)\d{2}\b', entry)
                            if not m or int(m.group(0)) != year:
                                continue
                        try:
                            with z.open(entry) as ef:
                                _process_pdf_bytes(ef.read(), entry)
                        except Exception as e:
                            failed_files.add(entry)
                            try:
                                with open(error_log_path, 'a', encoding='utf-8') as lf:
                                    lf.write(f"{entry} (in {zf}): {repr(e)}\n")
                            except Exception:
                                pass
                            continue
            except Exception:
                continue

    elif os.path.isfile(resolved) and resolved.endswith('.zip'):
        with zipfile.ZipFile(resolved, 'r') as z:
            for entry in z.namelist():
                if not entry.endswith('.pdf'):
                    continue
                if year is not None:
                    m = re.search(r'\b(19|20)\d{2}\b', entry)
                    if not m or int(m.group(0)) != year:
                        continue
                try:
                    with z.open(entry) as ef:
                        _process_pdf_bytes(ef.read(), entry)
                except Exception as e:
                    failed_files.add(entry)
                    try:
                        with open(error_log_path, 'a', encoding='utf-8') as lf:
                            lf.write(f"{entry} (in {os.path.basename(resolved)}): {repr(e)}\n")
                    except Exception:
                        pass
                    continue

    else:
        raise ValueError(f"Caminho não suportado: {resolved}")

    return sorted(descriptions)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Coleta descrições de ativos a partir de Notas (PDFs)')
    parser.add_argument('--year', '-y', type=int, default=None, help='Ano para filtrar arquivos')
    parser.add_argument('--output', '-o', type=str, default=None, help='Arquivo de saída para salvar descrições (opcional)')
    args = parser.parse_args()

    descs = collect_descriptions_from_path(year=args.year)
    print(f"✓ Encontradas {len(descs)} descrições únicas")
    if args.output:
        outpath = args.output
    else:
        cfg = get_config()
        outfolder = cfg.resolve_path('resouces')
        os.makedirs(outfolder, exist_ok=True)
        outpath = os.path.join(outfolder, f"ticker_candidates_{args.year or 'all'}.txt")

    with open(outpath, 'w', encoding='utf-8') as f:
        for d in descs:
            f.write(d + '\n')

    print(f"✓ Salvo: {outpath}")


if __name__ == '__main__':
    main()
