import pdfplumber
import pandas as pd
import re
import difflib
import os
import zipfile
import logging
import signal
import sys
import argparse
from collections import Counter
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional
from config import get_config

# Carregar configurações
config = get_config()

# Configuração de Logging
logging_level = config.get_logging_level()
logs_folder = config.resolve_path(config.get_logs_folder())

# Criar pasta de logs se não existir
if not os.path.exists(logs_folder):
    os.makedirs(logs_folder)

# Gera nome do arquivo de log com timestamp
log_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(logs_folder, f"extracao_{log_timestamp}.log")

# Configurar logging com ambos console e arquivo
logging.basicConfig(
    level=getattr(logging, logging_level),
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
    handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Flag para controle de interrupção pelo usuário (Ctrl+C)
stop_processing = False


def _handle_sigint(signum, frame):
    global stop_processing
    if not stop_processing:
        stop_processing = True
        logger.warning(
            "⏸️ Interrupção solicitada pelo usuário (Ctrl+C). Finalizando após o arquivo atual..."
        )
    else:
        logger.error("✖ Forçando saída imediata por novo Ctrl+C")
        sys.exit(1)


# Registra o handler para SIGINT
signal.signal(signal.SIGINT, _handle_sigint)


def _count_total_pdfs(caminho):
    """Conta o total estimado de PDFs que serão processados a partir do caminho.
    Suporta arquivo ZIP único, pasta com PDFs e/ou ZIPs, e caminho para pasta com PDFs diretos.
    """
    try:
        if caminho.endswith(".zip") or (os.path.isfile(caminho) and zipfile.is_zipfile(caminho)):
            with zipfile.ZipFile(caminho, "r") as z:
                return len([f for f in z.namelist() if f.endswith(".pdf")])

        if os.path.isdir(caminho):
            total = 0
            # PDFs diretos
            total += len([f for f in os.listdir(caminho) if f.endswith(".pdf")])
            # PDFs dentro de ZIPs na pasta
            zips = [f for f in os.listdir(caminho) if f.endswith(".zip")]
            for zf in zips:
                try:
                    with zipfile.ZipFile(os.path.join(caminho, zf), "r") as z:
                        total += len([f for f in z.namelist() if f.endswith(".pdf")])
                except Exception:
                    continue
            return total

        return 0
    except Exception:
        return 0


# 1. Dicionário De-Para para mapear nomes de ativos para Tickers
# Baseado nos exemplos dos fontes como "FIAGRO SUNO" [6] e "SUNO FIC FI" [7]
DE_PARA_TICKERS = {
    "PORTOSEGURO": "PSSA3",
    "PETROBRAS": "PETR3",
    "COPEL ON ED N1": "CPLE3",
    "NEOENERGIA ON NM": "NEOE3",
    "VALE ON": "VALE3",
    # "FIAGRO SUNO": "SNAG11",
    # "SUNO FIC FI": "SNCI11",
    # "FII ATRIO": "ARRI11",
    # "FII KINEA RI": "KNCR11",
    # "FII HSI CRI": "HSAF11"
}


def criar_bytesio_com_nome(conteudo, nome_arquivo):
    """Cria um BytesIO com atributo 'name' para compatibilidade."""
    bio = BytesIO(conteudo)
    bio.name = nome_arquivo
    return bio


def limpar_ticker(texto, dicionario):
    """Extrai o ticker ou usa o de-para para nomes conhecidos."""
    texto = texto.replace("\n", " ").strip()
    # Tenta encontrar um padrão de Ticker (4 letras + 2 números)
    match = re.search(r"[A-Z]{4}\d{2}", texto)
    if match:
        return match.group(0)

    # Se não achar o Ticker puro, busca no dicionário De-Para
    for nome, ticker in dicionario.items():
        if nome in texto.upper():
            return ticker
    return texto  # Retorna o original se não mapear


def _normalize_number(text):
    """Converte números no formato brasileiro para ponto decimal (ex: '1.234,56' -> '1234.56')."""
    if not text:
        return ""
    s = str(text).strip()
    # Remove espaços e símbolos extras
    s = s.replace("\xa0", "").replace(" ", "")
    # Se já tem apenas dígitos e ponto, tenta retornar
    # Substitui milhares (.) e decimal (,) -> '.'
    # Primeiro, remove pontos que representam milhares
    # Mas cuidado: se houver apenas one dot and no comma, keep it
    if "," in s:
        s = s.replace(".", "")
        s = s.replace(",", ".")
    else:
        # Remove any non-digit or dot
        s = re.sub(r"[^0-9\.]", "", s)
    return s


def _extract_operations_from_text(text, data_pregao, ticker_mapping):
    """Extrai operações de negociação diretamente do texto (fallback para tabelas faltantes).

    Padrão típico em notas de corretagem:
    1-BOVESPA C FRACIONARIO NOME DO ATIVO ON NM 1 40,00 40,00 D
    ou com prazo:
    1-BOVESPA C FRACIONARIO 01/00 NOME DO ATIVO ON NM 1 40,00 40,00 D

    Busca por: '1-BOVESPA' seguido de dados e retorna lista de operações encontradas.
    """
    operacoes = []

    if not text or "1-BOVESPA" not in text:
        return operacoes

    # Padrão: 1-BOVESPA seguido de operação C/V, tipo, NOME ATIVO (asset pode ter extra como DM 0,10), [opcional #], qtd, preço, preço, D/C
    # CORRIGIDO: Prazo DD/DD é OPCIONAL agora - algumas notas não têm prazo
    # CORRIGIDO: ([A-Z0-9\s]+?) para capturar nomes com números (ex: ELETROBLAS, RAIADROGASIL ON NM)
    # CORRIGIDO: (.+?) para capturar asset name com extra info (ex: FORJA TAURUS DM 0,10), com #? para lidar com # nos dados
    pattern = r"1-BOVESPA\s+([CV])\s+(\w+)\s+(.+?)\s+#?\s*(\d+)\s+([\d.,]+)\s+([\d.,]+)\s+([DC])"

    for match in re.finditer(pattern, text, re.IGNORECASE):
        try:
            operacao = match.group(1).upper()
            ativo_nome = match.group(3).strip()

            # Os números são: quantidade, preço/ajuste, valor da operação
            qty_str = match.group(4)
            price_str = match.group(5)

            # Extrai ticker do nome do ativo
            ticker = _extract_ticker_from_cells([ativo_nome], ticker_mapping)
            if not ticker:
                continue

            quantidade = _normalize_number(qty_str)
            preco = _normalize_number(price_str)

            if not quantidade or not preco:
                continue

            operacoes.append(
                {
                    "Data": data_pregao,
                    "Ticker": ticker,
                    "Operação": operacao,
                    "Quantidade": quantidade,
                    "Preço": preco,
                }
            )
        except Exception:
            continue

    return operacoes


def _is_likely_header(cells):
    """Verifica se a linha parece ser um cabeçalho (nomes de colunas)."""
    if not cells:
        return False

    # Palavras típicas de cabeçalhos
    header_keywords = [
        "data",
        "ativo",
        "especif",
        "qtd",
        "preço",
        "valor",
        "operação",
        "nota",
        "corretora",
    ]
    header_text = " ".join([str(c).lower() for c in cells if c])

    # Se muitas células têm pontos/dois-pontos, pode ser cabeçalho
    if header_text.count(":") > 3:
        return True

    # Se contém múltiplas palavras de cabeçalho
    count = sum(1 for kw in header_keywords if kw in header_text)
    return count >= 2


def _is_valid_data_row(cells, is_negotiation_table=False):
    """Verifica se a linha parece ser um registro de negociação e não cabeçalho/resumo/footer.

    Args:
        cells: List of cell values from the row
        is_negotiation_table: True if this is an 11-column negotiation table (less strict validation)
    """
    if not cells or len(cells) < 2:
        return False

    # Rejeita se parece ser cabeçalho
    if _is_likely_header(cells):
        return False

    # Palavras-chave que indicam linhas que NÃO são negociações (headers, footers, summaries)
    skip_keywords = [
        "resumo",
        "total",
        "debêntures",
        "vendas",
        "compras",
        "opções",
        "termo",
        "taxa",
        "emolumentos",
        "transf",
        "ativos",
        "custodiante",
        "clearing",
        "especificações",
        "bovespa",
        "cblc",
        "cliente",
        "código",
        "assessor",
        "participante",
        "folha",
        "data pregão",
        "negociação",
        "c.p.f",
        "cnpj",
        "valor das oper",
        "valor líquido",
        "qualificado",
        "nota de negociação",
        "impostos",
        "i.r.r.f",
        "execução",
        "custódia",
        "bolsa",
        "operacional",
        "custos",
        "agente",
        "qualificado",
        "especificações diversas",
        "coluna q",
        "liquidação",
        "agente do qualificado",
        "(*)",
        "observações",
        "líquido para",  # Settlement rows, not transactions
        "conta",
        "saldo",
        "c.m.c",
        "participante destino",  # Account/routing info
    ]

    # Para tabelas de negociação (11 colunas), validação menos rigorosa
    if is_negotiation_table:
        # Apenas rejeita se tem palavras-chave muito óbvias (menos a de "bovespa")
        strict_skip = [
            "resumo",
            "total",
            "debêntures",
            "taxa",
            "emolumentos",
            "custos",
            "líquido para",
            "client",
            "código",
            "c.p.f",
            "cnpj",
            "observações",
            "(*)",
            "saldo",
            "conta",
        ]
        row_text = " ".join(cells).upper()
        for keyword in strict_skip:
            if keyword.upper() in row_text:
                return False
    else:
        # Para outras tabelas, validação rigorosa
        row_text = " ".join(cells).upper()
        for keyword in skip_keywords:
            if keyword.upper() in row_text:
                return False

    # Uma linha válida deve ter pelo menos um número (quantidade ou preço)
    has_number = False
    for cell in cells:
        # Aceita tanto números decimais quanto inteiros
        if re.search(r"\d", str(cell)):
            has_number = True
            break

    return has_number


def _normalize_text_for_comparison(text: str) -> str:
    """Normaliza texto para comparação fuzzy de nomes de ativos.

    Remove espaços extras, converte para maiúsculas, remove caracteres especiais.
    Exemplo: "SUZANO PAPEL ON NM" -> "SUZANO PAPEL ON NM" (sem mudança, mas padronizado)
    Exemplo: "SUZANOPAPEL ONNM" -> "SUZANO PAPEL ON NM" (após tokenização)
    """
    # Converte para maiúsculas
    text = text.upper().strip()

    # Remove múltiplos espaços
    text = re.sub(r"\s+", " ", text)

    # Remove hífen (algumas variações podem usar hífen)
    text = text.replace("-", " ")

    # Remove caracteres especiais mantendo apenas letras, números e espaço
    text = re.sub(r"[^A-Z0-9\s]", "", text)

    # Remove espaços novamente se criados pela remoção de caracteres
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _extract_words_from_asset_name(text: str) -> set:
    """Extrai palavras significativas de um nome de ativo.

    Remove stopwords comuns e retorna um conjunto de palavras principais.
    Exemplo: "SUZANO PAPEL ON NM" -> {"SUZANO", "PAPEL", "ON", "NM"}
    """
    # Palavras comuns em tickers B3 que geralmente não ajudam na identificação
    stopwords = {"ON", "PN", "NM", "N1", "N2", "ED", "EDUC", "PREFER", "ORDINARIA"}

    text = _normalize_text_for_comparison(text)
    words = set(text.split())

    # Remove stopwords, mas mantém pelo menos algo
    significant_words = words - stopwords
    if significant_words:
        return significant_words
    return words


def _fuzzy_match_asset_name(cell_text: str, mapping_name: str) -> bool:
    """Faz correspondência fuzzy entre nome de ativo da célula e nome no mapeamento.

    Usa intersecção de palavras principais. Se pelo menos 70% das palavras
    principais do mapeamento estão presentes na célula, considera um match.

    Exemplos:
    - "SUZANO PAPEL ON NM" vs "SUZANO ON NM" -> True (78% match)
    - "SUZANO PAPEL ON NM" vs "SUZANOPAPEL ONNM" -> True (wordset match)
    - "SUZANO PAPEL ON NM" vs "PETROBRAS ON" -> False (0% overlap)
    """
    cell_words = _extract_words_from_asset_name(cell_text)
    mapping_words = _extract_words_from_asset_name(mapping_name)

    if not mapping_words:
        return False

    # Calcula intersecção de palavras
    common_words = cell_words.intersection(mapping_words)
    match_percentage = len(common_words) / len(mapping_words)

    # Aceita match se pelo menos 70% das palavras mapeadas estão presentes
    # OU se há pelo menos 2 palavras em comum (para evitar falsos positivos)
    return match_percentage >= 0.70 or len(common_words) >= 2


def _fuzzy_match_score(cell_text: str, mapping_name: str) -> float:
    """Calcula score de correspondência fuzzy (0.0 a 1.0).

    Retorna o percentual de palavras do mapeamento presentes na célula,
    com bônus para mapeamentos mais específicos (com mais palavras).

    Exemplos:
    - "PETROBRAS PN EJ N2" vs "PETROBRAS PN EJ N2" → 1.0 (perfeito, 4 palavras)
    - "PETROBRAS PN EJ N2" vs "PETROBRAS PN" → 0.8 (2/2 palavras do mapping, mas mapping é genérico)
    - "PETROBRAS PN EJ N2" vs "PETROBRAS ON" → 0.5 (1 palavra em comum, mapping genérico)
    """
    cell_words = _extract_words_from_asset_name(cell_text)
    mapping_words = _extract_words_from_asset_name(mapping_name)

    if not mapping_words:
        return 0.0

    common_words = cell_words.intersection(mapping_words)

    # Score base: percentual de palavras do mapping presentes no cell
    base_score = len(common_words) / len(mapping_words)

    # Bônus de especificidade: mapeamentos com mais palavras recebem bônus
    # Isso garante que "PETROBRAS PN EJ N2" (4 palavras) bata "PETROBRAS PN" (2 palavras)
    # quando ambos têm base_score = 1.0
    specificity_bonus = len(mapping_words) / (len(cell_words) + len(mapping_words))

    # Combina: 90% do base_score + 10% do bônus de especificidade
    return 0.9 * base_score + 0.1 * specificity_bonus


def _string_similarity(a: str, b: str) -> float:
    """Retorna similaridade entre duas strings (0..1) usando SequenceMatcher."""
    if not a or not b:
        return 0.0
    a_norm = _normalize_text_for_comparison(a)
    b_norm = _normalize_text_for_comparison(b)
    # Use ratio direto
    return difflib.SequenceMatcher(None, a_norm, b_norm).ratio()


def _extract_ticker_from_cells(cells, ticker_mapping=None):
    """
    Extrai ticker da linha, buscando padrão B3 ou nome de ativo conhecido.

    Estratégia (prioriza arquivo configurável sobre hardcoded):
    1. Procura por padrão ticker B3 (4 letras + 2 dígitos)
    2. Busca em ticker_mapping com correspondência exata
    3. Busca em ticker_mapping com correspondência fuzzy (ordenada por score, prioriza descrições mais específicas)
    4. Busca em DE_PARA_TICKERS (hardcoded) com correspondência exata
    5. Busca em DE_PARA_TICKERS (hardcoded) com correspondência fuzzy (ordenada por score)
    """
    for cell in cells:
        cell_str = str(cell).strip()
        if not cell_str:
            continue

        # Passo 1: Tenta padrão ticker B3 (4 letras + 2 dígitos)
        match = re.search(r"[A-Z]{4}\d{2}", cell_str)
        if match:
            return match.group(0)

        cell_str_normalized = _normalize_text_for_comparison(cell_str)

        # Passo 2: Tenta correspondência exata em ticker_mapping (configurável - PRIORIDADE)
        if ticker_mapping:
            for nome, ticker in ticker_mapping.items():
                if _normalize_text_for_comparison(nome) == cell_str_normalized:
                    return ticker

        # Passo 3: Tenta correspondência fuzzy em ticker_mapping (prioriza descrições mais específicas)
        if ticker_mapping:
            best_match = None
            best_score = 0.0
            for nome, ticker in ticker_mapping.items():
                if _fuzzy_match_asset_name(cell_str, nome):
                    score = _fuzzy_match_score(cell_str, nome)
                    # Prioriza matches com score mais alto (mais em comum)
                    # Em caso de empate, a ordem do dicionário decide
                    if score > best_score:
                        best_score = score
                        best_match = ticker
            if best_match:
                return best_match

        # Passo 4: Tenta correspondência exata em DE_PARA (hardcoded - fallback)
        for nome, ticker in DE_PARA_TICKERS.items():
            if _normalize_text_for_comparison(nome) == cell_str_normalized:
                return ticker

        # Passo 5: Tenta correspondência fuzzy em DE_PARA (fallback ordenada por score)
        best_match = None
        best_score = 0.0
        for nome, ticker in DE_PARA_TICKERS.items():
            if _fuzzy_match_asset_name(cell_str, nome):
                score = _fuzzy_match_score(cell_str, nome)
                if score > best_score:
                    best_score = score
                    best_match = ticker
        if best_match:
            return best_match

        # Passo 6: Última tentativa - correspondência por similaridade de string
        # (cobre erros de digitação como 'BRASKEN' vs 'BRASKEM')
        try:
            for nome, ticker in ticker_mapping.items():
                sim = _string_similarity(cell_str, nome)
                if sim >= 0.85:
                    return ticker
            for nome, ticker in DE_PARA_TICKERS.items():
                sim = _string_similarity(cell_str, nome)
                if sim >= 0.85:
                    return ticker
        except Exception:
            pass
    # Se não encontrou padrão, retorna None (linha provavelmente não é válida)
    return None


def _extract_year_from_filename(filename: str) -> Optional[int]:
    """Extrai o ano do nome do arquivo PDF.

    Procura por padrões como:
    - Clear 2026 01 Janeiro
    - Clear 2025 12 Dezembro
    - Arquivo_2024_01_Janeiro

    Args:
        filename: Nome do arquivo PDF

    Returns:
        Ano extraído como inteiro, ou None se não encontrar
    """
    # Padrão: 4 dígitos que representam um ano (entre 1900 e 2100)
    match = re.search(r"\b(19|20)\d{2}\b", filename)
    if match:
        return int(match.group(0))
    return None


def _should_process_file(filename: str, target_year: Optional[int]) -> bool:
    """Verifica se o arquivo deve ser processado baseado no filtro de ano.

    Args:
        filename: Nome do arquivo
        target_year: Ano desejado (None = processar todos)

    Returns:
        True se deve processar, False caso contrário
    """
    if target_year is None:
        return True

    file_year = _extract_year_from_filename(filename)
    if file_year is None:
        logger.warning(f"⚠️  Não foi possível extrair ano de: {filename}")
        return False

    return file_year == target_year


def _normalize_ticker_value(ticker_value: str) -> str:
    """Normaliza ticker para comparação case-insensitive e sem espaços."""
    return re.sub(r"\s+", "", str(ticker_value).upper().strip())


def _filter_dataframe_by_ticker(df: pd.DataFrame, target_ticker: Optional[str]) -> pd.DataFrame:
    """Filtra DataFrame para um único ticker quando solicitado."""
    if df.empty or not target_ticker:
        return df

    if "Ticker" not in df.columns:
        logger.warning("⚠️  Coluna 'Ticker' não encontrada. Filtro de ticker não aplicado.")
        return df

    target = _normalize_ticker_value(target_ticker)
    filtered = df[df["Ticker"].astype(str).apply(_normalize_ticker_value) == target].copy()

    logger.info(
        f"🔎 Filtro de ticker aplicado: {target} | Registros antes: {len(df)} | depois: {len(filtered)}"
    )
    return filtered


def processar_pdf(pdf_file, senha=None):
    dados_extraidos = []

    # Carrega mapeamento de tickers do arquivo de configuração
    ticker_mapping = config.get_ticker_mapping()

    # Tratamento inteligente do nome do arquivo para diferentes tipos de entrada
    if isinstance(pdf_file, str):
        arquivo_nome = os.path.basename(pdf_file)
    else:
        # Para file objects e BytesIO, tenta obter 'name', senão usa genérico
        arquivo_nome = getattr(pdf_file, "name", "pdf_temporario.pdf")

    try:
        logger.info(f"📄 Processando arquivo: {arquivo_nome}")
        sys.stderr.flush()

        # Tenta abrir com senha se fornecida
        try:
            if senha:
                pdf = pdfplumber.open(pdf_file, password=senha)
            else:
                pdf = pdfplumber.open(pdf_file)
        except pdfplumber.utils.exceptions.PdfminerException:
            # Se falhar sem senha, tenta com a senha padrão da config
            try:
                senha_config = config.get_pdf_password()
                if senha_config:
                    pdf = pdfplumber.open(pdf_file, password=senha_config)
                else:
                    raise
            except:
                logger.warning(
                    f"⚠️  {arquivo_nome}: PDF protegido. Configure 'pdf.password' em application.properties"
                )
                sys.stderr.flush()
                return dados_extraidos

        with pdf:
            total_paginas = len(pdf.pages)
            logger.debug(f"   Total de páginas: {total_paginas}")

            for num_pagina, page in enumerate(pdf.pages, 1):
                try:
                    # Extração da Data (procura por "Data pregão") [3, 8, 9]
                    texto_topo = page.extract_text()
                    data_pregao = None
                    match_data = re.search(r"(\d{2}/\d{2}/\d{4})", texto_topo)
                    if match_data:
                        data_pregao = match_data.group(1)

                    # Extração da Tabela de Negócios [1, 2, 10]
                    tables = page.extract_tables()
                    registros_pagina = 0

                    for table in tables:
                        if not table:
                            continue

                        # Detecta tabelas de negociações — geralmente 11 colunas em muitas corretoras
                        num_cols = len(table[0]) if table and table[0] else 0
                        table_text = " ".join(" ".join([str(c) for c in row if c]) for row in table)
                        is_negociacao = (num_cols == 11) or any(
                            k in table_text
                            for k in ["Data pregão", "Nr. nota", "Negociação", "Especificação"]
                        )

                        if not is_negociacao:
                            # Heurística fallback: tente encontrar linhas que contenham quantidade+preço
                            # MAS USANDO A MESMA VALIDAÇÃO que acima
                            for row in table[1:]:
                                if not row or all(not (str(c).strip()) for c in row):
                                    continue

                                cells = [(c or "").strip() for c in row]

                                # APLICAR VALIDAÇÃO: recusa headers/footers/summaries
                                if not _is_valid_data_row(cells, is_negotiation_table=False):
                                    continue

                                try:
                                    # Verifica se é uma linha válida de negociação
                                    ticker = _extract_ticker_from_cells(cells, ticker_mapping)
                                    if not ticker:
                                        continue  # Não conseguiu extrair ticker válido

                                    # Procura por padrões de número (quantidade/price)
                                    possible_qty = None
                                    possible_price = None
                                    for c in cells:
                                        if re.search(r"\d+[\.,]\d+", c):
                                            # assume price-like
                                            if not possible_price:
                                                possible_price = _normalize_number(c)
                                        elif re.search(
                                            r"^\d+$", c.replace(".", "").replace(",", "")
                                        ):
                                            if not possible_qty:
                                                possible_qty = _normalize_number(c)

                                    if not possible_qty and not possible_price:
                                        continue

                                    operacao = ""
                                    for c in cells:
                                        if (
                                            " C " in f" {c} ".upper()
                                            or c.strip().upper() == "C"
                                            or c.strip().upper() == "V"
                                        ):
                                            operacao = (
                                                "C"
                                                if "C" in c.upper()
                                                else "V" if "V" in c.upper() else ""
                                            )
                                            if operacao:
                                                break

                                    dados_extraidos.append(
                                        {
                                            "Data": data_pregao,
                                            "Ticker": ticker,
                                            "Operação": operacao,
                                            "Quantidade": possible_qty or "",
                                            "Preço": possible_price or "",
                                        }
                                    )
                                    registros_pagina += 1
                                except Exception:
                                    continue
                            # fim heurística fallback
                        else:
                            # Para tabelas de negociação, processa TODAS as linhas (não pula a primeira)
                            # A detecção de cabeçalho é feita dentro de _is_valid_data_row()
                            start_row = 0 if is_negociacao else 1
                            for row in table[start_row:]:
                                # Filtra linhas vazias
                                if not row or all(not (str(c).strip()) for c in row):
                                    continue

                                cells = [(c or "").strip() for c in row]

                                # Verifica se é uma linha válida de negociação
                                if not _is_valid_data_row(cells, is_negotiation_table=True):
                                    continue

                                try:
                                    # Mapeamento comum observado em amostras:
                                    # col[2] = operação (C/V), col[5] = especificação (nome do ativo), col[7] = quantidade, col[8] = preço

                                    # Extrai ticker de forma robusta
                                    ticker = _extract_ticker_from_cells(cells, ticker_mapping)
                                    if not ticker:
                                        continue  # Não conseguiu extrair ticker válido

                                    operacao = ""
                                    if len(cells) > 2 and cells[2]:
                                        operacao = (
                                            "C"
                                            if "C" in cells[2].upper()
                                            else ("V" if "V" in cells[2].upper() else "")
                                        )

                                    quantidade_raw = cells[7] if len(cells) > 7 else ""
                                    preco_raw = cells[8] if len(cells) > 8 else ""

                                    quantidade = _normalize_number(quantidade_raw)
                                    preco = _normalize_number(preco_raw)

                                    # Se não houver quantidade nem preço, provavelmente não é linha de negócio
                                    if not quantidade and not preco:
                                        continue

                                    dados_extraidos.append(
                                        {
                                            "Data": data_pregao,
                                            "Ticker": ticker,
                                            "Operação": operacao,
                                            "Quantidade": quantidade,
                                            "Preço": preco,
                                        }
                                    )
                                    registros_pagina += 1
                                except Exception as e:
                                    logger.debug(f"   ⚠️  Erro ao extrair linha: {str(e)}")
                                    continue

                    # FALLBACK: Extrair operações diretamente do texto como backup
                    # Isso trata casos onde pdfplumber falha ao extrair todas as linhas das tabelas
                    # (ex: operações do meio ficam faltando na divisão de tabelas)
                    if data_pregao:
                        operacoes_texto = _extract_operations_from_text(
                            texto_topo, data_pregao, ticker_mapping
                        )

                        # Conta quantas vezes cada assinatura (Data+Ticker+Qtd+Preço) já existe
                        # nas operações extraídas da tabela. Usa Counter (e não set) para
                        # preservar operações idênticas legítimas — ex: 2 compras do mesmo ativo
                        # na mesma data, mesma quantidade e mesmo preço na mesma nota.
                        operacoes_existentes = Counter()
                        for op in dados_extraidos:
                            sig = (
                                op.get("Data"),
                                op.get("Ticker"),
                                op.get("Quantidade"),
                                op.get("Preço"),
                            )
                            operacoes_existentes[sig] += 1

                        # Pré-computa quantas vezes cada sig aparece no texto extraído
                        texto_count = Counter()
                        for op in operacoes_texto:
                            sig = (
                                op.get("Data"),
                                op.get("Ticker"),
                                op.get("Quantidade"),
                                op.get("Preço"),
                            )
                            texto_count[sig] += 1

                        # Adiciona operações do texto apenas para a quantidade excedente.
                        # Permite preservar operações idênticas legítimas (mesmo ativo,
                        # mesma data, mesma qtd, mesmo preço na mesma nota) que o parser
                        # de tabela pode ter capturado apenas parcialmente.
                        novas_operacoes = 0
                        texto_adicionadas = Counter()
                        for op in operacoes_texto:
                            sig = (
                                op.get("Data"),
                                op.get("Ticker"),
                                op.get("Quantidade"),
                                op.get("Preço"),
                            )
                            if texto_adicionadas[sig] + operacoes_existentes[sig] < texto_count[sig]:
                                dados_extraidos.append(op)
                                texto_adicionadas[sig] += 1
                                novas_operacoes += 1

                        if novas_operacoes > 0:
                            logger.debug(
                                f"   ℹ️  Adicionadas {novas_operacoes} operação(ões) extraída(s) do texto"
                            )
                            registros_pagina += novas_operacoes

                    if registros_pagina > 0:
                        logger.debug(
                            f"   ✓ Página {num_pagina}/{total_paginas}: {registros_pagina} registro(s) extraído(s)"
                        )

                except Exception as e:
                    logger.error(f"   ✗ Erro ao processar página {num_pagina}: {str(e)}")
                    continue

        total_registros = len(dados_extraidos)
        if total_registros > 0:
            logger.info(f"✓ {arquivo_nome}: {total_registros} registro(s) extraído(s) com sucesso")
        else:
            logger.warning(f"⚠️  {arquivo_nome}: Nenhum registro extraído")
        sys.stderr.flush()

    except FileNotFoundError:
        logger.error(f"✗ Arquivo não encontrado: {arquivo_nome}")
    except Exception as e:
        logger.error(f"✗ Erro ao processar {arquivo_nome}: {str(e)}")

    return dados_extraidos


def analisar_pasta_ou_zip(caminho, year_filter: Optional[int] = None, sort_by: str = "name"):
    todos_dados = []
    arquivos_processados = 0
    arquivos_erro = 0
    arquivos_ignorados = 0

    try:
        logger.info("=" * 60)
        logger.info("🚀 INICIANDO PROCESSAMENTO")
        if year_filter is not None:
            logger.info(f"🔍 Filtro de ano ativo: {year_filter}")
        logger.info("=" * 60)

        # Resolve caminho relativo se necessário
        if not os.path.isabs(caminho):
            caminho_resolvido = os.path.join(os.path.dirname(__file__), caminho)
            if os.path.exists(caminho_resolvido):
                caminho = caminho_resolvido

        # Validação do caminho fornecido
        if not os.path.exists(caminho):
            logger.error(f"✗ Caminho não encontrado: {caminho}")
            return pd.DataFrame()

        total_arquivos = _count_total_pdfs(caminho)
        logger.info(f"📥 Total estimado de PDFs para processar: {total_arquivos}")

        if total_arquivos == 0:
            logger.warning("⚠️  Nenhum arquivo PDF encontrado para processar")
            return pd.DataFrame()

        # Cria a lista de tarefas (uniformiza arquivos diretos e dentro de ZIPs)
        tarefas = []

        if caminho.endswith(".zip") or (os.path.isfile(caminho) and zipfile.is_zipfile(caminho)):
            tarefas_tipo = "single_zip"
            zip_stat = os.stat(caminho)
            with zipfile.ZipFile(caminho, "r") as z:
                for f in z.namelist():
                    if f.endswith(".pdf"):
                        # Aplica filtro de ano se especificado
                        if _should_process_file(f, year_filter):
                            info = z.getinfo(f)
                            e_mtime = datetime(*info.date_time).timestamp() if info.date_time[0] > 0 else zip_stat.st_mtime
                            tarefas.append({
                                "type": "zip_entry",
                                "zip": caminho,
                                "name": f,
                                "_name": os.path.basename(f),
                                "_mtime": e_mtime,
                                "_ctime": zip_stat.st_ctime,
                            })
                        else:
                            arquivos_ignorados += 1

        elif os.path.isdir(caminho):
            # PDFs diretos
            for f in os.listdir(caminho):
                if f.endswith(".pdf"):
                    # Aplica filtro de ano se especificado
                    if _should_process_file(f, year_filter):
                        full_path = os.path.join(caminho, f)
                        st = os.stat(full_path)
                        tarefas.append({
                            "type": "file",
                            "path": full_path,
                            "_name": f,
                            "_mtime": st.st_mtime,
                            "_ctime": st.st_ctime,
                        })
                    else:
                        arquivos_ignorados += 1

            # PDFs dentro de ZIPs na pasta
            for zf in [f for f in os.listdir(caminho) if f.endswith(".zip")]:
                caminho_zip = os.path.join(caminho, zf)
                try:
                    zip_stat = os.stat(caminho_zip)
                    with zipfile.ZipFile(caminho_zip, "r") as z:
                        for entry in z.namelist():
                            if entry.endswith(".pdf"):
                                # Aplica filtro de ano se especificado
                                if _should_process_file(entry, year_filter):
                                    info = z.getinfo(entry)
                                    e_mtime = datetime(*info.date_time).timestamp() if info.date_time[0] > 0 else zip_stat.st_mtime
                                    tarefas.append(
                                        {
                                            "type": "zip_entry",
                                            "zip": caminho_zip,
                                            "name": entry,
                                            "_name": os.path.basename(entry),
                                            "_mtime": e_mtime,
                                            "_ctime": zip_stat.st_ctime,
                                        }
                                    )
                                else:
                                    arquivos_ignorados += 1
                except Exception as e:
                    logger.warning(f"⚠️  Não foi possível listar ZIP {zf}: {str(e)}")

        else:
            logger.error(f"✗ Caminho não é arquivo ZIP ou pasta: {caminho}")
            return pd.DataFrame()

        # Ordena a lista de tarefas pelo critério escolhido
        _SORT_FIELDS = {"name": "_name", "mtime": "_mtime", "ctime": "_ctime"}
        sort_field = _SORT_FIELDS.get(sort_by, "_name")
        tarefas.sort(key=lambda t: t[sort_field])
        logger.info(f"🗂️  Ordenação de arquivos: {sort_by} | {len(tarefas)} arquivo(s) a processar")

        # Processando PDFs sem barra de progresso (logs indicam progresso suficientemente)
        try:
            for tarefa in tarefas:
                if stop_processing:
                    logger.warning(
                        "⏸️ Interrupção detectada — finalizando processamento após o arquivo atual."
                    )
                    break

                if tarefa["type"] == "file":
                    try:
                        dados = processar_pdf(tarefa["path"])
                        todos_dados.extend(dados)
                        arquivos_processados += 1
                    except Exception as e:
                        logger.error(f"✗ Erro ao processar {tarefa['path']}: {str(e)}")
                        arquivos_erro += 1

                elif tarefa["type"] == "zip_entry":
                    try:
                        with zipfile.ZipFile(tarefa["zip"], "r") as z:
                            with z.open(tarefa["name"]) as f:
                                bio = criar_bytesio_com_nome(
                                    f.read(), os.path.basename(tarefa["name"])
                                )
                                dados = processar_pdf(bio)
                                todos_dados.extend(dados)
                                arquivos_processados += 1
                    except Exception as e:
                        logger.error(
                            f"✗ Erro ao processar {tarefa['name']} do ZIP {os.path.basename(tarefa['zip'])}: {str(e)}"
                        )
                        arquivos_erro += 1

        except KeyboardInterrupt:
            logger.warning(
                "⚠️  Execução interrompida pelo usuário (KeyboardInterrupt). Salvando progresso parcial..."
            )
            # stop_processing já será True pelo handler; fora do laço iremos exportar o parcial

        # Resumo final
        logger.info("\n" + "=" * 60)
        logger.info("📊 RESUMO DO PROCESSAMENTO")
        logger.info("=" * 60)
        logger.info(f"✓ Arquivos processados com sucesso: {arquivos_processados}")
        if arquivos_erro > 0:
            logger.warning(f"⚠️  Arquivos com erro: {arquivos_erro}")
        if arquivos_ignorados > 0:
            logger.info(f"⏭️ Arquivos ignorados (fora do filtro de ano): {arquivos_ignorados}")
        logger.info(f"📈 Total de registros extraídos: {len(todos_dados)}")
        logger.info("=" * 60)

        df = pd.DataFrame(todos_dados)
        return df

    except Exception as e:
        logger.error(f"✗ Erro inesperado durante o processamento: {str(e)}")
        logger.info("=" * 60)
        return pd.DataFrame()


def ordenar_dados_por_data(df):
    """Ordena o DataFrame por Data (do mais antigo para o mais recente).

    Args:
        df (pd.DataFrame): DataFrame com coluna 'Data' em formato DD/MM/YYYY

    Returns:
        pd.DataFrame: DataFrame ordenado por data
    """
    if df.empty:
        return df

    try:
        # Converte coluna Data para datetime (formato DD/MM/YYYY)
        df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y")

        # Ordena por Data (do mais antigo para o mais recente) e depois por Ticker (alfabético)
        df = df.sort_values(["Data", "Ticker"], ascending=True)

        # Converte Data de volta para string no formato original DD/MM/YYYY
        df["Data"] = df["Data"].dt.strftime("%d/%m/%Y")

        logger.info(
            "✓ Dados ordenados por data (mais antigo para o mais recente) e depois por ticker"
        )
        return df.reset_index(drop=True)

    except Exception as e:
        logger.warning(f"⚠️  Erro ao ordenar dados por data: {str(e)}")
        return df


def criar_aba_arvore(df):
    """Cria um DataFrame com estrutura de árvore partindo a Data em Ano/Mês/Dia.

    As colunas de Ano, Mês e Dia são preenchidas apenas ao mudar o período,
    criando uma visualização em árvore hierárquica.

    Args:
        df (pd.DataFrame): DataFrame ordenado com coluna 'Data' em DD/MM/YYYY

    Returns:
        pd.DataFrame: DataFrame com colunas [Ano, Mês, Dia, Data, Ticker, Operação,
                      Quantidade, Preço]
    """
    if df.empty:
        return pd.DataFrame()

    try:
        # Cria cópia para não modificar o original
        df_arvore = df.copy()

        # Extrai Ano, Mês, Dia da Data
        df_arvore["Data_dt"] = pd.to_datetime(df_arvore["Data"], format="%d/%m/%Y")
        df_arvore["Ano"] = df_arvore["Data_dt"].dt.year.astype(str)
        df_arvore["Mes"] = df_arvore["Data_dt"].dt.month.astype(str).str.zfill(2)
        df_arvore["Dia"] = df_arvore["Data_dt"].dt.day.astype(str).str.zfill(2)

        # Monta chave de período (Ano-Mês-Dia)
        df_arvore["periodo"] = df_arvore["Ano"] + "-" + df_arvore["Mes"] + "-" + df_arvore["Dia"]

        # Identifica onde o período muda em relação à linha anterior
        df_arvore["periodo_anterior"] = df_arvore["periodo"].shift(1)
        df_arvore["muda_ano"] = df_arvore["Ano"] != df_arvore["Ano"].shift(1)
        df_arvore["muda_mes"] = (df_arvore["Ano"] + "-" + df_arvore["Mes"]) != (
            df_arvore["Ano"].shift(1) + "-" + df_arvore["Mes"].shift(1)
        )
        df_arvore["muda_dia"] = df_arvore["periodo"] != df_arvore["periodo"].shift(1)

        # Preenche Ano, Mês, Dia apenas quando mudam (criando efeito de árvore)
        df_arvore.loc[~df_arvore["muda_ano"], "Ano"] = ""
        df_arvore.loc[~df_arvore["muda_mes"], "Mes"] = ""
        df_arvore.loc[~df_arvore["muda_dia"], "Dia"] = ""

        # Ordena colunas: Ano, Mês, Dia, Data, Ticker, Operação, Quantidade, Preço
        colunas_arvore = ["Ano", "Mes", "Dia", "Data", "Ticker", "Operação", "Quantidade", "Preço"]
        df_arvore = df_arvore[colunas_arvore]

        # Remove coluna auxiliar de data convertida
        if "Data_dt" in df_arvore.columns:
            df_arvore = df_arvore.drop("Data_dt", axis=1, errors="ignore")

        return df_arvore.reset_index(drop=True)

    except Exception as e:
        logger.warning(f"⚠️  Erro ao criar aba de árvore: {str(e)}")
        return df.copy()


def exportar_dados(df, formato=None, ticker=None):
    """Exporta os dados extraídos para o formato especificado.

    Args:
        df (pd.DataFrame): DataFrame com os dados extraídos
        formato (str): Formato de saída (csv, xlsx, json). Se None, usa config.
        ticker (str): Ticker filtrado, quando aplicável. Incluído no nome do arquivo.

    Returns:
        bool: True se exportado com sucesso, False caso contrário
    """
    if df.empty:
        logger.warning("⚠️  Nenhum dado para exportar")
        return False

    try:
        # Ordena dados por data antes de exportar
        df = ordenar_dados_por_data(df)
        # Obtém formato da config se não fornecido
        if formato is None:
            formato = config.get_output_format().lower()

        # Cria pasta de output
        pasta_output = config.get_output_folder()
        if not os.path.exists(pasta_output):
            os.makedirs(pasta_output)
            logger.info(f"✓ Pasta de saída criada: {pasta_output}")

        # Gera nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ticker_suffix = f"_{_normalize_ticker_value(ticker)}" if ticker else ""

        # Exporta no formato escolhido
        if formato == "csv":
            arquivo_saida = os.path.join(pasta_output, f"dados_extraidos{ticker_suffix}_{timestamp}.csv")
            df.to_csv(arquivo_saida, index=False, encoding="utf-8-sig")
            logger.info(f"✓ Dados exportados para CSV: {arquivo_saida}")
            logger.info(f"   Linhas: {len(df)} | Colunas: {len(df.columns)}")

        elif formato == "xlsx":
            arquivo_saida = os.path.join(pasta_output, f"dados_extraidos{ticker_suffix}_{timestamp}.xlsx")
            # Cria writer para múltiplas abas
            with pd.ExcelWriter(arquivo_saida, engine="openpyxl") as writer:
                # Aba 1: Dados completos e ordenados
                # Formata coluna Preço com separador decimal em vírgula (padrão brasileiro)
                df_export = df.copy()
                if "Preço" in df_export.columns:
                    df_export["Preço"] = (
                        df_export["Preço"].astype(str).str.replace(".", ",", regex=False)
                    )
                df_export.to_excel(writer, sheet_name="Dados", index=False)
                logger.info(
                    f"✓ Aba 'Dados' criada: {len(df_export)} linhas, {len(df_export.columns)} colunas"
                )

                # Aba 2: Estrutura de árvore (Ano/Mês/Dia hierárquicos)
                df_arvore = criar_aba_arvore(df)
                if "Preço" in df_arvore.columns:
                    df_arvore["Preço"] = (
                        df_arvore["Preço"].astype(str).str.replace(".", ",", regex=False)
                    )
                df_arvore.to_excel(writer, sheet_name="Árvore", index=False)
                logger.info(
                    f"✓ Aba 'Árvore' criada: {len(df_arvore)} linhas (estrutura hierárquica)"
                )

            logger.info(f"✓ Arquivo XLSX exportado com 2 abas: {arquivo_saida}")

        elif formato == "json":
            arquivo_saida = os.path.join(pasta_output, f"dados_extraidos{ticker_suffix}_{timestamp}.json")
            df.to_json(arquivo_saida, orient="records", indent=2, force_ascii=False)
            logger.info(f"✓ Dados exportados para JSON: {arquivo_saida}")
            logger.info(f"   Linhas: {len(df)} | Colunas: {len(df.columns)}")
        else:
            logger.error(f"✗ Formato não suportado: {formato}")
            logger.info("   Formatos suportados: csv, xlsx, json")
            return False

        return True

    except ImportError as e:
        if "openpyxl" in str(e) and formato == "xlsx":
            logger.error("✗ Erro: openpyxl não instalado. Para usar XLSX, instale com:")
            logger.error("   pip install openpyxl")
        else:
            logger.error(f"✗ Biblioteca não encontrada: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"✗ Erro ao exportar dados: {str(e)}")
        return False


if __name__ == "__main__":
    # Cria parser de argumentos de linha de comando
    parser = argparse.ArgumentParser(
        description="Extrator de Notas de Negociação da Clear Corretora",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python3 extratorNotasCorretagem.py                         # Processa todos os PDFs (ordem: nome)
  python3 extratorNotasCorretagem.py --year 2024             # Apenas PDFs de 2024
  python3 extratorNotasCorretagem.py -y 2026 -t VALE3        # Ano + ticker
  python3 extratorNotasCorretagem.py --sort-by mtime         # Ordena por data de modificação
  python3 extratorNotasCorretagem.py --sort-by ctime         # Ordena por data de criação
        """,
    )
    parser.add_argument(
        "--year",
        "-y",
        type=int,
        default=None,
        help="Filtrar por ano (extrair apenas PDFs com esse ano no nome do arquivo)",
    )
    parser.add_argument(
        "--ticker",
        "-t",
        type=str,
        default=None,
        help="Filtrar por ticker (ex: PSSA3)",
    )
    parser.add_argument(
        "--sort-by",
        "-s",
        choices=["name", "mtime", "ctime"],
        default="name",
        help="Critério de ordenação dos arquivos antes de processar (name=nome, mtime=modificação, ctime=criação). Padrão: name",
    )

    args = parser.parse_args()
    year_filter = args.year
    ticker_filter = args.ticker
    sort_by = args.sort_by

    # Caminho da pasta com os arquivos de entrada
    caminho_pasta = config.get_input_folder()

    # Resolve o caminho absoluto
    caminho_absoluto = config.resolve_path(caminho_pasta)

    logger.info(f"📂 Diretório de entrada: {caminho_pasta}")
    logger.info(f"🔍 Caminho absoluto: {caminho_absoluto}\n")
    if ticker_filter:
        logger.info(f"🔎 Filtro de ticker ativo: {_normalize_ticker_value(ticker_filter)}")
    logger.info(f"🗂️  Ordenação de arquivos: {sort_by}")

    # Se a pasta não existe, tenta informar melhor
    if not os.path.exists(caminho_absoluto):
        logger.error(f"✗ Pasta não encontrada: {caminho_absoluto}")
        logger.info("\n💡 Dicas:")
        logger.info("   1. Verifique se o caminho está correto no arquivo application.properties")
        logger.info("   2. Certifique-se de que a pasta especificada existe")
        logger.info("   3. Coloque seus arquivos PDF ou ZIP dentro dessa pasta")
    else:
        logger.info("✓ Pasta encontrada. Processando...\n")
        df = analisar_pasta_ou_zip(caminho_absoluto, year_filter=year_filter, sort_by=sort_by)
        df = _filter_dataframe_by_ticker(df, ticker_filter)

        if not df.empty:
            logger.info(f"\n📋 Primeiras linhas dos dados extraídos:")
            logger.info(f"\n{df.head()}")

            # Exporta os dados
            logger.info("\n" + "=" * 60)
            logger.info("💾 EXPORTANDO DADOS")
            logger.info("=" * 60)
            formato = config.get_output_format()
            sucesso = exportar_dados(df, formato, ticker=ticker_filter)

            if sucesso:
                logger.info(f"\n✓ Processamento concluído com sucesso!")
            else:
                logger.warning("⚠️  Dados extraídos mas não foi possível exportar.")
        else:
            logger.warning("⚠️  Nenhum dado foi extraído. Verifique os arquivos PDF na pasta.")
