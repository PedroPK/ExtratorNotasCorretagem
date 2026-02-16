import pdfplumber
import pandas as pd
import re
import os
import zipfile
import logging
import signal
import sys
import argparse
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional
from tqdm import tqdm
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flag para controle de interrupção pelo usuário (Ctrl+C)
stop_processing = False

def _handle_sigint(signum, frame):
    global stop_processing
    if not stop_processing:
        stop_processing = True
        logger.warning("⏸️ Interrupção solicitada pelo usuário (Ctrl+C). Finalizando após o arquivo atual...")
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
        if caminho.endswith('.zip') or (os.path.isfile(caminho) and zipfile.is_zipfile(caminho)):
            with zipfile.ZipFile(caminho, 'r') as z:
                return len([f for f in z.namelist() if f.endswith('.pdf')])

        if os.path.isdir(caminho):
            total = 0
            # PDFs diretos
            total += len([f for f in os.listdir(caminho) if f.endswith('.pdf')])
            # PDFs dentro de ZIPs na pasta
            zips = [f for f in os.listdir(caminho) if f.endswith('.zip')]
            for zf in zips:
                try:
                    with zipfile.ZipFile(os.path.join(caminho, zf), 'r') as z:
                        total += len([f for f in z.namelist() if f.endswith('.pdf')])
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
    #"FIAGRO SUNO": "SNAG11",
    #"SUNO FIC FI": "SNCI11",
    #"FII ATRIO": "ARRI11",
    #"FII KINEA RI": "KNCR11",
    #"FII HSI CRI": "HSAF11"
}

def criar_bytesio_com_nome(conteudo, nome_arquivo):
    """Cria um BytesIO com atributo 'name' para compatibilidade."""
    bio = BytesIO(conteudo)
    bio.name = nome_arquivo
    return bio

def limpar_ticker(texto, dicionario):
    """Extrai o ticker ou usa o de-para para nomes conhecidos."""
    texto = texto.replace('\n', ' ').strip()
    # Tenta encontrar um padrão de Ticker (4 letras + 2 números)
    match = re.search(r'[A-Z]{4}\d{2}', texto)
    if match:
        return match.group(0)
    
    # Se não achar o Ticker puro, busca no dicionário De-Para
    for nome, ticker in dicionario.items():
        if nome in texto.upper():
            return ticker
    return texto # Retorna o original se não mapear


def _normalize_number(text):
    """Converte números no formato brasileiro para ponto decimal (ex: '1.234,56' -> '1234.56')."""
    if not text:
        return ''
    s = str(text).strip()
    # Remove espaços e símbolos extras
    s = s.replace('\xa0', '').replace(' ', '')
    # Se já tem apenas dígitos e ponto, tenta retornar
    # Substitui milhares (.) e decimal (,) -> '.'
    # Primeiro, remove pontos que representam milhares
    # Mas cuidado: se houver apenas one dot and no comma, keep it
    if ',' in s:
        s = s.replace('.', '')
        s = s.replace(',', '.')
    else:
        # Remove any non-digit or dot
        s = re.sub(r'[^0-9\.]', '', s)
    return s


def _is_likely_header(cells):
    """Verifica se a linha parece ser um cabeçalho (nomes de colunas)."""
    if not cells:
        return False
    
    # Palavras típicas de cabeçalhos
    header_keywords = ['data', 'ativo', 'especif', 'qtd', 'preço', 'valor', 'operação', 'nota', 'corretora']
    header_text = ' '.join([str(c).lower() for c in cells if c])
    
    # Se muitas células têm pontos/dois-pontos, pode ser cabeçalho
    if header_text.count(':') > 3:
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
        'resumo', 'total', 'debêntures', 'vendas', 'compras', 'opções', 'termo',
        'taxa', 'emolumentos', 'transf', 'ativos', 'custodiante', 'clearing',
        'especificações', 'bovespa', 'cblc', 'cliente', 'código', 'assessor',
        'participante', 'folha', 'data pregão', 'negociação', 'c.p.f', 'cnpj',
        'valor das oper', 'valor líquido', 'qualificado', 'nota de negociação',
        'impostos', 'i.r.r.f', 'execução', 'custódia', 'bolsa', 'operacional',
        'custos', 'agente', 'qualificado', 'especificações diversas',
        'coluna q', 'liquidação', 'agente do qualificado', '(*)', 'observações',
        'líquido para',  # Settlement rows, not transactions
        'conta', 'saldo', 'c.m.c', 'participante destino'  # Account/routing info
    ]
    
    # Para tabelas de negociação (11 colunas), validação menos rigorosa
    if is_negotiation_table:
        # Apenas rejeita se tem palavras-chave muito óbvias (menos a de "bovespa")
        strict_skip = [
            'resumo', 'total', 'debêntures', 'taxa', 'emolumentos', 'custos',
            'líquido para', 'client', 'código', 'c.p.f', 'cnpj', 'observações',
            '(*)', 'saldo', 'conta'
        ]
        row_text = ' '.join(cells).upper()
        for keyword in strict_skip:
            if keyword.upper() in row_text:
                return False
    else:
        # Para outras tabelas, validação rigorosa
        row_text = ' '.join(cells).upper()
        for keyword in skip_keywords:
            if keyword.upper() in row_text:
                return False
    
    # Uma linha válida deve ter pelo menos um número (quantidade ou preço)
    has_number = False
    for cell in cells:
        # Aceita tanto números decimais quanto inteiros
        if re.search(r'\d', str(cell)):
            has_number = True
            break
    
    return has_number


