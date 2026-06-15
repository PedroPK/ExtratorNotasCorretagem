#!/usr/bin/env python3
"""Aplicação web para upload, processamento e visualização dos resultados."""

from __future__ import annotations

import mimetypes
import os
import re
import signal
import shutil
import tempfile
import threading
import time
import uuid
import webbrowser
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional


import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from PIL import Image
from ocrmac import ocrmac as _ocrmac

from config import get_config
from extratorNotasCorretagem import (
    _filter_dataframe_by_ticker,
    analisar_pasta_ou_zip,
    exportar_dados,
    ordenar_dados_por_data,
)

app = FastAPI(
    title="Extrator Notas Corretagem",
    description="Frontend web para upload de PDFs/ZIPs, processamento e download dos resultados.",
)

config = get_config()
OUTPUT_DIR = Path(config.resolve_path(config.get_output_folder()))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

_JOBS_LOCK = threading.Lock()
_PROCESS_JOBS: Dict[str, Dict[str, Any]] = {}

# Segurança: endpoint de desligamento só fica disponível quando o app é iniciado via CLI.
app.state.allow_shutdown = False


def _schedule_browser_open(url: str, delay_seconds: float = 1.0) -> None:
  """Agenda abertura do navegador sem bloquear a subida do servidor."""

  def _open() -> None:
    try:
      webbrowser.open(url, new=2, autoraise=True)
    except Exception as exc:  # pragma: no cover - comportamento depende do SO/ambiente.
      print(f"Aviso: não foi possível abrir o navegador automaticamente ({exc}).")

  timer = threading.Timer(max(delay_seconds, 0.0), _open)
  timer.daemon = True
  timer.start()


def _schedule_server_shutdown(delay_seconds: float = 0.8) -> None:
  """Agenda o desligamento do processo atual para permitir resposta HTTP antes do encerramento."""

  def _shutdown() -> None:
    os.kill(os.getpid(), signal.SIGTERM)

  timer = threading.Timer(max(delay_seconds, 0.0), _shutdown)
  timer.daemon = True
  timer.start()


def _normalize_date(date_text: str) -> str:
  raw = (date_text or "").strip()
  if not raw:
    return ""

  for date_format in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y"):
    try:
      return datetime.strptime(raw, date_format).strftime("%d/%m/%Y")
    except ValueError:
      continue

  matches = re.search(r"(\d{2})[\/-](\d{2})[\/-](\d{2,4})", raw)
  if not matches:
    return raw

  day, month, year = matches.groups()
  if len(year) == 2:
    year = f"20{year}"
  return f"{day}/{month}/{year}"


def _normalize_qty(qty_text: str) -> str:
  digits_only = re.sub(r"[^0-9]", "", (qty_text or "").strip())
  if not digits_only:
    return ""
  return str(int(digits_only))


def _normalize_number(value_text: str, decimal_places: int) -> str:
  cleaned = re.sub(r"[^0-9,.-]", "", (value_text or "").strip())
  if not cleaned:
    return ""

  if "," in cleaned and "." in cleaned:
    if cleaned.rfind(",") > cleaned.rfind("."):
      cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
      cleaned = cleaned.replace(",", "")
  else:
    cleaned = cleaned.replace(",", ".")

  try:
    numeric = float(cleaned)
  except ValueError:
    return ""
  return f"{numeric:.{decimal_places}f}"


def _extract_dividend_rows_from_ocr_text(ocr_text: str, fallback_date: str) -> pd.DataFrame:
  lines = [line.strip() for line in (ocr_text or "").splitlines() if line.strip()]
  records: List[Dict[str, Any]] = []

  ticker_pattern = re.compile(r"\b([A-Z]{4}\d{1,2})\b")
  date_pattern = re.compile(r"(\d{2}[\/-]\d{2}[\/-]\d{2,4})")
  value_pattern = re.compile(r"R\$\s*([\d.,]+)", re.IGNORECASE)
  s_qty_pattern = re.compile(r"S/\s*(\d[\d.,]*)", re.IGNORECASE)
  before_r_pattern = re.compile(r"([\d.,]+)\s+R\$", re.IGNORECASE)

  today_pattern = re.compile(r"^hoje$", re.IGNORECASE)

  active_date = _normalize_date(fallback_date)
  if not active_date:
    for line in lines:
      if today_pattern.match(line):
        active_date = datetime.now().strftime("%d/%m/%Y")
        break
      date_match = date_pattern.search(line)
      if date_match:
        active_date = _normalize_date(date_match.group(1))
        break

  i = 0
  while i < len(lines):
    line = lines[i]

    if today_pattern.match(line):
      active_date = datetime.now().strftime("%d/%m/%Y")
    else:
      date_match = date_pattern.search(line)
      if date_match:
        active_date = _normalize_date(date_match.group(1))

    if any(word in line.upper() for word in ("DIVID", "REND", "JCP")):
      window = [line]
      j = i + 1
      while j < len(lines) and len(window) < 6:
        next_line = lines[j]
        if date_pattern.search(next_line) or today_pattern.match(next_line):
          break
        if any(word in next_line.upper() for word in ("DIVID", "REND", "JCP")):
          break
        window.append(next_line)
        j += 1

      window_text = " ".join(window)

      ticker_match = ticker_pattern.search(window_text)
      value_match = value_pattern.search(window_text)

      if ticker_match and value_match:
        ticker = ticker_match.group(1).upper()
        value_text = _normalize_number(value_match.group(1), 2).replace(".", ",")

        qty_text = ""

        s_qty_match = s_qty_pattern.search(window_text)
        if s_qty_match:
          qty_text = _normalize_qty(s_qty_match.group(1))

        if not qty_text:
          before_r_match = before_r_pattern.search(window_text)
          if before_r_match:
            qty_text = _normalize_qty(before_r_match.group(1))

        if not qty_text:
          for wline in window:
            if re.match(r"^[\d.,]+$", wline) and "R$" not in wline.upper():
              qty_text = _normalize_qty(wline)
              break

        if qty_text and value_text:
          records.append(
            {
              "Data": active_date or "",
              "Ticker": ticker,
              "Tipo": "D",
              "Quantidade": qty_text,
              "Valor Recebido": value_text,
            }
          )

    i += 1

  if not records:
    return pd.DataFrame(columns=["Data", "Ticker", "Tipo", "Quantidade", "Valor Recebido"])

  df = pd.DataFrame(records)
  return df[["Data", "Ticker", "Tipo", "Quantidade", "Valor Recebido"]]


