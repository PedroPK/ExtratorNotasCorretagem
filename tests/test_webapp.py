import sys
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import webapp as webapp_module


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(webapp_module, "OUTPUT_DIR", tmp_path)

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

    return TestClient(webapp_module.app)


def test_index_returns_html(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Drag and drop" in response.text


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