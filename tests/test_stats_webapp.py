import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import execution_stats as execution_stats_module
import stats_webapp as stats_webapp_module


def test_stats_webapp_serves_history_and_html(tmp_path, monkeypatch):
    stats_dir = tmp_path / "stats"
    stats_dir.mkdir()
    monkeypatch.setattr(execution_stats_module, "STATS_DIR", stats_dir)

    sample_run = {
        "execution_id": "20260514_151010_000003",
        "started_at": "2026-05-14T15:10:10",
        "finished_at": "2026-05-14T15:10:20",
        "status": "completed",
        "totals": {
            "processed_files": 4,
            "failed_files": 0,
            "ignored_files": 0,
            "pages_processed": 12,
            "records_extracted": 32,
            "elapsed_seconds": 18.5,
            "avg_seconds_per_pdf": 4.625,
            "avg_seconds_per_page": 1.5417,
            "avg_seconds_per_record": 0.5781,
            "avg_records_per_pdf": 8.0,
        },
    }
    (stats_dir / "execucao_dashboard.json").write_text(json.dumps(sample_run), encoding="utf-8")

    client = TestClient(stats_webapp_module.app)

    html_response = client.get("/")
    assert html_response.status_code == 200
    assert "Histórico de performance" in html_response.text

    api_response = client.get("/api/history?limit=5")
    assert api_response.status_code == 200
    payload = api_response.json()
    assert payload["summary"]["total_runs"] == 1
    assert payload["runs"][0]["records_extracted"] == 32
    assert payload["runs"][0]["stats_file"] == "execucao_dashboard.json"
