#!/usr/bin/env python3
"""Aplicação web para upload, processamento e visualização dos resultados."""

from __future__ import annotations

import mimetypes
import os
import shutil
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

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


HTML_PAGE = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Extrator Notas Corretagem</title>
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
        <div class="eyebrow">Drag and drop de PDFs e ZIPs</div>
        <h1>Extrator de Notas de Corretagem</h1>
        <p class="lede">
          Arraste PDFs ou arquivos ZIP, processe no backend existente e receba o resultado na tela
          com opção de download do arquivo exportado. O preview mostra os dados extraídos sem
          exigir troca de contexto.
        </p>

        <div class="hero-stats">
          <div class="stat"><strong>PDF + ZIP</strong><span>Entrada única ou múltipla</span></div>
          <div class="stat"><strong>Preview</strong><span>Dados exibidos no navegador</span></div>
          <div class="stat"><strong>Download</strong><span>CSV, XLSX ou JSON gerado</span></div>
        </div>
      </div>

      <aside class="card status-panel">
        <p class="status-title"><span>Processamento</span><span id="queue-state">Pronto</span></p>
        <div class="status-box">
          <div class="status-pill"><span class="pulse"></span><span id="status-label">Aguardando arquivos</span></div>
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
          <div id="status-message" class="message">Selecione os arquivos e clique em processar.</div>
          <div id="download-slot" class="hidden"></div>
        </div>
      </aside>
    </section>

    <section class="card" style="margin-top: 20px; padding: 24px;">
      <form id="upload-form">
        <div id="dropzone" class="dropzone">
          <strong>Solte aqui seus PDFs ou ZIPs</strong>
          <p>Você também pode clicar nesta área para escolher múltiplos arquivos.</p>
          <div id="file-count" class="file-count">Nenhum arquivo selecionado.</div>
          <input class="file-input" id="files" name="files" type="file" accept=".pdf,.zip,application/pdf,application/zip" multiple />
        </div>

        <div class="controls">
          <div>
            <label for="year">Ano</label>
            <input id="year" name="year" type="number" min="1900" max="2100" placeholder="Opcional" />
          </div>
          <div>
            <label for="ticker">Ticker</label>
            <input id="ticker" name="ticker" type="text" placeholder="Ex.: PSSA3" />
          </div>
          <div>
            <label for="sort-by">Ordenação</label>
            <select id="sort-by" name="sort_by">
              <option value="name">Nome</option>
              <option value="mtime">Data de modificação</option>
              <option value="ctime">Data de criação</option>
            </select>
          </div>
          <div>
            <label for="output-format">Saída</label>
            <select id="output-format" name="output_format">
              <option value="xlsx">XLSX</option>
              <option value="csv">CSV</option>
              <option value="json">JSON</option>
            </select>
          </div>
          <div class="process-actions">
            <button id="process-button" class="primary" type="submit">Processar</button>
            <button id="cancel-button" class="danger hidden" type="button">Interromper processamento</button>
          </div>
        </div>

        <div class="actions">
          <button id="clear-button" class="secondary" type="button">Limpar seleção</button>
          <button id="scroll-button" class="secondary" type="button">Ver preview</button>
        </div>
      </form>
    </section>

    <section id="results" class="results hidden">
      <div class="results-grid">
        <div class="result-card"><span>Registros extraídos</span><strong id="metric-records">0</strong></div>
        <div class="result-card"><span>Arquivos enviados</span><strong id="metric-files">0</strong></div>
        <div class="result-card"><span>Formato exportado</span><strong id="metric-format">-</strong></div>
        <div class="result-card"><span>Arquivo gerado</span><strong id="metric-file">-</strong></div>
      </div>

      <div class="card" style="padding: 18px;">
        <div id="table-message" class="message hidden"></div>
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
    const cancelButton = document.getElementById('cancel-button');
    const results = document.getElementById('results');
    const downloadSlot = document.getElementById('download-slot');
    const tableMessage = document.getElementById('table-message');
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
    let cancellationRequested = false;
    let processingStartMs = null;
    let elapsedTimerId = null;
    let lastProgressSnapshot = { processed: 0, total: 0 };

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
        ? `${files.length} arquivo(s) selecionado(s): ${Array.from(files).map((file) => file.name).join(', ')}`
        : 'Nenhum arquivo selecionado.';
    }

    function clearPreview() {
      previewHead.innerHTML = '';
      previewBody.innerHTML = '';
      tableMessage.classList.add('hidden');
      tableMessage.textContent = '';
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

    function renderDownload(payload) {
      downloadSlot.innerHTML = '';
      if (!payload.download_url) {
        downloadSlot.classList.add('hidden');
        return;
      }

      const link = document.createElement('a');
      link.href = payload.download_url;
      link.textContent = 'Baixar arquivo processado';
      link.className = 'primary';
      link.style.display = 'inline-flex';
      link.style.textDecoration = 'none';
      link.style.alignItems = 'center';
      link.style.justifyContent = 'center';
      link.style.padding = '14px 20px';
      downloadSlot.appendChild(link);
      downloadSlot.classList.remove('hidden');
    }

    function setLoading(loading) {
      processButton.disabled = loading;
      clearButton.disabled = loading;
      scrollButton.disabled = loading;
      fileInput.disabled = loading;
      cancelButton.classList.toggle('hidden', !loading);
      cancelButton.disabled = !loading || cancellationRequested;
      queueState.textContent = loading ? 'Processando...' : 'Pronto';

      if (loading) {
        processingStartMs = Date.now();
        startElapsedTimer();
      } else {
        updateTimeEstimate(lastProgressSnapshot.processed, lastProgressSnapshot.total);
        stopElapsedTimer();
      }
    }

    async function requestCancel(jobId) {
      const response = await fetch(`/api/process/cancel/${jobId}`, {
        method: 'POST',
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || payload.message || 'Não foi possível solicitar o cancelamento.');
      }
      return payload;
    }

    async function startProcessing(formData) {
      const response = await fetch('/api/process/start', {
        method: 'POST',
        body: formData,
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || payload.message || 'Falha ao iniciar o processamento.');
      }
      return payload;
    }

    async function pollJobUntilFinished(jobId) {
      while (true) {
        const response = await fetch(`/api/process/status/${jobId}`);
        const payload = await response.json();

        if (!response.ok) {
          throw new Error(payload.detail || 'Não foi possível consultar o status do processamento.');
        }

        updateProgress(payload.processed_files || 0, payload.total_files || 0, payload.current_file || '');
        if (payload.status === 'running') {
          setStatus('Processando', payload.message || 'Extraindo dados dos arquivos...', 'Em andamento');
        }

        if (payload.status === 'cancelling') {
          setStatus('Cancelando', payload.message || 'Finalizando arquivo atual...', 'Cancelando...');
        }

        if (payload.status === 'completed') {
          return payload;
        }

        if (payload.status === 'cancelled') {
          return payload;
        }

        if (payload.status === 'failed') {
          throw new Error(payload.error || 'Falha ao processar arquivos.');
        }

        await new Promise((resolve) => setTimeout(resolve, 700));
      }
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
      const dropped = Array.from(event.dataTransfer.files || []);
      if (!dropped.length) {
        return;
      }

      const dataTransfer = new DataTransfer();
      dropped.forEach((file) => dataTransfer.items.add(file));
      fileInput.files = dataTransfer.files;
      refreshFileCount();
    });

    clearButton.addEventListener('click', () => {
      fileInput.value = '';
      refreshFileCount();
      clearPreview();
      setStatus('Aguardando arquivos', 'Selecione os arquivos e clique em processar.', 'Pronto');
    });

    scrollButton.addEventListener('click', () => {
      results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    cancelButton.addEventListener('click', async () => {
      if (!activeJobId || cancellationRequested) {
        return;
      }

      cancellationRequested = true;
      cancelButton.disabled = true;
      setStatus('Cancelando', 'Solicitação enviada. Finalizando arquivo atual...', 'Cancelando...');

      try {
        await requestCancel(activeJobId);
      } catch (error) {
        cancellationRequested = false;
        cancelButton.disabled = false;
        setStatus('Erro', error.message, 'Falha');
      }
    });

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const files = fileInput.files;
      if (!files || !files.length) {
        setStatus('Seleção vazia', 'Adicione ao menos um PDF ou ZIP para continuar.', 'Atenção');
        return;
      }

      const formData = new FormData();
      Array.from(files).forEach((file) => formData.append('files', file));

      const year = document.getElementById('year').value.trim();
      const ticker = document.getElementById('ticker').value.trim();
      const sortBy = document.getElementById('sort-by').value;
      const outputFormat = document.getElementById('output-format').value;

      if (year) formData.append('year', year);
      if (ticker) formData.append('ticker', ticker);
      formData.append('sort_by', sortBy);
      formData.append('output_format', outputFormat);

      clearPreview();
      resetProgress();
      setLoading(true);
      setStatus('Processando', 'Preparando arquivos para processamento...', 'Em andamento');

      try {
        const started = await startProcessing(formData);
        activeJobId = started.job_id;
        cancellationRequested = false;

        const responsePayload = await pollJobUntilFinished(started.job_id);
        const payload = responsePayload.result || {};

        if (responsePayload.status === 'cancelled') {
          setStatus('Interrompido', responsePayload.message || 'Processamento interrompido pelo usuário.', 'Interrompido');
        }

        if (responsePayload.status === 'completed') {
          updateProgress(payload.files_received || 0, payload.files_received || 0, '');
        }

        if (payload && Object.keys(payload).length) {
          results.classList.remove('hidden');
          metrics.records.textContent = String(payload.records_extracted || 0);
          metrics.files.textContent = String(payload.files_received || 0);
          metrics.format.textContent = String(payload.export_format || '-').toUpperCase();
          metrics.file.textContent = payload.filename || '-';

          renderPreview(payload);
          renderDownload(payload);
        }

        if (responsePayload.status === 'completed') {
          const message = payload.message || 'Processamento concluído.';
          setStatus('Concluído', message, 'Finalizado');
          if (payload.preview_rows && payload.preview_rows.length) {
            results.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }
      } catch (error) {
        resetProgress();
        setStatus('Erro', error.message, 'Falha');
        tableMessage.textContent = error.message;
        tableMessage.classList.remove('hidden');
        results.classList.remove('hidden');
      } finally {
        activeJobId = null;
        cancellationRequested = false;
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
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port, reload=False)