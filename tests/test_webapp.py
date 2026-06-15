import sys
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import webapp as webapp_module


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """
    Fixture compartilhada entre todos os testes que precisam de um cliente HTTP.

    Responsabilidades:
    - Redireciona OUTPUT_DIR para um diretório temporário isolado por teste,
      evitando que arquivos gerados poluam o repositório.
    - Limpa o dicionário de jobs em memória antes e depois de cada teste,
      garantindo isolamento entre execuções paralelas ou sequenciais.
    - Substitui as funções de análise de PDF e exportação pelas versões fake,
      para que os testes de /api/process não dependam de arquivos reais.
    """
    monkeypatch.setattr(webapp_module, "OUTPUT_DIR", tmp_path)
    with webapp_module._JOBS_LOCK:
        webapp_module._PROCESS_JOBS.clear()

    def fake_analisar_pasta_ou_zip(caminho, year_filter=None, sort_by="name"):
        return pd.DataFrame(
            {
                "Data": ["13/05/2026", "12/05/2026"],
                "Ticker": ["VALE3", "PSSA3"],
                "Operação": ["C", "V"],
                "Quantidade": [10, 20],
                "Preço": ["12.34", "56.78"],
            }
        )

    def fake_exportar_dados(df, formato=None, ticker=None):
        suffix = f"_{ticker.upper()}" if ticker else ""
        export_name = f"dados_extraidos{suffix}_20260513_120000.csv"
        (tmp_path / export_name).write_text("Data,Ticker\n13/05/2026,VALE3\n", encoding="utf-8")
        return True

    monkeypatch.setattr(webapp_module, "analisar_pasta_ou_zip", fake_analisar_pasta_ou_zip)
    monkeypatch.setattr(webapp_module, "exportar_dados", fake_exportar_dados)

    test_client = TestClient(webapp_module.app)
    yield test_client
    with webapp_module._JOBS_LOCK:
        webapp_module._PROCESS_JOBS.clear()


def test_index_returns_html(client):
    """
    Verifica que a rota raiz (GET /) entrega a interface web corretamente.

    A página principal deve conter os elementos mínimos esperados pelo usuário:
    área de arrastar/soltar de arquivos e o botão de encerramento do servidor.
    """
    response = client.get("/")

    # A aplicação deve responder com sucesso (não 404, 500, etc.)
    assert response.status_code == 200
    # O HTML deve conter referência à área de drag-and-drop de arquivos
    assert "drag and drop" in response.text.lower()
    # O botão de encerramento do servidor deve estar presente na página
    assert "Encerrar aplicação" in response.text


def test_shutdown_endpoint_is_forbidden_when_not_enabled(client):
    """
    Garante que o endpoint de encerramento remoto é bloqueado por padrão.

    O servidor só deve aceitar o comando de shutdown quando iniciado com a flag
    --allow-shutdown. Sem ela, qualquer chamada deve ser rejeitada com HTTP 403,
    protegendo contra desligamentos acidentais ou não autorizados.
    """
    response = client.post("/api/system/shutdown")

    # O servidor deve recusar a requisição com "Proibido"
    assert response.status_code == 403
    # A mensagem de erro deve deixar claro o motivo da rejeição
    assert "Encerramento remoto" in response.json()["detail"]


def test_process_endpoint_returns_preview_and_download(client):
    """
    Verifica o fluxo completo de processamento de notas de corretagem via PDF.

    Envia um arquivo PDF fake para /api/process e confirma que a resposta contém
    a contagem de registros extraídos, o número de arquivos recebidos, a URL de
    download do CSV gerado e as linhas de pré-visualização da tabela.
    """
    response = client.post(
        "/api/process",
        files={"files": ("nota.pdf", b"dummy pdf", "application/pdf")},
        data={"sort_by": "name", "output_format": "csv"},
    )

    assert response.status_code == 200
    payload = response.json()
    # O fake retorna 2 linhas; o endpoint deve reportar exatamente 2 registros
    assert payload["records_extracted"] == 2
    # O endpoint deve confirmar que recebeu exatamente 1 arquivo
    assert payload["files_received"] == 1
    # A URL de download deve apontar para o arquivo gerado pelo fake_exportar_dados
    assert payload["download_url"] == "/api/download/dados_extraidos_20260513_120000.csv"
    # A pré-visualização deve conter as mesmas 2 linhas retornadas pelo fake
    assert len(payload["preview_rows"]) == 2


