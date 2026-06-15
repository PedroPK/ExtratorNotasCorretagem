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
    response = client.get("/")

    assert response.status_code == 200
    assert "drag and drop" in response.text.lower()
    assert "Encerrar aplicação" in response.text


def test_shutdown_endpoint_is_forbidden_when_not_enabled(client):
    response = client.post("/api/system/shutdown")

    assert response.status_code == 403
    assert "Encerramento remoto" in response.json()["detail"]


def test_process_endpoint_returns_preview_and_download(client):
    response = client.post(
        "/api/process",
        files={"files": ("nota.pdf", b"dummy pdf", "application/pdf")},
        data={"sort_by": "name", "output_format": "csv"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["records_extracted"] == 2
    assert payload["files_received"] == 1
    assert payload["download_url"] == "/api/download/dados_extraidos_20260513_120000.csv"
    assert len(payload["preview_rows"]) == 2


def test_download_endpoint_serves_exported_file(client):
    client.post(
        "/api/process",
        files={"files": ("nota.pdf", b"dummy pdf", "application/pdf")},
        data={"sort_by": "name", "output_format": "csv"},
    )

    response = client.get("/api/download/dados_extraidos_20260513_120000.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")


def test_cancel_process_job_sets_cancelling_state(client):
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

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "cancelling"

    status_response = client.get(f"/api/process/status/{job_id}")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["status"] == "cancelling"


def test_cancel_process_job_returns_final_state_when_already_done(client):
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
    assert payload["status"] == "completed"


def test_process_image_endpoint_rejects_non_image(client):
    response = client.post(
        "/api/process-image",
        files={"file": ("nota.pdf", b"dummy pdf", "application/pdf")},
    )

    assert response.status_code == 400
    assert "imagem" in response.json()["detail"].lower()


def test_process_image_endpoint_returns_sheets_payload(client, monkeypatch):
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
    assert payload["records_extracted"] == 1
    assert payload["columns"] == ["Data", "Ticker", "Tipo", "Quantidade", "Valor Recebido"]
    assert payload["preview_rows"][0]["Tipo"] == "D"
    assert "\t" in payload["sheets_text"]


def test_process_image_multiline_ocr(client, monkeypatch):
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
    assert payload["records_extracted"] == 3

    rows = payload["preview_rows"]
    assert rows[0]["Data"] == "12/06/2026"
    assert rows[0]["Ticker"] == "KNCR11"
    assert rows[0]["Quantidade"] == "260"
    assert rows[0]["Valor Recebido"] == "286,00"

    assert rows[1]["Data"] == "08/06/2026"
    assert rows[1]["Ticker"] == "RZTR11"
    assert rows[1]["Quantidade"] == "230"
    assert rows[1]["Valor Recebido"] == "230,00"

    assert rows[2]["Ticker"] == "PORD11"
    assert rows[2]["Quantidade"] == "2575"
    assert rows[2]["Valor Recebido"] == "252,35"