def _extract_ticker_from_cells(cells, ticker_mapping=None):
    """
    Extrai ticker da linha, buscando padrão B3 ou nome de ativo conhecido.
    
    Estratégia:
    1. Procura por padrão ticker B3 (4 letras + 2 dígitos)
    2. Busca em DE_PARA_TICKERS (hardcoded)
    3. Busca em ticker_mapping (carregado de resouces/tickerMapping.properties)
    """
    for cell in cells:
        cell_str = str(cell).strip()
        
        # Tenta padrão ticker B3 (4 letras + 2 dígitos)
        match = re.search(r'[A-Z]{4}\d{2}', cell_str)
        if match:
            return match.group(0)
        
        # Tenta encontrar nome conhecido de ativo (DE_PARA hardcoded)
        for nome, ticker in DE_PARA_TICKERS.items():
            if nome.upper() in cell_str.upper():
                return ticker
        
        # Tenta ticker_mapping (carregado de arquivo de configuração)
        if ticker_mapping:
            for nome, ticker in ticker_mapping.items():
                if nome.upper() in cell_str.upper():
                    return ticker
    
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
    match = re.search(r'\b(19|20)\d{2}\b', filename)
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


def processar_pdf(pdf_file, senha=None):
    dados_extraidos = []
    
    # Carrega mapeamento de tickers do arquivo de configuração
    ticker_mapping = config.get_ticker_mapping()
    
    # Tratamento inteligente do nome do arquivo para diferentes tipos de entrada
    if isinstance(pdf_file, str):
        arquivo_nome = os.path.basename(pdf_file)
    else:
        # Para file objects e BytesIO, tenta obter 'name', senão usa genérico
        arquivo_nome = getattr(pdf_file, 'name', 'pdf_temporario.pdf')
    
    try:
        logger.info(f"📄 Processando arquivo: {arquivo_nome}")
        
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
                logger.warning(f"⚠️  {arquivo_nome}: PDF protegido. Configure 'pdf.password' em application.properties")
                return dados_extraidos
        
        with pdf:
            total_paginas = len(pdf.pages)
            logger.debug(f"   Total de páginas: {total_paginas}")
            
            for num_pagina, page in enumerate(pdf.pages, 1):
                try:
                    # Extração da Data (procura por "Data pregão") [3, 8, 9]
                    texto_topo = page.extract_text()
                    data_pregao = None
                    match_data = re.search(r'(\d{2}/\d{2}/\d{4})', texto_topo)
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
                        table_text = ' '.join(' '.join([str(c) for c in row if c]) for row in table)
                        is_negociacao = (num_cols == 11) or any(k in table_text for k in ['Data pregão', 'Nr. nota', 'Negociação', 'Especificação'])

                        if not is_negociacao:
                            # Heurística fallback: tente encontrar linhas que contenham quantidade+preço
                            # MAS USANDO A MESMA VALIDAÇÃO que acima
                            for row in table[1:]:
                                if not row or all(not (str(c).strip()) for c in row):
                                    continue

                                cells = [(c or '').strip() for c in row]
                                
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
                                        if re.search(r'\d+[\.,]\d+', c):
                                            # assume price-like
                                            if not possible_price:
                                                possible_price = _normalize_number(c)
                                        elif re.search(r'^\d+$', c.replace('.', '').replace(',', '')):
                                            if not possible_qty:
                                                possible_qty = _normalize_number(c)

                                    if not possible_qty and not possible_price:
                                        continue

                                    operacao = ''
                                    for c in cells:
                                        if ' C ' in f' {c} '.upper() or c.strip().upper() == 'C' or c.strip().upper() == 'V':
                                            operacao = 'C' if 'C' in c.upper() else 'V' if 'V' in c.upper() else ''
                                            if operacao:
                                                break

                                    dados_extraidos.append({
                                        "Data": data_pregao,
                                        "Ticker": ticker,
                                        "Operação": operacao,
                                        "Quantidade": possible_qty or '',
                                        "Preço": possible_price or ''
                                    })
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

                                cells = [(c or '').strip() for c in row]
                                
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
                                    
                                    operacao = ''
                                    if len(cells) > 2 and cells[2]:
                                        operacao = 'C' if 'C' in cells[2].upper() else ('V' if 'V' in cells[2].upper() else '')

                                    quantidade_raw = cells[7] if len(cells) > 7 else ''
                                    preco_raw = cells[8] if len(cells) > 8 else ''

                                    quantidade = _normalize_number(quantidade_raw)
                                    preco = _normalize_number(preco_raw)

                                    # Se não houver quantidade nem preço, provavelmente não é linha de negócio
                                    if not quantidade and not preco:
                                        continue

                                    dados_extraidos.append({
                                        "Data": data_pregao,
                                        "Ticker": ticker,
                                        "Operação": operacao,
                                        "Quantidade": quantidade,
                                        "Preço": preco
                                    })
                                    registros_pagina += 1
                                except Exception as e:
                                    logger.debug(f"   ⚠️  Erro ao extrair linha: {str(e)}")
                                    continue
                    
                    if registros_pagina > 0:
                        logger.debug(f"   ✓ Página {num_pagina}/{total_paginas}: {registros_pagina} registro(s) extraído(s)")
                        
                except Exception as e:
                    logger.error(f"   ✗ Erro ao processar página {num_pagina}: {str(e)}")
                    continue
        
        total_registros = len(dados_extraidos)
        if total_registros > 0:
            logger.info(f"✓ {arquivo_nome}: {total_registros} registro(s) extraído(s) com sucesso")
        else:
            logger.warning(f"⚠️  {arquivo_nome}: Nenhum registro extraído")
            
    except FileNotFoundError:
        logger.error(f"✗ Arquivo não encontrado: {arquivo_nome}")
    except Exception as e:
        logger.error(f"✗ Erro ao processar {arquivo_nome}: {str(e)}")
    
    return dados_extraidos

