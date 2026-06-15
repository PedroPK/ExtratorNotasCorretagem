import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import execution_stats as execution_stats_module


def test_build_history_payload_aggregates_runs(tmp_path, monkeypatch):
    stats_dir = tmp_path / "stats"
    stats_dir.mkdir()
    monkeypatch.setattr(execution_stats_module, "STATS_DIR", stats_dir)

    first = {
        "execution_id": "20260514_101010_000001",
        "started_at": "2026-05-14T10:10:10",
        "finished_at": "2026-05-14T10:10:20",
        "status": "completed",
        "totals": {
            "processed_files": 3,
            "failed_files": 0,
            "ignored_files": 1,
            "pages_processed": 9,
            "records_extracted": 21,
            "elapsed_seconds": 10.0,
            "avg_seconds_per_pdf": 3.3333,
            "avg_seconds_per_page": 1.1111,
            "avg_seconds_per_record": 0.4762,
            "avg_records_per_pdf": 7.0,
        },
    }
    second = {
        "execution_id": "20260514_111111_000002",
        "started_at": "2026-05-14T11:11:11",
        "finished_at": "2026-05-14T11:11:41",
        "status": "failed",
        "totals": {
            "processed_files": 2,
            "failed_files": 1,
            "ignored_files": 0,
            "pages_processed": 4,
            "records_extracted": 8,
            "elapsed_seconds": 30.0,
            "avg_seconds_per_pdf": 15.0,
            "avg_seconds_per_page": 7.5,
            "avg_seconds_per_record": 3.75,
            "avg_records_per_pdf": 4.0,
        },
    }

    (stats_dir / "execucao_1.json").write_text(json.dumps(first), encoding="utf-8")
    (stats_dir / "execucao_2.json").write_text(json.dumps(second), encoding="utf-8")

    payload = execution_stats_module.build_history_payload(limit=10)

    assert payload["summary"]["total_runs"] == 2
    assert payload["summary"]["completed_runs"] == 1
    assert payload["summary"]["total_files"] == 5
    assert payload["summary"]["total_records"] == 29
    assert len(payload["runs"]) == 2
    assert payload["runs"][0]["execution_id"] == "20260514_111111_000002"
    assert payload["runs"][0]["stats_file"] == "execucao_2.json"