def _build_sheets_payload(df: pd.DataFrame) -> Dict[str, Any]:
  sheets_columns = ["Data", "Ticker", "Tipo", "Quantidade", "Valor Recebido"]
  safe_df = df.copy() if not df.empty else pd.DataFrame(columns=sheets_columns)
  for column in sheets_columns:
    if column not in safe_df.columns:
      safe_df[column] = ""
  safe_df = safe_df[sheets_columns]

  if not safe_df.empty and "Data" in safe_df.columns:
    try:
      safe_df = safe_df.copy()
      safe_df["_data_dt"] = pd.to_datetime(safe_df["Data"], format="%d/%m/%Y", errors="coerce")
      safe_df = safe_df.sort_values("_data_dt", ascending=True).drop(columns=["_data_dt"])
      safe_df = safe_df.reset_index(drop=True)
    except Exception:
      pass

  preview_rows = safe_df.to_dict(orient="records")
  sheets_lines = ["\t".join(sheets_columns)]
  for row in preview_rows:
    sheets_lines.append("\t".join(str(row.get(column, "")) for column in sheets_columns))

  return {
    "message": f"Processamento concluído com {len(preview_rows)} registro(s).",
    "records_extracted": len(preview_rows),
    "files_received": 1,
    "export_format": "sheets",
    "columns": sheets_columns,
    "preview_rows": preview_rows,
    "filename": None,
    "download_url": None,
    "sheets_text": "\n".join(sheets_lines),
  }


def _build_e2e_demo_image_payload() -> Dict[str, Any]:
  df = pd.DataFrame(
    {
      "Data": ["10/05/2026", "10/05/2026", "11/05/2026"],
      "Ticker": ["VALE3", "ITSA4", "PSSA3"],
      "Tipo": ["D", "D", "D"],
      "Quantidade": ["10", "12", "30"],
      "Valor Recebido": ["58,42", "11,90", "28,33"],
    }
  )
  return _build_sheets_payload(df)


def _process_image_content(image_bytes: bytes, payment_date: Optional[str]) -> Dict[str, Any]:
  try:
    image = Image.open(BytesIO(image_bytes))
  except Exception as exc:
    raise HTTPException(status_code=400, detail=f"Imagem inválida: {exc}") from exc

  try:
    results = _ocrmac.OCR(
      image,
      language_preference=["pt-BR"],
      recognition_level="accurate",
    ).recognize()
    try:
      results = sorted(results, key=lambda r: (-(r[2][1] + r[2][3]), r[2][0]))
    except Exception:
      pass
    ocr_text = "\n".join(text for text, _conf, _bbox in results)
  except Exception as exc:
    raise HTTPException(status_code=500, detail=f"Falha no OCR da imagem: {exc}") from exc

  df = _extract_dividend_rows_from_ocr_text(ocr_text, payment_date or "")
  return _build_sheets_payload(df)