def analisar_pasta_ou_zip(caminho, year_filter: Optional[int] = None):
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

        if caminho.endswith('.zip') or (os.path.isfile(caminho) and zipfile.is_zipfile(caminho)):
            tarefas_tipo = 'single_zip'
            with zipfile.ZipFile(caminho, 'r') as z:
                for f in z.namelist():
                    if f.endswith('.pdf'):
                        # Aplica filtro de ano se especificado
                        if _should_process_file(f, year_filter):
                            tarefas.append({'type': 'zip_entry', 'zip': caminho, 'name': f})
                        else:
                            arquivos_ignorados += 1

        elif os.path.isdir(caminho):
            # PDFs diretos
            for f in os.listdir(caminho):
                if f.endswith('.pdf'):
                    # Aplica filtro de ano se especificado
                    if _should_process_file(f, year_filter):
                        tarefas.append({'type': 'file', 'path': os.path.join(caminho, f)})
                    else:
                        arquivos_ignorados += 1

            # PDFs dentro de ZIPs na pasta
            for zf in [f for f in os.listdir(caminho) if f.endswith('.zip')]:
                caminho_zip = os.path.join(caminho, zf)
                try:
                    with zipfile.ZipFile(caminho_zip, 'r') as z:
                        for entry in z.namelist():
                            if entry.endswith('.pdf'):
                                # Aplica filtro de ano se especificado
                                if _should_process_file(entry, year_filter):
                                    tarefas.append({'type': 'zip_entry', 'zip': caminho_zip, 'name': entry})
                                else:
                                    arquivos_ignorados += 1
                except Exception as e:
                    logger.warning(f"⚠️  Não foi possível listar ZIP {zf}: {str(e)}")

        else:
            logger.error(f"✗ Caminho não é arquivo ZIP ou pasta: {caminho}")
            return pd.DataFrame()

        # Barra de progresso global para todos os PDFs
        with tqdm(total=len(tarefas), desc="📥 Processando PDFs", unit="arquivo") as pbar:
            try:
                for tarefa in tarefas:
                    if stop_processing:
                        logger.warning("⏸️ Interrupção detectada — finalizando processamento após o arquivo atual.")
                        break

                    if tarefa['type'] == 'file':
                        try:
                            dados = processar_pdf(tarefa['path'])
                            todos_dados.extend(dados)
                            arquivos_processados += 1
                        except Exception as e:
                            logger.error(f"✗ Erro ao processar {tarefa['path']}: {str(e)}")
                            arquivos_erro += 1
                        finally:
                            pbar.update(1)

                    elif tarefa['type'] == 'zip_entry':
                        try:
                            with zipfile.ZipFile(tarefa['zip'], 'r') as z:
                                with z.open(tarefa['name']) as f:
                                    bio = criar_bytesio_com_nome(f.read(), os.path.basename(tarefa['name']))
                                    dados = processar_pdf(bio)
                                    todos_dados.extend(dados)
                                    arquivos_processados += 1
                        except Exception as e:
                            logger.error(f"✗ Erro ao processar {tarefa['name']} do ZIP {os.path.basename(tarefa['zip'])}: {str(e)}")
                            arquivos_erro += 1
                        finally:
                            pbar.update(1)

            except KeyboardInterrupt:
                logger.warning("⚠️  Execução interrompida pelo usuário (KeyboardInterrupt). Salvando progresso parcial...")
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


