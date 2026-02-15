import pdfplumber
import pandas as pd
import re
import os
import zipfile
import logging
import signal
import sys
from io import BytesIO
from datetime import datetime
from tqdm import tqdm
from config import get_config

# Carregar configurações
config = get_config()

# Configuração de Logging
logging_level = config.get_logging_level()
logging.basicConfig(
    level=getattr(logging, logging_level),
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Flag para controle de interrupção pelo usuário (Ctrl+C)
stop_processing = False

def _handle_sigint(signum, frame):
    global stop_processing
    stop_processing = True
    logger.warning("⏸️ Interrupção solicitada pelo usuário (Ctrl+C). Finalizando após o arquivo atual...")

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

def processar_pdf(pdf_file, senha=None):
    dados_extraidos = []
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
                        # Identifica a tabela correta pelo cabeçalho
                        if any("Especificação do título" in str(cell) for cell in table):
                            for row in table[1:]:
                                # Filtra linhas vazias ou de resumo
                                if not row or len(row) < 5 or "Resumo" in str(row):
                                    continue
                                
                                try:
                                    # Mapeamento de colunas baseado nos fontes [1, 5, 11]
                                    # Nota: A posição pode variar se o PDF tiver colunas vazias
                                    operacao = "C" if "C" in str(row[3]) else "V"
                                    especificacao = str(row[12])
                                    quantidade = str(row[2]).split('\n')[-1] # Lida com quebras [2]
                                    preco = str(row[13] if row[13] else row[14]).split('\n')
                                    
                                    dados_extraidos.append({
                                        "Data": data_pregao,
                                        "Ticker": limpar_ticker(especificacao, DE_PARA_TICKERS),
                                        "Operação": operacao,
                                        "Quantidade": quantidade,
                                        "Preço": preco.replace('.', '').replace(',', '.')
                                    })
                                    registros_pagina += 1
                                except (IndexError, ValueError) as e:
                                    logger.warning(f"   ⚠️  Erro ao extrair linha na página {num_pagina}: {str(e)}")
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

def analisar_pasta_ou_zip(caminho):
    todos_dados = []
    arquivos_processados = 0
    arquivos_erro = 0

    try:
        logger.info("=" * 60)
        logger.info("🚀 INICIANDO PROCESSAMENTO")
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
                        tarefas.append({'type': 'zip_entry', 'zip': caminho, 'name': f})

        elif os.path.isdir(caminho):
            # PDFs diretos
            for f in os.listdir(caminho):
                if f.endswith('.pdf'):
                    tarefas.append({'type': 'file', 'path': os.path.join(caminho, f)})

            # PDFs dentro de ZIPs na pasta
            for zf in [f for f in os.listdir(caminho) if f.endswith('.zip')]:
                caminho_zip = os.path.join(caminho, zf)
                try:
                    with zipfile.ZipFile(caminho_zip, 'r') as z:
                        for entry in z.namelist():
                            if entry.endswith('.pdf'):
                                tarefas.append({'type': 'zip_entry', 'zip': caminho_zip, 'name': entry})
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
        df = analisar_pasta_ou_zip(caminho_absoluto)
        
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
