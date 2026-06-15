#!/usr/bin/env python3
"""Dashboard web para acompanhar estatísticas históricas de processamento."""

from __future__ import annotations

import argparse
import threading
import webbrowser

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from execution_stats import build_history_payload

app = FastAPI(
    title="Dashboard de Estatísticas",
    description="Visualização histórica das métricas de processamento de PDFs.",
)


HTML_PAGE = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Dashboard de Estatísticas</title>
  <style>
    :root {
      --bg: #f6f1e8;
      --ink: #172126;
      --muted: #6b7280;
      --panel: rgba(255, 251, 245, 0.88);
      --line: rgba(23, 33, 38, 0.10);
      --accent: #d97706;
      --accent-2: #0f766e;
      --accent-3: #1d4ed8;
      --danger: #b91c1c;
      --radius: 24px;
      --shadow: 0 18px 50px rgba(59, 34, 11, 0.10);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(217, 119, 6, 0.16), transparent 30%),
        radial-gradient(circle at 85% 10%, rgba(15, 118, 110, 0.14), transparent 24%),
        linear-gradient(180deg, #f8f3ea 0%, #efe6d8 100%);
    }

    .shell {
      max-width: 1320px;
      margin: 0 auto;
      padding: 28px 20px 44px;
    }

    .hero,
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      backdrop-filter: blur(12px);
    }

    .hero {
      padding: 28px;
      display: grid;
      gap: 18px;
      margin-bottom: 20px;
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      width: fit-content;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(217, 119, 6, 0.12);
      color: var(--accent);
      font-size: 0.78rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    h1 {
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", serif;
      font-size: clamp(2.1rem, 5vw, 4rem);
      line-height: 0.98;
      letter-spacing: -0.04em;
    }

    .lede {
      margin: 0;
      max-width: 72ch;
      color: var(--muted);
      line-height: 1.7;
    }

    .grid,
    .trend-grid {
      display: grid;
      gap: 16px;
    }

    .grid {
      grid-template-columns: repeat(4, minmax(0, 1fr));
      margin-bottom: 20px;
    }

    .trend-grid {
      grid-template-columns: 1.35fr 1fr;
      margin-bottom: 20px;
    }

    .card {
      padding: 20px;
      border-radius: 20px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.55);
    }

    .metric-label {
      display: block;
      color: var(--muted);
      font-size: 0.86rem;
      margin-bottom: 10px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .metric-value {
      font-size: 2rem;
      font-weight: 700;
    }

    .metric-foot {
      margin-top: 8px;
      color: var(--muted);
      font-size: 0.92rem;
    }

    .panel {
      padding: 20px;
    }

    .panel h2 {
      margin: 0 0 10px;
      font-size: 1rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
    }

    .panel p {
      margin: 0 0 16px;
      color: var(--muted);
    }

    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 14px;
    }

    button {
      border: 0;
      border-radius: 999px;
      padding: 12px 18px;
      font: inherit;
      cursor: pointer;
      background: linear-gradient(135deg, var(--accent) 0%, #f59e0b 100%);
      color: #fff7ed;
      box-shadow: 0 12px 24px rgba(217, 119, 6, 0.18);
    }

    button.secondary {
      background: linear-gradient(135deg, var(--accent-2) 0%, #14b8a6 100%);
    }

    .chart {
      width: 100%;
      height: 280px;
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(255,255,255,0.7), rgba(247, 241, 232, 0.8));
      border: 1px solid var(--line);
      padding: 12px;
    }

    .legend {
      display: flex;
      gap: 14px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 0.9rem;
      margin-top: 12px;
    }

    .legend span::before {
      content: "";
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 999px;
      margin-right: 8px;
      vertical-align: middle;
    }

    .legend .line::before { background: var(--accent-3); }
    .legend .bars::before { background: var(--accent); }

    .table-wrap {
      overflow: auto;
      border-radius: 18px;
      border: 1px solid var(--line);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 980px;
      background: rgba(255,255,255,0.64);
    }

    th, td {
      padding: 13px 14px;
      text-align: left;
      border-bottom: 1px solid rgba(23, 33, 38, 0.08);
    }

    th {
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
      background: rgba(255,255,255,0.76);
      position: sticky;
      top: 0;
    }

    .status {
      display: inline-flex;
      align-items: center;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 0.82rem;
      font-weight: 600;
    }

    .status.completed { background: rgba(15, 118, 110, 0.12); color: var(--accent-2); }
    .status.failed { background: rgba(185, 28, 28, 0.12); color: var(--danger); }
    .status.cancelled { background: rgba(29, 78, 216, 0.12); color: var(--accent-3); }
    .status.running, .status.warning { background: rgba(217, 119, 6, 0.12); color: var(--accent); }

    .empty {
      padding: 18px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.56);
      border: 1px dashed var(--line);
      color: var(--muted);
    }

    @media (max-width: 1120px) {
      .grid,
      .trend-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="eyebrow">Histórico de performance</div>
      <h1>Como o extrator vem se comportando ao longo do tempo</h1>
      <p class="lede">
        Esta aplicação lê os arquivos de estatísticas gerados a cada execução e mostra evolução de
        throughput, volume e latência. Use isso para identificar regressões, sazonalidade e PDFs
        com comportamento fora da curva.
      </p>
    </section>

    <section class="grid" id="summary-grid"></section>

    <section class="trend-grid">
      <div class="panel">
        <h2>Evolução por execução</h2>
        <p>Linhas para tempo total e barras para registros extraídos por run.</p>
        <div class="actions">
          <button id="reload-button">Atualizar agora</button>
          <button id="toggle-limit" class="secondary">Mostrar 20 execuções</button>
        </div>
        <svg id="trend-chart" class="chart" viewBox="0 0 920 280" preserveAspectRatio="none"></svg>
        <div class="legend">
          <span class="line">Tempo total</span>
          <span class="bars">Registros extraídos</span>
        </div>
      </div>

      <div class="panel">
        <h2>Destaques</h2>
        <p id="highlights">Carregando...</p>
        <div id="outliers"></div>
      </div>
    </section>

    <section class="panel">
      <h2>Execuções recentes</h2>
      <p>Resumo detalhado por run, com foco em arquivos processados, páginas e tempos médios.</p>
      <div id="history-slot" class="table-wrap"></div>
    </section>
  </main>

  <script>
    const summaryGrid = document.getElementById('summary-grid');
    const historySlot = document.getElementById('history-slot');
    const trendChart = document.getElementById('trend-chart');
    const highlights = document.getElementById('highlights');
    const outliers = document.getElementById('outliers');
    const reloadButton = document.getElementById('reload-button');
    const toggleLimitButton = document.getElementById('toggle-limit');
    let limit = 20;

    function formatNumber(value, digits = 2) {
      const numeric = Number(value || 0);
      return numeric.toLocaleString('pt-BR', {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      });
    }

    function formatSeconds(value) {
      const seconds = Math.max(0, Number(value || 0));
      if (seconds >= 3600) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const rest = Math.floor(seconds % 60);
        return `${hours}h ${minutes}m ${rest}s`;
      }
      if (seconds >= 60) {
        const minutes = Math.floor(seconds / 60);
        const rest = Math.floor(seconds % 60);
        return `${minutes}m ${rest}s`;
      }
      return `${formatNumber(seconds, 2)}s`;
    }

    function statusClass(status) {
      return ['completed', 'failed', 'cancelled', 'running', 'warning'].includes(status)
        ? status
        : 'warning';
    }

    function renderSummary(summary) {
      const cards = [
        {
          label: 'Execuções registradas',
          value: formatNumber(summary.total_runs || 0, 0),
          foot: `${formatNumber(summary.completed_runs || 0, 0)} concluídas com sucesso`,
        },
        {
          label: 'Arquivos processados',
          value: formatNumber(summary.total_files || 0, 0),
          foot: `${formatNumber(summary.avg_files_per_run || 0)} por execução`,
        },
        {
          label: 'Registros extraídos',
          value: formatNumber(summary.total_records || 0, 0),
          foot: `${formatNumber(summary.avg_records_per_run || 0)} por execução`,
        },
        {
          label: 'Latência média por PDF',
          value: formatSeconds(summary.avg_seconds_per_pdf || 0),
          foot: `Página: ${formatSeconds(summary.avg_seconds_per_page || 0)} | Registro: ${formatSeconds(summary.avg_seconds_per_record || 0)}`,
        },
      ];

      summaryGrid.innerHTML = cards.map((card) => `
        <article class="card">
          <span class="metric-label">${card.label}</span>
          <div class="metric-value">${card.value}</div>
          <div class="metric-foot">${card.foot}</div>
        </article>
      `).join('');
    }

    function buildLinePath(points, maxValue, chartHeight, topPadding) {
      if (!points.length) {
        return '';
      }
      return points.map((point, index) => {
        const x = 50 + index * ((820) / Math.max(points.length - 1, 1));
        const y = topPadding + (chartHeight - ((point / Math.max(maxValue, 1)) * chartHeight));
        return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
      }).join(' ');
    }

    function renderTrendChart(runs) {
      if (!runs.length) {
        trendChart.innerHTML = '<text x="40" y="40" fill="#6b7280">Nenhuma execução registrada ainda.</text>';
        return;
      }

      const ordered = [...runs].reverse();
      const elapsedValues = ordered.map((run) => Number(run.elapsed_seconds || 0));
      const recordValues = ordered.map((run) => Number(run.records_extracted || 0));
      const maxElapsed = Math.max(...elapsedValues, 1);
      const maxRecords = Math.max(...recordValues, 1);
      const chartHeight = 180;
      const topPadding = 28;
      const barWidth = Math.max(14, 760 / Math.max(ordered.length, 1));
      const linePath = buildLinePath(elapsedValues, maxElapsed, chartHeight, topPadding);

      const bars = ordered.map((run, index) => {
        const x = 50 + index * (820 / Math.max(ordered.length, 1));
        const barHeight = (Number(run.records_extracted || 0) / maxRecords) * chartHeight;
        const y = topPadding + (chartHeight - barHeight);
        return `<rect x="${x}" y="${y}" width="${Math.max(8, barWidth - 10)}" height="${barHeight}" rx="8" fill="#d97706" opacity="0.78"><title>${run.started_at}: ${run.records_extracted} registros</title></rect>`;
      }).join('');

      const dots = ordered.map((run, index) => {
        const x = 50 + index * (820 / Math.max(ordered.length - 1, 1));
        const y = topPadding + (chartHeight - ((Number(run.elapsed_seconds || 0) / maxElapsed) * chartHeight));
        return `<circle cx="${x}" cy="${y}" r="4.5" fill="#1d4ed8"><title>${run.started_at}: ${formatSeconds(run.elapsed_seconds)}</title></circle>`;
      }).join('');

      const labels = ordered.map((run, index) => {
        const x = 50 + index * (820 / Math.max(ordered.length - 1, 1));
        const label = String(run.started_at || '').slice(5, 16).replace('T', ' ');
        return `<text x="${x}" y="248" font-size="10" fill="#6b7280" text-anchor="middle">${label}</text>`;
      }).join('');

      trendChart.innerHTML = `
        <line x1="40" y1="208" x2="890" y2="208" stroke="#cbd5e1" stroke-width="1" />
        <line x1="40" y1="28" x2="40" y2="208" stroke="#cbd5e1" stroke-width="1" />
        ${bars}
        <path d="${linePath}" fill="none" stroke="#1d4ed8" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
        ${dots}
        ${labels}
      `;
    }

    function renderHighlights(runs) {
      if (!runs.length) {
        highlights.textContent = 'Nenhuma execução registrada ainda.';
        outliers.innerHTML = '';
        return;
      }

      const slowest = [...runs].sort((a, b) => (b.elapsed_seconds || 0) - (a.elapsed_seconds || 0))[0];
      const densest = [...runs].sort((a, b) => (b.records_extracted || 0) - (a.records_extracted || 0))[0];
      const fastestPerPdf = [...runs]
        .filter((run) => Number(run.processed_files || 0) > 0)
        .sort((a, b) => (a.avg_seconds_per_pdf || 0) - (b.avg_seconds_per_pdf || 0))[0];

      highlights.innerHTML = `
        Execução mais lenta: <strong>${formatSeconds(slowest.elapsed_seconds)}</strong> em ${slowest.started_at}.<br />
        Maior volume: <strong>${formatNumber(densest.records_extracted || 0, 0)} registros</strong> em ${densest.started_at}.<br />
        Melhor média por PDF: <strong>${formatSeconds(fastestPerPdf ? fastestPerPdf.avg_seconds_per_pdf : 0)}</strong>.
      `;

      const alerts = runs
        .filter((run) => Number(run.avg_seconds_per_record || 0) > 0.15 || Number(run.failed_files || 0) > 0)
        .slice(0, 4)
        .map((run) => `
          <div class="card" style="margin-top: 10px;">
            <strong>${run.started_at}</strong>
            <div class="metric-foot">Status: ${run.status} | Falhas: ${run.failed_files} | Tempo/registro: ${formatSeconds(run.avg_seconds_per_record)}</div>
          </div>
        `)
        .join('');

      outliers.innerHTML = alerts || '<div class="empty">Nenhum outlier recente pelos critérios atuais.</div>';
    }

    function renderHistoryTable(runs) {
      if (!runs.length) {
        historySlot.innerHTML = '<div class="empty">Nenhum arquivo de estatística foi encontrado em resouces/output/stats.</div>';
        return;
      }

      const rows = runs.map((run) => `
        <tr>
          <td>${run.started_at || '-'}</td>
          <td><span class="status ${statusClass(run.status)}">${run.status}</span></td>
          <td>${formatNumber(run.processed_files || 0, 0)}</td>
          <td>${formatNumber(run.pages_processed || 0, 0)}</td>
          <td>${formatNumber(run.records_extracted || 0, 0)}</td>
          <td>${formatSeconds(run.elapsed_seconds || 0)}</td>
          <td>${formatSeconds(run.avg_seconds_per_pdf || 0)}</td>
          <td>${formatSeconds(run.avg_seconds_per_page || 0)}</td>
          <td>${formatSeconds(run.avg_seconds_per_record || 0)}</td>
          <td>${formatNumber(run.avg_records_per_pdf || 0)}</td>
          <td>${run.year_filter ?? '-'}</td>
          <td>${run.stats_file || '-'}</td>
        </tr>
      `).join('');

      historySlot.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Início</th>
              <th>Status</th>
              <th>PDFs</th>
              <th>Páginas</th>
              <th>Registros</th>
              <th>Tempo total</th>
              <th>Tempo/PDF</th>
              <th>Tempo/página</th>
              <th>Tempo/registro</th>
              <th>Registros/PDF</th>
              <th>Filtro ano</th>
              <th>Arquivo</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      `;
    }

    async function loadHistory() {
      const response = await fetch(`/api/history?limit=${limit}`);
      const payload = await response.json();
      renderSummary(payload.summary || {});
      renderTrendChart(payload.runs || []);
      renderHighlights(payload.runs || []);
      renderHistoryTable(payload.runs || []);
    }

    reloadButton.addEventListener('click', loadHistory);
    toggleLimitButton.addEventListener('click', () => {
      limit = limit === 20 ? 60 : 20;
      toggleLimitButton.textContent = limit === 20 ? 'Mostrar 60 execuções' : 'Mostrar 20 execuções';
      loadHistory();
    });

    loadHistory();
  </script>
</body>
</html>"""


def _schedule_browser_open(url: str, delay_seconds: float = 1.0) -> None:
    def _open() -> None:
        try:
            webbrowser.open(url, new=2, autoraise=True)
        except Exception:
            return

    timer = threading.Timer(max(delay_seconds, 0.0), _open)
    timer.daemon = True
    timer.start()


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse(HTML_PAGE)


@app.get("/api/history")
def get_history(limit: int = 20) -> JSONResponse:
    return JSONResponse(content=build_history_payload(limit=max(1, min(limit, 200))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dashboard histórico de métricas do extrator")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8011)
    parser.add_argument("--no-open-browser", action="store_true")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"
    if not args.no_open_browser:
        _schedule_browser_open(url)

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)