HTML_PAGE = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Extrator de Dividendos por Imagem</title>
  <style>
    :root {
      --bg: #07111f;
      --bg-2: #0d1b2a;
      --panel: rgba(15, 28, 44, 0.78);
      --panel-strong: #13263b;
      --line: rgba(255, 255, 255, 0.10);
      --text: #edf5ff;
      --muted: #9db0c6;
      --accent: #7dd3fc;
      --accent-2: #34d399;
      --warn: #fbbf24;
      --shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
      --radius: 24px;
    }

    * { box-sizing: border-box; }
    html, body { min-height: 100%; }
    body {
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(125, 211, 252, 0.20), transparent 34%),
        radial-gradient(circle at 80% 20%, rgba(52, 211, 153, 0.16), transparent 28%),
        linear-gradient(180deg, var(--bg) 0%, var(--bg-2) 100%);
      color: var(--text);
    }

    .shell {
      max-width: 1280px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }

    .hero {
      display: grid;
      grid-template-columns: 1.4fr 0.9fr;
      gap: 20px;
      align-items: stretch;
    }

    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
    }

    .hero-copy { padding: 32px; }
    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(125, 211, 252, 0.12);
      border: 1px solid rgba(125, 211, 252, 0.22);
      color: var(--accent);
      font-size: 0.82rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    h1 {
      margin: 18px 0 12px;
      font-size: clamp(2.4rem, 5vw, 4.4rem);
      line-height: 0.95;
      letter-spacing: -0.04em;
    }

    .lede {
      margin: 0;
      max-width: 60ch;
      color: var(--muted);
      font-size: 1.05rem;
      line-height: 1.7;
    }

    .hero-stats {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-top: 28px;
    }

    .stat {
      padding: 16px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .stat strong {
      display: block;
      font-size: 1.35rem;
      margin-bottom: 6px;
    }

    .stat span { color: var(--muted); font-size: 0.9rem; }

    .status-panel { padding: 24px; display: grid; gap: 14px; }
    .status-title {
      display: flex; align-items: center; justify-content: space-between; gap: 12px;
      margin: 0;
      font-size: 1rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em;
    }

    .status-box {
      min-height: 220px;
      padding: 20px;
      border-radius: 20px;
      background: linear-gradient(180deg, rgba(9, 17, 30, 0.95), rgba(15, 28, 44, 0.90));
      border: 1px solid rgba(255, 255, 255, 0.08);
      display: grid;
      align-content: start;
      gap: 14px;
    }

    .progress-wrap {
      display: grid;
      gap: 8px;
      margin-top: 2px;
    }

    .progress-meta {
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: var(--muted);
      font-size: 0.88rem;
    }

    .progress-time {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      color: #c7d7ea;
      font-size: 0.82rem;
    }

    .progress-track {
      width: 100%;
      height: 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.12);
      overflow: hidden;
    }

    .progress-bar {
      width: 0%;
      height: 100%;
      background: linear-gradient(90deg, #38bdf8 0%, #34d399 100%);
      transition: width 240ms ease;
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      border-radius: 999px;
      background: rgba(52, 211, 153, 0.12);
      color: #9ef0cc;
      border: 1px solid rgba(52, 211, 153, 0.25);
      width: fit-content;
    }

    .pulse {
      width: 9px; height: 9px; border-radius: 50%; background: var(--accent-2);
      box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.65);
      animation: pulse 1.6s infinite;
    }

    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.55); }
      70% { box-shadow: 0 0 0 14px rgba(52, 211, 153, 0); }
      100% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
    }

    .controls {
      margin-top: 20px;
      display: grid;
      grid-template-columns: 1fr 1fr 1fr 1fr auto;
      gap: 12px;
      align-items: end;
    }

    .process-actions {
      display: grid;
      gap: 10px;
      align-self: end;
    }

    label { display: block; font-size: 0.84rem; color: var(--muted); margin-bottom: 8px; }
    input, select, button {
      width: 100%;
      padding: 14px 16px;
      border-radius: 14px;
      border: 1px solid rgba(255, 255, 255, 0.10);
      background: rgba(7, 17, 31, 0.72);
      color: var(--text);
      font: inherit;
    }

    input::placeholder { color: #7890a8; }
    input:focus, select:focus, button:focus { outline: 2px solid rgba(125, 211, 252, 0.34); outline-offset: 2px; }

    .dropzone {
      position: relative;
      padding: 28px;
      margin-top: 18px;
      border-radius: 24px;
      border: 1.5px dashed rgba(125, 211, 252, 0.30);
      background: linear-gradient(180deg, rgba(16, 29, 46, 0.72), rgba(10, 19, 32, 0.92));
      transition: 180ms ease;
    }

    .dropzone.dragover {
      border-color: rgba(125, 211, 252, 0.70);
      transform: translateY(-2px);
      background: linear-gradient(180deg, rgba(18, 37, 56, 0.90), rgba(10, 19, 32, 0.95));
    }

    .dropzone strong { display: block; font-size: 1.25rem; margin-bottom: 8px; }
    .dropzone p { margin: 0; color: var(--muted); line-height: 1.6; }
    .file-count { margin-top: 14px; color: var(--accent); font-size: 0.92rem; }
    .file-input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }

    .actions {
      display: flex;
      gap: 12px;
      margin-top: 20px;
      flex-wrap: wrap;
    }

    .primary, .secondary, .danger {
      width: auto;
      padding-inline: 20px;
      font-weight: 700;
      cursor: pointer;
      transition: transform 150ms ease, box-shadow 150ms ease, background 150ms ease;
    }

    .primary {
      border: 0;
      background: linear-gradient(135deg, #38bdf8 0%, #34d399 100%);
      color: #03121d;
      box-shadow: 0 14px 32px rgba(56, 189, 248, 0.22);
    }

    .secondary {
      background: rgba(255, 255, 255, 0.03);
    }

    .danger {
      border: 1px solid rgba(248, 113, 113, 0.55);
      background: linear-gradient(135deg, rgba(220, 38, 38, 0.92) 0%, rgba(185, 28, 28, 0.92) 100%);
      color: #ffe9e9;
      box-shadow: 0 12px 26px rgba(185, 28, 28, 0.30);
    }

    .primary:hover, .secondary:hover, .danger:hover { transform: translateY(-1px); }
    .primary:disabled, .secondary:disabled, .danger:disabled { cursor: not-allowed; opacity: 0.55; transform: none; }

    .results {
      margin-top: 22px;
      display: grid;
      gap: 18px;
    }

    .results-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }

    .result-card {
      padding: 18px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .result-card span { display: block; color: var(--muted); font-size: 0.84rem; margin-bottom: 8px; }
    .result-card strong { font-size: 1.35rem; }

    .table-wrap {
      overflow: auto;
      border-radius: 20px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(5, 12, 22, 0.86);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 780px;
    }

    thead th {
      position: sticky; top: 0;
      background: rgba(13, 24, 39, 0.96);
      color: #cfe7ff;
      text-align: left;
      font-size: 0.83rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      padding: 14px 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }

    tbody td {
      padding: 13px 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      color: #e8f2ff;
      vertical-align: top;
    }

    tbody tr:hover { background: rgba(125, 211, 252, 0.05); }

    .message {
      padding: 14px 16px;
      border-radius: 16px;
      background: rgba(251, 191, 36, 0.10);
      color: #ffe8ac;
      border: 1px solid rgba(251, 191, 36, 0.20);
      white-space: pre-wrap;
    }

    .error {
      background: rgba(248, 113, 113, 0.12);
      color: #ffd1d1;
      border-color: rgba(248, 113, 113, 0.25);
    }

    .hidden { display: none; }

    @media (max-width: 1080px) {
      .hero, .controls, .results-grid { grid-template-columns: 1fr; }
      .progress-time { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="card hero-copy">
        <div class="eyebrow">Imagem do extrato de dividendos</div>
        <h1>Extrator de Dividendos</h1>
        <p class="lede">
          Selecione, arraste ou cole uma imagem do extrato da conta de investimentos para extrair
          Data, Ticker, Tipo da Operação, Quantidade de Cotas e Valor Recebido em formato pronto
          para colar no Google Sheets.
        </p>

        <div class="hero-stats">
          <div class="stat"><strong>Imagem</strong><span>Upload, drag and drop ou Ctrl/Cmd+V</span></div>
          <div class="stat"><strong>Preview</strong><span>Linhas extraídas para conferência</span></div>
          <div class="stat"><strong>Copiar</strong><span>Texto tabulado para Google Sheets</span></div>
        </div>
      </div>

      <aside class="card status-panel">
        <p class="status-title"><span>Processamento</span><span id="queue-state">Pronto</span></p>
        <div class="status-box">
          <div class="status-pill"><span class="pulse"></span><span id="status-label">Aguardando imagem</span></div>
          <div id="progress-wrap" class="progress-wrap hidden">
            <div class="progress-meta">
              <span id="progress-count">0 / 0 arquivos</span>
              <span id="progress-percent">0%</span>
            </div>
            <div class="progress-track">
              <div id="progress-bar" class="progress-bar"></div>
            </div>
            <div class="progress-time">
              <span id="progress-elapsed">Tempo decorrido: 00:00</span>
              <span id="progress-eta">Tempo restante estimado: --:--</span>
            </div>
          </div>
          <div id="status-message" class="message">Selecione ou cole uma imagem e clique em processar.</div>
          <div id="download-slot" class="hidden"></div>
        </div>
      </aside>
    </section>

    <section class="card" style="margin-top: 20px; padding: 24px;">
      <form id="upload-form">
        <div id="dropzone" class="dropzone">
          <strong>Solte aqui uma imagem do extrato</strong>
          <p>Você também pode clicar para escolher uma imagem ou colar com Ctrl/Cmd+V.</p>
          <div id="file-count" class="file-count">Nenhuma imagem selecionada.</div>
          <input class="file-input" id="files" name="files" type="file" accept="image/*" />
        </div>

        <div class="controls">
          <div>
            <label for="payment-date">Data de recebimento (opcional)</label>
            <input id="payment-date" name="payment_date" type="text" placeholder="Ex.: 15/05/2026" />
          </div>
          <div class="process-actions">
            <button id="process-button" class="primary" type="submit">Processar imagem</button>
          </div>
        </div>

        <div class="actions">
          <button id="clear-button" class="secondary" type="button">Limpar seleção</button>
          <button id="copy-button" class="primary" type="button">Copiar para Google Sheets</button>
          <button id="scroll-button" class="secondary" type="button">Ver preview</button>
          <button id="shutdown-button" class="danger" type="button">Encerrar aplicação</button>
        </div>
      </form>
    </section>

    <section id="results" class="results hidden">
      <div class="results-grid">
        <div class="result-card"><span>Registros extraídos</span><strong id="metric-records">0</strong></div>
        <div class="result-card"><span>Imagem enviada</span><strong id="metric-files">0</strong></div>
        <div class="result-card"><span>Formato exportado</span><strong id="metric-format">-</strong></div>
        <div class="result-card"><span>Arquivo gerado</span><strong id="metric-file">-</strong></div>
      </div>

      <div class="card" style="padding: 18px;">
        <div id="table-message" class="message hidden"></div>
        <div id="sheets-block" class="message hidden"></div>
        <div class="table-wrap">
          <table id="preview-table">
            <thead></thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </section>
  </main>

  <script>
    const form = document.getElementById('upload-form');
    const fileInput = document.getElementById('files');
    const dropzone = document.getElementById('dropzone');
    const fileCount = document.getElementById('file-count');
    const statusLabel = document.getElementById('status-label');
    const statusMessage = document.getElementById('status-message');
    const queueState = document.getElementById('queue-state');
    const processButton = document.getElementById('process-button');
    const clearButton = document.getElementById('clear-button');
    const scrollButton = document.getElementById('scroll-button');
    const copyButton = document.getElementById('copy-button');
    const shutdownButton = document.getElementById('shutdown-button');
    const results = document.getElementById('results');
    const downloadSlot = document.getElementById('download-slot');
    const tableMessage = document.getElementById('table-message');
    const sheetsBlock = document.getElementById('sheets-block');
    const previewTable = document.getElementById('preview-table');
    const previewHead = previewTable.querySelector('thead');
    const previewBody = previewTable.querySelector('tbody');
    const progressWrap = document.getElementById('progress-wrap');
    const progressCount = document.getElementById('progress-count');
    const progressPercent = document.getElementById('progress-percent');
    const progressBar = document.getElementById('progress-bar');
    const progressElapsed = document.getElementById('progress-elapsed');
    const progressEta = document.getElementById('progress-eta');
    let activeJobId = null;
    let processingStartMs = null;
    let elapsedTimerId = null;
    let lastProgressSnapshot = { processed: 0, total: 0 };
    let lastSheetsText = '';

    const metrics = {
      records: document.getElementById('metric-records'),
      files: document.getElementById('metric-files'),
      format: document.getElementById('metric-format'),
      file: document.getElementById('metric-file'),
    };

    function setStatus(title, message, state = 'Pronto') {
      statusLabel.textContent = title;
      statusMessage.textContent = message;
      queueState.textContent = state;
    }

    function resetProgress() {
      progressWrap.classList.add('hidden');
      progressCount.textContent = '0 / 0 arquivos';
      progressPercent.textContent = '0%';
      progressBar.style.width = '0%';
      progressElapsed.textContent = 'Tempo decorrido: 00:00';
      progressEta.textContent = 'Tempo restante estimado: --:--';
      lastProgressSnapshot = { processed: 0, total: 0 };
    }

    function formatDuration(totalSeconds) {
      const safeSeconds = Math.max(0, Math.floor(totalSeconds || 0));
      const hours = Math.floor(safeSeconds / 3600);
      const minutes = Math.floor((safeSeconds % 3600) / 60);
      const seconds = safeSeconds % 60;

      const mm = String(minutes).padStart(2, '0');
      const ss = String(seconds).padStart(2, '0');
      if (hours > 0) {
        return `${String(hours).padStart(2, '0')}:${mm}:${ss}`;
      }
      return `${mm}:${ss}`;
    }

    function updateTimeEstimate(processed, total) {
      if (!processingStartMs) {
        progressElapsed.textContent = 'Tempo decorrido: 00:00';
        progressEta.textContent = 'Tempo restante estimado: --:--';
        return;
      }

      const elapsedSeconds = Math.max(0, (Date.now() - processingStartMs) / 1000);
      progressElapsed.textContent = `Tempo decorrido: ${formatDuration(elapsedSeconds)}`;

      const safeTotal = Math.max(0, Number(total) || 0);
      const safeProcessed = Math.max(0, Number(processed) || 0);
      if (safeTotal === 0 || safeProcessed <= 0) {
        progressEta.textContent = 'Tempo restante estimado: --:--';
        return;
      }

      if (safeProcessed >= safeTotal) {
        progressEta.textContent = 'Tempo restante estimado: 00:00';
        return;
      }

      const filesPerSecond = safeProcessed / Math.max(elapsedSeconds, 0.001);
      const remainingFiles = safeTotal - safeProcessed;
      const etaSeconds = remainingFiles / Math.max(filesPerSecond, 0.001);
      progressEta.textContent = `Tempo restante estimado: ${formatDuration(etaSeconds)}`;
    }

    function startElapsedTimer() {
      if (elapsedTimerId) {
        clearInterval(elapsedTimerId);
      }
      elapsedTimerId = setInterval(() => {
        updateTimeEstimate(lastProgressSnapshot.processed, lastProgressSnapshot.total);
      }, 1000);
    }

    function stopElapsedTimer() {
      if (!elapsedTimerId) {
        return;
      }
      clearInterval(elapsedTimerId);
      elapsedTimerId = null;
    }

    function updateProgress(processed, total, fileName = '') {
      if (!total || total < 1) {
        resetProgress();
        return;
      }

      if (!processingStartMs) {
        processingStartMs = Date.now();
      }

      const safeProcessed = Math.max(0, Math.min(processed, total));
      const percent = Math.round((safeProcessed / total) * 100);
      progressWrap.classList.remove('hidden');
      progressCount.textContent = `${safeProcessed} / ${total} arquivos`;
      progressPercent.textContent = `${percent}%`;
      progressBar.style.width = `${percent}%`;
      lastProgressSnapshot = { processed: safeProcessed, total };
      updateTimeEstimate(safeProcessed, total);
    }

    function refreshFileCount() {
      const files = fileInput.files;
      fileCount.textContent = files && files.length
        ? `${files.length} imagem(ns) selecionada(s): ${Array.from(files).map((file) => file.name).join(', ')}`
        : 'Nenhuma imagem selecionada.';
    }

    function clearPreview() {
      previewHead.innerHTML = '';
      previewBody.innerHTML = '';
      tableMessage.classList.add('hidden');
      tableMessage.textContent = '';
      sheetsBlock.classList.add('hidden');
      sheetsBlock.textContent = '';
      downloadSlot.classList.add('hidden');
      downloadSlot.innerHTML = '';
      results.classList.add('hidden');
      metrics.records.textContent = '0';
      metrics.files.textContent = '0';
      metrics.format.textContent = '-';
      metrics.file.textContent = '-';
    }

    function renderPreview(payload) {
      previewHead.innerHTML = '';
      previewBody.innerHTML = '';

      const columns = payload.columns && payload.columns.length
        ? payload.columns
        : (payload.preview_rows[0] ? Object.keys(payload.preview_rows[0]) : []);

      if (!columns.length) {
        tableMessage.textContent = 'Nenhuma linha disponível para visualização.';
        tableMessage.classList.remove('hidden');
        return;
      }

      const headRow = document.createElement('tr');
      columns.forEach((column) => {
        const th = document.createElement('th');
        th.textContent = column;
        headRow.appendChild(th);
      });
      previewHead.appendChild(headRow);

      payload.preview_rows.forEach((row) => {
        const tr = document.createElement('tr');
        columns.forEach((column) => {
          const td = document.createElement('td');
          const value = row[column];
          td.textContent = value === null || value === undefined ? '' : String(value);
          tr.appendChild(td);
        });
        previewBody.appendChild(tr);
      });
    }

    function buildSheetsText(payload) {
      const rows = payload.preview_rows || [];
      if (!rows.length) {
        return '';
      }
      const columns = ['Data', 'Ticker', 'Tipo', 'Quantidade', 'Valor Recebido'];
      const lines = [columns.join('\\t')];
      rows.forEach((row) => {
        lines.push(columns.map((column) => {
          const value = row[column];
          return value === null || value === undefined ? '' : String(value);
        }).join('\\t'));
      });
      return lines.join('\\n');
    }

    async function copySheetsText() {
      if (!lastSheetsText) {
        setStatus('Sem dados', 'Faça o processamento antes de copiar para o Google Sheets.', 'Atenção');
        return;
      }

      try {
        await navigator.clipboard.writeText(lastSheetsText);
        setStatus('Copiado', 'Dados copiados no formato tabulado para colar no Google Sheets.', 'Pronto');
      } catch (error) {
        setStatus('Erro', 'Não foi possível copiar automaticamente. Use o texto exibido na tela.', 'Falha');
      }
    }

    function setLoading(loading) {
      processButton.disabled = loading;
      clearButton.disabled = loading;
      scrollButton.disabled = loading;
      copyButton.disabled = loading;
      fileInput.disabled = loading;
      queueState.textContent = loading ? 'Processando...' : 'Pronto';

      if (loading) {
        processingStartMs = Date.now();
        startElapsedTimer();
      } else {
        updateTimeEstimate(lastProgressSnapshot.processed, lastProgressSnapshot.total);
        stopElapsedTimer();
      }
    }

    async function startProcessingImage(formData) {
      const response = await fetch('/api/process-image', {
        method: 'POST',
        body: formData,
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || payload.message || 'Falha ao processar imagem.');
      }
      return payload;
    }

    async function shutdownApplication() {
      const response = await fetch('/api/system/shutdown', {
        method: 'POST',
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || payload.message || 'Não foi possível encerrar a aplicação.');
      }
      return payload;
    }

    function attemptWindowClose() {
      setTimeout(() => {
        window.open('', '_self');
        window.close();
      }, 350);
    }

    fileInput.addEventListener('change', refreshFileCount);

    ['dragenter', 'dragover'].forEach((eventName) => {
      dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach((eventName) => {
      dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', (event) => {
      const dropped = Array.from(event.dataTransfer.files || []).filter((file) => file.type.startsWith('image/'));
      if (!dropped.length) {
        return;
      }

      const dataTransfer = new DataTransfer();
      dropped.forEach((file) => dataTransfer.items.add(file));
      fileInput.files = dataTransfer.files;
      refreshFileCount();
    });

    document.addEventListener('paste', (event) => {
      const items = Array.from((event.clipboardData && event.clipboardData.items) || []);
      const imageItems = items.filter((item) => item.type.startsWith('image/'));
      if (!imageItems.length) {
        return;
      }

      const dataTransfer = new DataTransfer();
      imageItems.forEach((item, index) => {
        const file = item.getAsFile();
        if (!file) {
          return;
        }
        const ext = (file.type.split('/')[1] || 'png').replace(/[^a-z0-9]/gi, '');
        const safeFile = new File([file], `clipboard_${Date.now()}_${index}.${ext}`, { type: file.type });
        dataTransfer.items.add(safeFile);
      });

      if (dataTransfer.files.length > 0) {
        fileInput.files = dataTransfer.files;
        refreshFileCount();
        setStatus('Imagem colada', 'Imagem capturada do clipboard. Clique em processar.', 'Pronto');
      }
    });

    clearButton.addEventListener('click', () => {
      fileInput.value = '';
      refreshFileCount();
      clearPreview();
      lastSheetsText = '';
      setStatus('Aguardando imagem', 'Selecione ou cole uma imagem e clique em processar.', 'Pronto');
    });

    scrollButton.addEventListener('click', () => {
      results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    copyButton.addEventListener('click', copySheetsText);

    shutdownButton.addEventListener('click', async () => {
      if (activeJobId) {
        setStatus('Ação bloqueada', 'Aguarde o processamento finalizar antes de encerrar a aplicação.', 'Em andamento');
        return;
      }

      shutdownButton.disabled = true;
      setStatus('Encerrando', 'Liberando recursos e finalizando o servidor...', 'Encerrando...');

      try {
        await shutdownApplication();
        setStatus('Encerrando', 'Servidor finalizado. A janela será fechada.', 'Finalizado');
        attemptWindowClose();
      } catch (error) {
        shutdownButton.disabled = false;
        setStatus('Erro', error.message, 'Falha');
      }
    });

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const files = fileInput.files;
      if (!files || !files.length) {
        setStatus('Seleção vazia', 'Adicione ao menos uma imagem para continuar.', 'Atenção');
        return;
      }

      const formData = new FormData();
      formData.append('file', files[0]);
      const paymentDate = document.getElementById('payment-date').value.trim();
      if (paymentDate) {
        formData.append('payment_date', paymentDate);
      }

      clearPreview();
      resetProgress();
      setLoading(true);
      setStatus('Processando', 'Executando OCR na imagem...', 'Em andamento');
      activeJobId = 'image-processing';
      updateProgress(0, 1);

      try {
        const payload = await startProcessingImage(formData);
        updateProgress(1, 1);
        results.classList.remove('hidden');
        metrics.records.textContent = String(payload.records_extracted || 0);
        metrics.files.textContent = '1';
        metrics.format.textContent = 'SHEETS';
        metrics.file.textContent = '-';

        renderPreview(payload);
        lastSheetsText = payload.sheets_text || buildSheetsText(payload);
        if (lastSheetsText) {
          sheetsBlock.textContent = lastSheetsText;
          sheetsBlock.classList.remove('hidden');
        }

        setStatus('Concluído', payload.message || 'Processamento concluído.', 'Finalizado');
      } catch (error) {
        resetProgress();
        setStatus('Erro', error.message, 'Falha');
        tableMessage.textContent = error.message;
        tableMessage.classList.remove('hidden');
        results.classList.remove('hidden');
      } finally {
        activeJobId = null;
        setLoading(false);
      }
    });

    refreshFileCount();
    resetProgress();
  </script>
</body>
</html>"""


def _update_job(job_id: str, **changes: Any) -> None:
  with _JOBS_LOCK:
    job = _PROCESS_JOBS.get(job_id)
    if not job:
      return
    job.update(changes)


def _get_job(job_id: str) -> Optional[Dict[str, Any]]:
  with _JOBS_LOCK:
    job = _PROCESS_JOBS.get(job_id)
    if not job:
      return None
    snapshot = dict(job)
  return snapshot


def _job_cancel_requested(job_id: str) -> bool:
  job = _get_job(job_id)
  if not job:
    return False
  return bool(job.get("cancel_requested"))


def _build_processing_result(
  temp_path: Path,
  year: Optional[int],
  ticker: Optional[str],
  sort_by: str,
  output_format: Optional[str],
  files_received: int,
  e2e_demo: bool,
  progress_callback=None,
  should_stop=None,
) -> Dict[str, Any]:
  before = _snapshot_output_files()
  if e2e_demo:
    if progress_callback:
      progress_callback(
        {
          "stage": "started",
          "current_file": "e2e_sample.pdf",
          "processed_files": 0,
          "failed_files": 0,
          "total_files": files_received,
        }
      )
      time.sleep(0.9)
      progress_callback(
        {
          "stage": "processing",
          "current_file": "e2e_sample.pdf",
          "processed_files": 0,
          "failed_files": 0,
          "total_files": files_received,
        }
      )
      time.sleep(0.9)
      progress_callback(
        {
          "stage": "processed",
          "current_file": "e2e_sample.pdf",
          "processed_files": files_received,
          "failed_files": 0,
          "total_files": files_received,
        }
      )
      progress_callback(
        {
          "stage": "finished",
          "current_file": "",
          "processed_files": files_received,
          "failed_files": 0,
          "total_files": files_received,
        }
      )
    df = _build_e2e_demo_dataframe()
  else:
    try:
      df = analisar_pasta_ou_zip(
        str(temp_path),
        year_filter=year,
        sort_by=sort_by,
        progress_callback=progress_callback,
        should_stop=should_stop,
      )
    except TypeError:
      # Compatibilidade com versões/mocks sem parâmetro progress_callback/should_stop.
      df = analisar_pasta_ou_zip(
        str(temp_path),
        year_filter=year,
        sort_by=sort_by,
      )

  df = _filter_dataframe_by_ticker(df, ticker)

  if df.empty:
    return {
      "message": "Nenhum registro foi extraído dos arquivos enviados.",
      "records_extracted": 0,
      "files_received": files_received,
      "export_format": (output_format or config.get_output_format()).lower(),
      "preview_rows": [],
      "columns": [],
      "filename": None,
      "download_url": None,
    }

  df_preview = ordenar_dados_por_data(df.copy())
  exported = exportar_dados(df, output_format, ticker)
  if not exported:
    raise RuntimeError("Os dados foram extraídos, mas não foi possível exportar o arquivo.")

  exported_file = _find_latest_export(before)
  preview_rows = df_preview.head(80).to_dict(orient="records")

  return {
    "message": f"Processamento concluído com {len(df_preview)} registro(s).",
    "records_extracted": len(df_preview),
    "files_received": files_received,
    "export_format": (output_format or config.get_output_format()).lower(),
    "columns": list(df_preview.columns),
    "preview_rows": preview_rows,
    "filename": exported_file.name if exported_file else None,
    "download_url": f"/api/download/{exported_file.name}" if exported_file else None,
  }


def _run_processing_job(
  job_id: str,
  temp_path: Path,
  year: Optional[int],
  ticker: Optional[str],
  sort_by: str,
  output_format: Optional[str],
  files_received: int,
  e2e_demo: bool,
) -> None:
  def on_progress(progress: Dict[str, Any]) -> None:
    if _job_cancel_requested(job_id):
      _update_job(
        job_id,
        status="cancelling",
        message="Cancelamento solicitado. Finalizando arquivo atual...",
      )
      return

    total_files = int(progress.get("total_files") or 0)
    processed_files = int(progress.get("processed_files") or 0)
    current_file = str(progress.get("current_file") or "")
    stage = str(progress.get("stage") or "processing")
    if stage == "processing" and current_file:
      message = f"Processando arquivo: {current_file}"
    elif stage == "processed":
      message = f"Arquivo concluído: {current_file}"
    elif stage == "error":
      message = f"Arquivo com erro: {current_file}"
    else:
      message = "Processando arquivos..."

    _update_job(
      job_id,
      status="running",
      total_files=total_files,
      processed_files=processed_files,
      current_file=current_file,
      message=message,
    )

  try:
    _update_job(job_id, status="running", message="Iniciando processamento...")
    result = _build_processing_result(
      temp_path=temp_path,
      year=year,
      ticker=ticker,
      sort_by=sort_by,
      output_format=output_format,
      files_received=files_received,
      e2e_demo=e2e_demo,
      progress_callback=on_progress,
      should_stop=lambda: _job_cancel_requested(job_id),
    )

    if _job_cancel_requested(job_id):
      _update_job(
        job_id,
        status="cancelled",
        message="Processamento interrompido pelo usuário.",
        current_file="",
        result=result,
      )
      return

    _update_job(
      job_id,
      status="completed",
      message=result.get("message") or "Processamento concluído.",
      current_file="",
      processed_files=files_received,
      total_files=files_received,
      result=result,
    )
  except Exception as exc:
    _update_job(
      job_id,
      status="failed",
      error=str(exc),
      message="Falha durante o processamento.",
      current_file="",
    )
  finally:
    shutil.rmtree(temp_path, ignore_errors=True)


def _safe_output_path(filename: str) -> Path:
    candidate = (OUTPUT_DIR / filename).resolve()
    if OUTPUT_DIR.resolve() not in candidate.parents and candidate != OUTPUT_DIR.resolve():
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")
    return candidate


def _snapshot_output_files() -> set[str]:
    return {path.name for path in OUTPUT_DIR.glob("dados_extraidos*")}


def _find_latest_export(before: set[str]) -> Optional[Path]:
    candidates = [path for path in OUTPUT_DIR.glob("dados_extraidos*") if path.name not in before]
    if not candidates:
        candidates = list(OUTPUT_DIR.glob("dados_extraidos*"))
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _should_use_e2e_demo(files: List[UploadFile]) -> bool:
    """Habilita dados fixos apenas em execução E2E quando explicitamente solicitado."""
    if os.getenv("WEBAPP_E2E_DEMO") != "1":
        return False
    return any((upload.filename or "").lower() == "e2e_sample.pdf" for upload in files)


def _build_e2e_demo_dataframe() -> pd.DataFrame:
    """Gera dados determinísticos para screenshots E2E com preview e download."""
    return pd.DataFrame(
        {
            "Data": ["10/05/2026", "11/05/2026", "12/05/2026", "13/05/2026"],
            "Ticker": ["VALE3", "PETR4", "PSSA3", "ITSA4"],
            "Operação": ["C", "V", "C", "C"],
            "Quantidade": [10, 5, 30, 12],
            "Preço": ["58.42", "37.10", "28.33", "11.90"],
        }
    )


async def _persist_uploads(files: List[UploadFile], destination: Path) -> None:
    for upload in files:
        file_name = os.path.basename(upload.filename or "arquivo_enviado")
        target = destination / file_name
        content = await upload.read()
        target.write_bytes(content)


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse(HTML_PAGE)


@app.post("/api/process-image")
async def process_image(
    file: UploadFile = File(...),
    payment_date: Optional[str] = Form(default=None),
):
    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Envie um arquivo de imagem.")

    if os.getenv("WEBAPP_E2E_DEMO") == "1":
        return JSONResponse(content=_build_e2e_demo_image_payload())

    image_bytes = await file.read()
    content = await run_in_threadpool(_process_image_content, image_bytes, payment_date)
    return JSONResponse(content=content)


@app.post("/api/process")
async def process_files(
    files: List[UploadFile] = File(...),
    year: Optional[int] = Form(default=None),
    ticker: Optional[str] = Form(default=None),
    sort_by: str = Form(default="name"),
    output_format: Optional[str] = Form(default=None),
):
    if not files:
        raise HTTPException(status_code=400, detail="Envie ao menos um arquivo PDF ou ZIP.")

    with tempfile.TemporaryDirectory(prefix="extrator_web_") as temp_dir:
        temp_path = Path(temp_dir)
        await _persist_uploads(files, temp_path)

        try:
            content = await run_in_threadpool(
                _build_processing_result,
                temp_path,
                year,
                ticker,
                sort_by,
                output_format,
                len(files),
                _should_use_e2e_demo(files),
                None,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return JSONResponse(content=content)


@app.post("/api/process/start")
async def start_process_job(
    files: List[UploadFile] = File(...),
    year: Optional[int] = Form(default=None),
    ticker: Optional[str] = Form(default=None),
    sort_by: str = Form(default="name"),
    output_format: Optional[str] = Form(default=None),
):
    if not files:
        raise HTTPException(status_code=400, detail="Envie ao menos um arquivo PDF ou ZIP.")

    temp_path = Path(tempfile.mkdtemp(prefix="extrator_web_job_"))
    await _persist_uploads(files, temp_path)

    job_id = uuid.uuid4().hex
    job_state = {
        "job_id": job_id,
        "status": "queued",
        "message": "Fila criada. Processamento será iniciado.",
      "cancel_requested": False,
        "current_file": "",
        "processed_files": 0,
        "total_files": len(files),
        "result": None,
        "error": None,
    }
    with _JOBS_LOCK:
        _PROCESS_JOBS[job_id] = job_state

    worker = threading.Thread(
        target=_run_processing_job,
        args=(
            job_id,
            temp_path,
            year,
            ticker,
            sort_by,
            output_format,
            len(files),
            _should_use_e2e_demo(files),
        ),
        daemon=True,
    )
    worker.start()

    return JSONResponse(content={"job_id": job_id})


@app.get("/api/process/status/{job_id}")
def get_process_status(job_id: str):
    job = _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")

    total_files = int(job.get("total_files") or 0)
    processed_files = int(job.get("processed_files") or 0)
    progress_percent = (
        min(100, max(0, round((processed_files / total_files) * 100))) if total_files > 0 else 0
    )

    return JSONResponse(
        content={
            "job_id": job_id,
            "status": job.get("status"),
            "message": job.get("message"),
            "current_file": job.get("current_file"),
            "processed_files": processed_files,
            "total_files": total_files,
            "progress_percent": progress_percent,
            "result": job.get("result"),
            "error": job.get("error"),
        }
    )


@app.post("/api/process/cancel/{job_id}")
def cancel_process_job(job_id: str):
    job = _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")

    status = str(job.get("status") or "")
    if status in {"completed", "failed", "cancelled"}:
        return JSONResponse(
            content={
                "job_id": job_id,
                "status": status,
                "message": job.get("message") or "Job já finalizado.",
            }
        )

    _update_job(
        job_id,
        cancel_requested=True,
        status="cancelling",
        message="Cancelamento solicitado. Finalizando arquivo atual...",
    )

    return JSONResponse(
        content={
            "job_id": job_id,
            "status": "cancelling",
            "message": "Cancelamento solicitado. Finalizando arquivo atual...",
        }
    )


@app.post("/api/system/shutdown")
def shutdown_webapp():
    if not bool(getattr(app.state, "allow_shutdown", False)):
        raise HTTPException(status_code=403, detail="Encerramento remoto não está habilitado.")

    _schedule_server_shutdown()
    return JSONResponse(
        content={
            "status": "shutting_down",
            "message": "Servidor será encerrado em instantes.",
        }
    )


@app.get("/api/download/{filename}")
def download_file(filename: str):
    file_path = _safe_output_path(filename)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    media_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type=media_type,
    )


if __name__ == "__main__":
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="Executa o frontend web do extrator.")
    parser.add_argument("--host", default="0.0.0.0", help="Host de bind do servidor web.")
    parser.add_argument("--port", type=int, default=8000, help="Porta do servidor web.")
    parser.set_defaults(open_browser=os.getenv("WEBAPP_E2E_DEMO") != "1")
    parser.add_argument(
      "--open-browser",
      dest="open_browser",
      action="store_true",
      help="Força abertura automática da URL do frontend no navegador.",
    )
    parser.add_argument(
      "--no-open-browser",
      dest="open_browser",
      action="store_false",
      help="Não abre a URL automaticamente no navegador.",
    )
    parser.add_argument(
      "--browser-delay",
      type=float,
      default=1.0,
      help="Atraso (segundos) antes de abrir o navegador automaticamente.",
    )
    args = parser.parse_args()

    app.state.allow_shutdown = True
    if args.open_browser:
      browser_host = args.host
      if browser_host in {"0.0.0.0", "::"}:
        browser_host = "127.0.0.1"
      _schedule_browser_open(f"http://{browser_host}:{args.port}", args.browser_delay)

    uvicorn.run(app, host=args.host, port=args.port, reload=False)