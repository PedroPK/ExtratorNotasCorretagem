#!/usr/bin/env python3
"""Leitura e agregação do histórico de estatísticas por execução."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import get_config


config = get_config()
STATS_DIR = Path(config.resolve_path(config.get_stats_folder()))
STATS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def load_execution_stats_file(stats_path: str | Path) -> Dict[str, Any]:
    path = Path(stats_path)
    with path.open("r", encoding="utf-8") as stats_file:
        payload = json.load(stats_file)
    payload["stats_file"] = path.name
    return payload


def list_execution_history(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    history = []
    for stats_file in sorted(STATS_DIR.glob("execucao_*.json"), reverse=True):
        try:
            history.append(load_execution_stats_file(stats_file))
        except (OSError, json.JSONDecodeError):
            continue

    history.sort(key=lambda item: str(item.get("started_at") or ""), reverse=True)
    if limit is not None:
        return history[:limit]
    return history


def build_history_summary(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_runs = len(history)
    completed_runs = [run for run in history if run.get("status") == "completed"]
    totals_list = [run.get("totals") or {} for run in history]

    total_files = sum(_safe_int(totals.get("processed_files")) for totals in totals_list)
    total_records = sum(_safe_int(totals.get("records_extracted")) for totals in totals_list)
    total_pages = sum(_safe_int(totals.get("pages_processed")) for totals in totals_list)
    total_elapsed = sum(_safe_float(totals.get("elapsed_seconds")) for totals in totals_list)

    return {
        "total_runs": total_runs,
        "completed_runs": len(completed_runs),
        "failed_or_cancelled_runs": total_runs - len(completed_runs),
        "total_files": total_files,
        "total_records": total_records,
        "total_pages": total_pages,
        "avg_elapsed_seconds": round(total_elapsed / total_runs, 4) if total_runs else 0.0,
        "avg_files_per_run": round(total_files / total_runs, 4) if total_runs else 0.0,
        "avg_records_per_run": round(total_records / total_runs, 4) if total_runs else 0.0,
        "avg_seconds_per_pdf": round(
            sum(_safe_float(totals.get("avg_seconds_per_pdf")) for totals in totals_list) / total_runs,
            4,
        ) if total_runs else 0.0,
        "avg_seconds_per_page": round(
            sum(_safe_float(totals.get("avg_seconds_per_page")) for totals in totals_list) / total_runs,
            4,
        ) if total_runs else 0.0,
        "avg_seconds_per_record": round(
            sum(_safe_float(totals.get("avg_seconds_per_record")) for totals in totals_list) / total_runs,
            4,
        ) if total_runs else 0.0,
    }


def build_history_payload(limit: int = 60) -> Dict[str, Any]:
    history = list_execution_history(limit=limit)
    summary = build_history_summary(history)
    runs = []

    for run in history:
        totals = run.get("totals") or {}
        runs.append(
            {
                "execution_id": run.get("execution_id"),
                "started_at": run.get("started_at"),
                "finished_at": run.get("finished_at"),
                "status": run.get("status"),
                "year_filter": run.get("year_filter"),
                "sort_by": run.get("sort_by"),
                "input_path": run.get("input_path"),
                "stats_file": run.get("stats_file"),
                "processed_files": _safe_int(totals.get("processed_files")),
                "failed_files": _safe_int(totals.get("failed_files")),
                "ignored_files": _safe_int(totals.get("ignored_files")),
                "pages_processed": _safe_int(totals.get("pages_processed")),
                "records_extracted": _safe_int(totals.get("records_extracted")),
                "elapsed_seconds": _safe_float(totals.get("elapsed_seconds")),
                "avg_seconds_per_pdf": _safe_float(totals.get("avg_seconds_per_pdf")),
                "avg_seconds_per_page": _safe_float(totals.get("avg_seconds_per_page")),
                "avg_seconds_per_record": _safe_float(totals.get("avg_seconds_per_record")),
                "avg_records_per_pdf": _safe_float(totals.get("avg_records_per_pdf")),
            }
        )

    return {
        "summary": summary,
        "runs": runs,
    }