def test_download_endpoint_serves_exported_file(client):
    """
    Verifica que o endpoint de download serve o arquivo CSV gerado anteriormente.

    Primeiro dispara um processamento (que cria o arquivo via fake_exportar_dados),
    depois solicita o download pelo nome do arquivo e confirma que o conteúdo é
    entregue com o Content-Type correto.
    """
    client.post(
        "/api/process",
        files={"files": ("nota.pdf", b"dummy pdf", "application/pdf")},
        data={"sort_by": "name", "output_format": "csv"},
    )

    response = client.get("/api/download/dados_extraidos_20260513_120000.csv")

    # O arquivo deve ser encontrado e entregue com sucesso
    assert response.status_code == 200
    # O Content-Type deve indicar CSV para que o navegador ofereça o download corretamente
    assert response.headers["content-type"].startswith("text/csv")


def test_cancel_process_job_sets_cancelling_state(client):
    """
    Verifica que cancelar um job em execução transita seu estado para 'cancelling'.

    Cria manualmente um job com status 'running' no dicionário interno de jobs,
    envia a requisição de cancelamento e confirma que:
    - a resposta imediata do POST já reflete o estado 'cancelling'
    - uma consulta subsequente de status também retorna 'cancelling'

    Isso garante que a sinalização de cancelamento é persistida no estado do job
    e não apenas retornada pontualmente na resposta do POST.
    """
    job_id = "job_cancel_test"
    with webapp_module._JOBS_LOCK:
        webapp_module._PROCESS_JOBS[job_id] = {
            "job_id": job_id,
            "status": "running",
            "message": "Processando",
            "cancel_requested": False,
            "current_file": "nota.pdf",
            "processed_files": 0,
            "total_files": 1,
            "result": None,
            "error": None,
        }

    response = client.post(f"/api/process/cancel/{job_id}")

    # O endpoint de cancelamento deve confirmar a transição imediatamente
    assert response.status_code == 200
    payload = response.json()
    # O job deve estar em estado de 'cancelling' (aguardando a thread finalizar)
    assert payload["status"] == "cancelling"

    # Consultar o status via GET deve retornar o mesmo estado persistido
    status_response = client.get(f"/api/process/status/{job_id}")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    # O estado deve ser consistente entre POST /cancel e GET /status
    assert status_payload["status"] == "cancelling"


def test_cancel_process_job_returns_final_state_when_already_done(client):
    """
    Verifica que tentar cancelar um job já finalizado não altera seu estado.

    Quando o job já chegou ao estado 'completed', o endpoint de cancelamento
    deve devolver o estado atual sem modificá-lo — não faz sentido sinalizar
    cancelamento para uma operação que já terminou.
    """
    job_id = "job_done_test"
    with webapp_module._JOBS_LOCK:
        webapp_module._PROCESS_JOBS[job_id] = {
            "job_id": job_id,
            "status": "completed",
            "message": "Processamento concluído.",
            "cancel_requested": False,
            "current_file": "",
            "processed_files": 1,
            "total_files": 1,
            "result": {"records_extracted": 1},
            "error": None,
        }

    response = client.post(f"/api/process/cancel/{job_id}")

    assert response.status_code == 200
    payload = response.json()
    # O estado deve permanecer 'completed', ignorando o pedido de cancelamento tardio
    assert payload["status"] == "completed"


def test_process_image_endpoint_rejects_non_image(client):
    """
    Garante que o endpoint /api/process-image recusa arquivos que não são imagens.

    Enviar um PDF (ou qualquer outro tipo não-imagem) deve resultar em HTTP 400,
    protegendo o pipeline de OCR contra entradas inválidas e fornecendo ao
    usuário uma mensagem de erro clara sobre o tipo de arquivo esperado.
    """
    response = client.post(
        "/api/process-image",
        files={"file": ("nota.pdf", b"dummy pdf", "application/pdf")},
    )

    # Arquivo não-imagem deve ser rejeitado com Bad Request
    assert response.status_code == 400
    # A mensagem de erro deve mencionar "imagem" para orientar o usuário
    assert "imagem" in response.json()["detail"].lower()