def exportar_dados(df, formato=None):
    """Exporta os dados extraídos para o formato especificado.
    
    Args:
        df (pd.DataFrame): DataFrame com os dados extraídos
        formato (str): Formato de saída (csv, xlsx, json). Se None, usa config.
        
    Returns:
        bool: True se exportado com sucesso, False caso contrário
    """
    if df.empty:
        logger.warning("⚠️  Nenhum dado para exportar")
        return False
    
    try:
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
        
        # Exporta no formato escolhido
        if formato == 'csv':
            arquivo_saida = os.path.join(pasta_output, f"dados_extraidos_{timestamp}.csv")
            df.to_csv(arquivo_saida, index=False, encoding='utf-8-sig')
            logger.info(f"✓ Dados exportados para CSV: {arquivo_saida}")
            logger.info(f"   Linhas: {len(df)} | Colunas: {len(df.columns)}")
            
        elif formato == 'xlsx':
            arquivo_saida = os.path.join(pasta_output, f"dados_extraidos_{timestamp}.xlsx")
            df.to_excel(arquivo_saida, index=False, sheet_name="Dados")
            logger.info(f"✓ Dados exportados para XLSX: {arquivo_saida}")
            logger.info(f"   Linhas: {len(df)} | Colunas: {len(df.columns)}")
            
        elif formato == 'json':
            arquivo_saida = os.path.join(pasta_output, f"dados_extraidos_{timestamp}.json")
            df.to_json(arquivo_saida, orient='records', indent=2, force_ascii=False)
            logger.info(f"✓ Dados exportados para JSON: {arquivo_saida}")
            logger.info(f"   Linhas: {len(df)} | Colunas: {len(df.columns)}")
        else:
            logger.error(f"✗ Formato não suportado: {formato}")
            logger.info("   Formatos suportados: csv, xlsx, json")
            return False
        
        return True
        
    except ImportError as e:
        if 'openpyxl' in str(e) and formato == 'xlsx':
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
  python3 extratorNotasCorretagem.py                    # Processa todos os PDFs
  python3 extratorNotasCorretagem.py --year 2024        # Processa apenas PDFs de 2024
  python3 extratorNotasCorretagem.py -y 2026            # Processa apenas PDFs de 2026
        """
    )
    parser.add_argument(
        '--year', '-y',
        type=int,
        default=None,
        help='Filtrar por ano (extrair apenas PDFs com esse ano no nome do arquivo)'
    )
    
    args = parser.parse_args()
    year_filter = args.year
    
    # Caminho da pasta com os arquivos de entrada
    caminho_pasta = config.get_input_folder()
    
    # Resolve o caminho absoluto
    caminho_absoluto = config.resolve_path(caminho_pasta)
    
    logger.info(f"📂 Diretório de entrada: {caminho_pasta}")
    logger.info(f"🔍 Caminho absoluto: {caminho_absoluto}\n")
    
    # Se a pasta não existe, tenta informar melhor
    if not os.path.exists(caminho_absoluto):
        logger.error(f"✗ Pasta não encontrada: {caminho_absoluto}")
        logger.info("\n💡 Dicas:")
        logger.info("   1. Verifique se o caminho está correto no arquivo application.properties")
        logger.info("   2. Certifique-se de que a pasta especificada existe")
        logger.info("   3. Coloque seus arquivos PDF ou ZIP dentro dessa pasta")
    else:
        logger.info("✓ Pasta encontrada. Processando...\n")
        df = analisar_pasta_ou_zip(caminho_absoluto, year_filter=year_filter)
        
        if not df.empty:
            logger.info(f"\n📋 Primeiras linhas dos dados extraídos:")
            logger.info(f"\n{df.head()}")
            
            # Exporta os dados
            logger.info("\n" + "=" * 60)
            logger.info("💾 EXPORTANDO DADOS")
            logger.info("=" * 60)
            formato = config.get_output_format()
            sucesso = exportar_dados(df, formato)
            
            if sucesso:
                logger.info(f"\n✓ Processamento concluído com sucesso!")
            else:
                logger.warning("⚠️  Dados extraídos mas não foi possível exportar.")
        else:
            logger.warning("⚠️  Nenhum dado foi extraído. Verifique os arquivos PDF na pasta.")
