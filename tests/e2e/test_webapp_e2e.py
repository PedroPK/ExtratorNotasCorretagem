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


def _create_sample_image() -> str:
    image_path = FIXTURES_DIR / "e2e_sample.png"
    if image_path.exists():
        return str(image_path)

    try:
        from PIL import Image
    except ImportError:
        image_path.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0bIDATx\x9cc``\x00\x00\x00\x03\x00\x01h&Y\r\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return str(image_path)

    image = Image.new("RGB", (1200, 700), "white")
    image.save(image_path, format="PNG")
    return str(image_path)



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

            # Faz upload da imagem de exemplo
            page.set_input_files("#files", _create_sample_image())
            page.screenshot(path=str(IMG_DIR / "webapp_upload_selected.png"), full_page=True)

            # Processa e aguarda o preview
            page.click("#process-button")
            page.wait_for_selector("#results:not(.hidden)", timeout=15000)
            page.wait_for_selector("#preview-table tbody tr", timeout=15000)
            page.locator("#progress-wrap").scroll_into_view_if_needed()
            page.screenshot(path=str(IMG_DIR / "webapp_progress.png"), full_page=True)
            page.locator("#results").scroll_into_view_if_needed()
            page.screenshot(path=str(IMG_DIR / "webapp_preview.png"), full_page=True)

            # Captura estado com texto pronto para copiar no Sheets
            page.wait_for_selector("#sheets-block:not(.hidden)", timeout=15000)
            page.locator("#sheets-block").scroll_into_view_if_needed()
            page.screenshot(path=str(IMG_DIR / "webapp_sheets.png"), full_page=True)

            browser.close()
    finally:
        _stop_server(server)

if __name__ == "__main__":
    test_webapp_e2e()