def test_process_image_endpoint_returns_sheets_payload(client, monkeypatch):
    """
    Verifica o contrato básico da resposta de /api/process-image.

    Usa um OCR fake que retorna uma linha simples de dividendo (formato de linha única)
    e confirma que a resposta JSON contém todos os campos esperados pelo frontend:
    contagem de registros, lista de colunas, linhas de pré-visualização e o texto
    formatado em TSV para colar no Google Sheets.

    O monkeypatch substitui ocrmac.OCR para que o teste rode sem OCR real (macOS Vision).
    """
    image = Image.new("RGB", (60, 40), "white")
    buffer = webapp_module.BytesIO()
    image.save(buffer, format="PNG")

    fake_results = [
        ("15/05/2026", 0.99, (0, 0, 1, 1)),
        ("DIVIDENDO VALE3 100 R$ 34,56", 0.99, (0, 0, 1, 1)),
    ]

    class FakeOCR:
        def __init__(self, *_args, **_kwargs):
            pass

        def recognize(self, *_args, **_kwargs):
            return fake_results

    monkeypatch.setattr(webapp_module._ocrmac, "OCR", FakeOCR)

    response = client.post(
        "/api/process-image",
        files={"file": ("extrato.png", buffer.getvalue(), "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    # O parser deve identificar exatamente 1 registro de dividendo na imagem
    assert payload["records_extracted"] == 1
    # As colunas devem seguir o schema fixo esperado pelo Google Sheets
    assert payload["columns"] == ["Data", "Ticker", "Tipo", "Quantidade", "Valor Recebido"]
    # O tipo deve ser classificado como "D" (Dividendo) automaticamente
    assert payload["preview_rows"][0]["Tipo"] == "D"
    # O texto para colar no Sheets deve usar tabulação como separador de colunas
    assert "\t" in payload["sheets_text"]


def test_process_image_multiline_ocr(client, monkeypatch):
    """
    Verifica o parsing de um extrato com múltiplos registros em datas diferentes,
    descrições que quebram em várias linhas OCR e quantidades com vírgula (ex: 2,575).

    Cenário simulado:
    - 12/06/2026: KNCR11 — R$ 286,00, quantidade 260
    - 08/06/2026: RZTR11 — R$ 230,00, quantidade 230
    - 08/06/2026: PORD11 — R$ 252,35, quantidade 2,575 (deve virar "2575")

    A linha "Saldo do dia: R$ 1.228,54" deve ser ignorada pelo parser pois não
    corresponde ao padrão de registro de dividendo.

    Como o resultado é ordenado por data (mais antigo primeiro), a ordem esperada
    na resposta é: RZTR11 (08/06) → PORD11 (08/06) → KNCR11 (12/06).
    """
    image = Image.new("RGB", (60, 40), "white")
    buffer = webapp_module.BytesIO()
    image.save(buffer, format="PNG")

    fake_results = [
        ("12/06/2026", 0.99, (0, 0, 1, 1)),
        ("Saldo do dia: R$ 1.228,54", 0.99, (0, 0, 1, 1)),
        ("RENDIMENTOS DE", 0.99, (0, 0, 1, 1)),
        ("CLIENTES KNCR11 S/", 0.99, (0, 0, 1, 1)),
        ("R$ 286,00", 0.99, (0, 0, 1, 1)),
        ("260", 0.99, (0, 0, 1, 1)),
        ("08/06/2026", 0.99, (0, 0, 1, 1)),
        ("RENDIMENTOS DE CLIENTES", 0.99, (0, 0, 1, 1)),
        ("RZTR11 S/", 0.99, (0, 0, 1, 1)),
        ("R$ 230,00", 0.99, (0, 0, 1, 1)),
        ("230", 0.99, (0, 0, 1, 1)),
        ("RENDIMENTOS DE CLIENTES PORD11 S/", 0.99, (0, 0, 1, 1)),
        ("R$ 252,35", 0.99, (0, 0, 1, 1)),
        ("2,575", 0.99, (0, 0, 1, 1)),
    ]

    class FakeOCR:
        def __init__(self, *_args, **_kwargs):
            pass

        def recognize(self, *_args, **_kwargs):
            return fake_results

    monkeypatch.setattr(webapp_module._ocrmac, "OCR", FakeOCR)

    response = client.post(
        "/api/process-image",
        files={"file": ("extrato.png", buffer.getvalue(), "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    # O parser deve ignorar o "Saldo do dia" e extrair os 3 registros de dividendo
    assert payload["records_extracted"] == 3

    rows = payload["preview_rows"]

    # Primeiro registro após ordenação por data: RZTR11 em 08/06/2026
    assert rows[0]["Data"] == "08/06/2026"
    assert rows[0]["Ticker"] == "RZTR11"
    assert rows[0]["Quantidade"] == "230"
    assert rows[0]["Valor Recebido"] == "230,00"

    # Segundo registro: PORD11 também em 08/06/2026 (mesma data, segue RZTR11)
    assert rows[1]["Data"] == "08/06/2026"
    assert rows[1]["Ticker"] == "PORD11"
    # Quantidade "2,575" deve ter a vírgula removida → "2575"
    assert rows[1]["Quantidade"] == "2575"
    assert rows[1]["Valor Recebido"] == "252,35"

    # Terceiro registro: KNCR11 em 12/06/2026 (data mais recente, aparece por último)
    assert rows[2]["Data"] == "12/06/2026"
    assert rows[2]["Ticker"] == "KNCR11"
    assert rows[2]["Quantidade"] == "260"
    assert rows[2]["Valor Recebido"] == "286,00"


def test_build_sheets_payload_sorts_by_date():
    """
    Verifica que _build_sheets_payload ordena os registros por data antes de gerar
    o payload para o Google Sheets, independentemente da ordem do DataFrame de entrada.

    O DataFrame de entrada propositalmente tem as datas fora de ordem (15, 08, 12)
    para confirmar que a ordenação cronológica é aplicada pela função, e não apenas
    herdada da ordem de extração do OCR.

    Testa tanto preview_rows (usado na tabela do frontend) quanto sheets_text (TSV
    copiado pelo usuário), para garantir que ambas as saídas são consistentes.
    """
    df = pd.DataFrame(
        {
            "Data": ["15/06/2026", "08/06/2026", "12/06/2026"],
            "Ticker": ["VALE3", "PSSA3", "ITSA4"],
            "Tipo": ["D", "D", "D"],
            "Quantidade": ["100", "200", "150"],
            "Valor Recebido": ["50,00", "30,00", "45,00"],
        }
    )
    payload = webapp_module._build_sheets_payload(df)
    rows = payload["preview_rows"]

    # A data mais antiga deve aparecer primeiro nas linhas de pré-visualização
    assert rows[0]["Data"] == "08/06/2026"
    assert rows[1]["Data"] == "12/06/2026"
    assert rows[2]["Data"] == "15/06/2026"

    lines = payload["sheets_text"].split("\n")
    # A primeira linha de dados no TSV (após o cabeçalho, índice 1) também deve
    # começar com a data mais antiga, garantindo consistência entre preview e TSV
    assert lines[1].startswith("08/06/2026")


def test_process_image_bbox_sorting_fixes_column_ordering(client, monkeypatch):
    """
    Reproduz o bug de layout multi-coluna do OCR nativo do macOS (Vision framework)
    e verifica que o sort por bounding box o corrige.

    Contexto do bug:
    O Vision framework pode retornar os tokens de colunas diferentes fora de ordem
    visual: primeiro todas as descrições (coluna esquerda), depois todos os valores
    R$ (coluna direita). Sem ordenação, o parser de janela deslizante associava o
    R$ do primeiro item ao segundo item — extraindo valores errados.

    Solução testada:
    Antes do parsing, os tokens são ordenados por posição na tela usando o bounding
    box [x, y, w, h] (coordenadas normalizadas, origem no canto inferior esquerdo
    da imagem). A chave de ordenação é (-(y+h), x), que coloca tokens mais altos
    na tela primeiro e, dentro da mesma linha, da esquerda para a direita.

    Cenário fake:
    - KNCR11: descrição em y=0.80..0.86, R$ 286,00 em y=0.80..0.86 (mesma altura)
    - RZTR11: descrição em y=0.65..0.71, R$ 230,00 em y=0.65..0.71 (mesma altura)
    - O OCR retorna as linhas de R$ DEPOIS de todas as descrições (bug simulado)
    - Após o sort por bbox, a ordem visual correta é restaurada

    Sem o sort: KNCR11 poderia receber R$ 230,00 (valor errado)
    Com o sort:  cada ticker recebe o valor correto da sua linha
    """
    image = Image.new("RGB", (60, 40), "white")
    buffer = webapp_module.BytesIO()
    image.save(buffer, format="PNG")

    fake_results = [
        ("12/06/2026", 0.99, [0.05, 0.94, 0.40, 0.04]),
        ("RENDIMENTOS DE CLIENTES KNCR11 S/", 0.99, [0.10, 0.80, 0.55, 0.06]),
        ("260", 0.99, [0.10, 0.74, 0.10, 0.04]),
        ("RENDIMENTOS DE CLIENTES RZTR11 S/", 0.99, [0.10, 0.65, 0.55, 0.06]),
        ("230", 0.99, [0.10, 0.59, 0.10, 0.04]),
        # R$ aparecem DEPOIS de todas as descrições na saída do Vision (bug original)
        ("R$ 286,00", 0.99, [0.75, 0.80, 0.20, 0.06]),
        ("R$ 230,00", 0.99, [0.75, 0.65, 0.20, 0.06]),
    ]

    class FakeOCR:
        def __init__(self, *_args, **_kwargs):
            pass

        def recognize(self, *_args, **_kwargs):
            return fake_results

    monkeypatch.setattr(webapp_module._ocrmac, "OCR", FakeOCR)

    response = client.post(
        "/api/process-image",
        files={"file": ("extrato.png", buffer.getvalue(), "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    # Ambos os registros devem ser extraídos (o bug os misturava ou descartava)
    assert payload["records_extracted"] == 2

    rows = payload["preview_rows"]

    # KNCR11 deve receber exatamente o valor e quantidade da sua linha (R$ 286,00 / 260)
    kncr = next(r for r in rows if r["Ticker"] == "KNCR11")
    assert kncr["Valor Recebido"] == "286,00"
    assert kncr["Quantidade"] == "260"

    # RZTR11 deve receber exatamente o valor e quantidade da sua linha (R$ 230,00 / 230)
    rztr = next(r for r in rows if r["Ticker"] == "RZTR11")
    assert rztr["Valor Recebido"] == "230,00"


def test_process_image_hoje_uses_today_date(client, monkeypatch):
    from datetime import datetime as _dt

    image = Image.new("RGB", (60, 40), "white")
    buffer = webapp_module.BytesIO()
    image.save(buffer, format="PNG")

    fake_results = [
        ("Hoje", 0.99, [0.05, 0.90, 0.20, 0.05]),
        ("RENDIMENTOS DE CLIENTES TVRI11 S/", 0.99, [0.10, 0.70, 0.55, 0.06]),
        ("R$ 257,25", 0.99, [0.75, 0.70, 0.20, 0.06]),
        ("245", 0.99, [0.10, 0.63, 0.10, 0.04]),
    ]

    class FakeOCR:
        def __init__(self, *_args, **_kwargs):
            pass

        def recognize(self, *_args, **_kwargs):
            return fake_results

    monkeypatch.setattr(webapp_module._ocrmac, "OCR", FakeOCR)

    response = client.post(
        "/api/process-image",
        files={"file": ("extrato.png", buffer.getvalue(), "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["records_extracted"] == 1

    today = _dt.now().strftime("%d/%m/%Y")
    assert payload["preview_rows"][0]["Data"] == today
    assert payload["preview_rows"][0]["Ticker"] == "TVRI11"
    assert payload["preview_rows"][0]["Valor Recebido"] == "257,25"