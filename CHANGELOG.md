# Changelog

Todas as mudanças relevantes deste projeto serão documentadas neste arquivo.

## [1.5.1] - 2026-06-15

### Changed
- TSV gerado no processamento de imagem agora é ordenado pela coluna Data, da mais antiga para a mais recente.

## [1.5.0] - 2026-06-09

### Added
- Endpoint `POST /api/process-image` para processamento de extrato de dividendos por imagem.
- OCR no backend com `pytesseract` e `Pillow`.
- Geração de saída tabulada (`sheets_text`) pronta para copiar e colar no Google Sheets.
- Suporte no frontend para upload de imagem, drag and drop e colagem via Ctrl/Cmd+V.
- Botão de cópia para clipboard no formato de colunas: Data, Ticker, Tipo, Quantidade, Valor Recebido.
- Modo demo para E2E com `WEBAPP_E2E_DEMO=1`.

### Changed
- Fluxo da interface web ajustado de PDFs/ZIP para processamento de imagem de extrato de dividendos.
- Teste E2E atualizado para sincronização por estado determinístico da UI e captura de `webapp_sheets.png`.
- Documentação (`README.md` e `docs/QUICKSTART.md`) atualizada com forma de execução e pré-requisito de OCR (Tesseract).

### Fixed
- Correção de erro de JavaScript na página causada por escape inválido na montagem de texto tabulado, que impedia o submit no fluxo E2E.

## [1.4.1] - 2026-05-14

### Added
- Autoabertura de navegador ao subir o `webapp`.
- Endpoint e botão de encerramento da aplicação via interface.

## [1.4.0] - 2026-05-13

### Added
- Barra de progresso por arquivo na interface web e endpoints de job assíncrono.
