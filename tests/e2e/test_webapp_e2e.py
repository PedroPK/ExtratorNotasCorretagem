import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

# Caminhos para salvar os prints
ROOT_DIR = Path(__file__).resolve().parents[2]
IMG_DIR = ROOT_DIR / "docs" / "img"
IMG_DIR.mkdir(parents=True, exist_ok=True)
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

E2E_PORT = 8010
BASE_URL = f"http://127.0.0.1:{E2E_PORT}"


def _port_is_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def _wait_for_server(url: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.2)
    raise RuntimeError(f"Servidor não respondeu em {url} dentro do timeout.")


def _create_sample_pdf() -> str:
    """Cria um PDF simples de exemplo para upload no cenário E2E."""
    pdf_path = FIXTURES_DIR / "e2e_sample.pdf"
    if not pdf_path.exists():
        with open(pdf_path, "wb") as f:
            f.write(
                b"%PDF-1.4\n"
                b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
                b"2 0 obj\n<< /Type /Pages /Count 1 /Kids [3 0 R] >>\nendobj\n"
                b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
                b"4 0 obj\n<< /Length 62 >>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Extrator Notas Corretagem - E2E Sample) Tj\nET\nendstream\nendobj\n"
                b"xref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000062 00000 n \n0000000120 00000 n \n0000000221 00000 n \n"
                b"trailer\n<< /Root 1 0 R /Size 5 >>\nstartxref\n343\n%%EOF"
            )
    return str(pdf_path)


def _start_server() -> subprocess.Popen:
    env = os.environ.copy()
    env["WEBAPP_E2E_DEMO"] = "1"
    process = subprocess.Popen(
        [sys.executable, "src/webapp.py", "--port", str(E2E_PORT)],
        cwd=str(ROOT_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _wait_for_server(BASE_URL)
    return process


def _stop_server(process: subprocess.Popen) -> None:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


@pytest.mark.e2e
@pytest.mark.skipif(os.getenv("CI"), reason="Evita rodar em CI sem servidor web")
def test_webapp_e2e():
    """
    Teste E2E: sobe servidor local, faz upload e captura prints com preview e download visíveis.
    """
    if _port_is_open("127.0.0.1", E2E_PORT):
        raise RuntimeError(
            f"Porta {E2E_PORT} já está em uso. Feche o processo da porta antes de rodar o E2E."
        )

    server = _start_server()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1600, "height": 1300})
            page.goto(BASE_URL, timeout=15000)
            page.wait_for_selector("#upload-form")
            page.screenshot(path=str(IMG_DIR / "webapp_upload.png"), full_page=True)

            # Faz upload do PDF de exemplo
            page.set_input_files("input[type=file]", _create_sample_pdf())
            page.screenshot(path=str(IMG_DIR / "webapp_upload_selected.png"), full_page=True)

            # Processa e aguarda o preview
            page.click("#process-button")
            page.wait_for_selector("#results:not(.hidden)", timeout=15000)
            page.wait_for_selector("#preview-table tbody tr", timeout=15000)
            page.locator("#results").scroll_into_view_if_needed()
            page.screenshot(path=str(IMG_DIR / "webapp_preview.png"), full_page=True)

            # Captura estado com download disponível
            page.wait_for_selector("#download-slot a", timeout=15000)
            page.locator("#download-slot").scroll_into_view_if_needed()
            page.screenshot(path=str(IMG_DIR / "webapp_download.png"), full_page=True)

            browser.close()
    finally:
        _stop_server(server)

if __name__ == "__main__":
    test_webapp_e2e()
