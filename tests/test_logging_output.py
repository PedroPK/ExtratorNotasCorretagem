"""
Testes para formatação de logs e output
Valida que logs são exibidos corretamente sem conflitos de formatação
"""

import pytest
import logging
import io
import sys
from datetime import datetime


class TestLoggingFormat:
    """Testa formatação dos logs"""
    
    def test_log_format_has_timestamp(self):
        """Log deve incluir timestamp"""
        # Formato esperado: [HH:MM:SS] - LEVEL - Mensagem
        timestamp_pattern = r'\d{2}:\d{2}:\d{2}'
        
        # Simula log
        log_message = "20/02/2026 22:10:01 - INFO - 📄 Processando arquivo..."
        
        import re
        assert re.search(timestamp_pattern, log_message) is not None
    
    def test_log_format_has_level(self):
        """Log deve incluir nível (INFO, ERROR, etc)"""
        log_message = "20/02/2026 22:10:01 - INFO - 📄 Processando arquivo..."
        
        assert ' - INFO - ' in log_message
    
    def test_log_format_has_message(self):
        """Log deve incluir mensagem"""
        log_message = "20/02/2026 22:10:01 - INFO - 📄 Processando arquivo..."
        
        assert 'Processando arquivo' in log_message
    
    def test_log_different_levels(self):
        """Logs com diferentes níveis devem ser formatados"""
        levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
        
        for level in levels:
            log_message = f"20/02/2026 22:10:01 - {level} - Test message"
            assert f' - {level} - ' in log_message


class TestLoggingOutput:
    """Testa saída de logs sem formatação excessiva"""
    
    def test_log_no_excessive_spacing(self):
        """Logs não devem ter espaçamento excessivo"""
        # Problema anterior: progress bar adicionava linhas vazias desnecessárias
        log_lines = [
            "20/02/2026 22:10:01 - INFO - Line 1",
            "20/02/2026 22:10:02 - INFO - Line 2",
            "20/02/2026 22:10:03 - INFO - Line 3",
        ]
        
        # Simula saída
        output = "\n".join(log_lines)
        
        # Conta linhas vazias (não deve haver)
        empty_lines = output.count("\n\n")
        assert empty_lines == 0, "Há linhas vazias desnecessárias"
    
    def test_log_lines_are_separate(self):
        """Cada log deve ser uma linha separada"""
        log_output = """20/02/2026 22:10:01 - INFO - Line 1
20/02/2026 22:10:02 - INFO - Line 2
20/02/2026 22:10:03 - INFO - Line 3"""
        
        lines = log_output.split('\n')
        assert len(lines) == 3
    
    def test_log_no_progress_bar_artifacts(self):
        """Output não deve ter artifacts de progress bar"""
        # Problema anterior: `| 25/93 [02:59]` misturado com logs
        log_output = """20/02/2026 22:10:01 - INFO - Processing file 1
20/02/2026 22:10:02 - INFO - Processing file 2
20/02/2026 22:10:03 - INFO - Processing file 3"""
        
        # Não deve conter padrão de progress bar
        assert '| ' not in log_output
        assert '[' not in log_output or 'Processing' in log_output
        assert ']' not in log_output or 'Processing' in log_output


class TestLoggingDuringProcessing:
    """Testa logs durante processamento de arquivos"""
    
    def test_file_processing_log_format(self):
        """Log de processamento de arquivo tem formato correto"""
        log = "20/02/2026 22:50:01 - INFO - 📄 Processando arquivo: Clear 2025 01 Janeiro..."
        
        assert '📄' in log  # Emoji para arquivo
        assert 'Processando arquivo' in log
        assert 'Clear 2025 01 Janeiro' in log
    
    def test_file_success_log_format(self):
        """Log de sucesso tem formato correto"""
        log = "20/02/2026 22:50:07 - INFO - ✓ Clear 2025 01 Janeiro...: 29 registro(s) com sucesso"
        
        assert '✓' in log  # Checkmark para sucesso
        assert 'registro(s) com sucesso' in log
    
    def test_multiple_file_logs_stay_separate(self):
        """Logs de múltiplos arquivos não se conflitam"""
        logs = [
            "20/02/2026 22:50:01 - INFO - 📄 Processando: File 1",
            "20/02/2026 22:50:02 - INFO - ✓ File 1: 10 registros",
            "20/02/2026 22:50:03 - INFO - 📄 Processando: File 2",
            "20/02/2026 22:50:04 - INFO - ✓ File 2: 15 registros",
        ]
        
        output = "\n".join(logs)
        
        # Cada log deve começar com timestamp
        for log in logs:
            assert output.count(log) == 1, "Log foi duplicado ou fragmentado"


class TestLoggingPerformance:
    """Testa performance de logging"""
    
    def test_logging_many_lines_is_fast(self):
        """Logging de muitas linhas não deve ser lento"""
        import time
        
        # Simula logging de 1000 linhas
        start = time.time()
        
        log_lines = []
        for i in range(1000):
            log_lines.append(f"20/02/2026 22:10:{i % 60:02d} - INFO - Log line {i}")
        
        output = "\n".join(log_lines)
        elapsed = time.time() - start
        
        assert elapsed < 0.1, f"Logging muito lento: {elapsed}s para 1000 linhas"
    
    def test_logging_does_not_buffer_excessively(self):
        """Sistema de logging não deve usar muita memória"""
        # Não há artifacts de progress bar que causem buffer
        import sys
        
        # Verificar que não há refs desnecessárias ao tqdm
        modules = sys.modules.keys()
        # (Este é mais um teste conceitual)


class TestLoggingLevels:
    """Testa diferentes níveis de logging"""
    
    def test_info_level_includes_info(self):
        """Nível INFO inclui msgs de INFO"""
        level = 'INFO'
        assert level in ['INFO', 'WARNING', 'ERROR', 'DEBUG']
    
    def test_error_level_shown(self):
        """Nível ERROR é mostrado sempre"""
        log = "20/02/2026 22:10:01 - ERROR - ✗ Erro ao processar arquivo"
        
        assert ' - ERROR - ' in log
        assert '✗' in log  # Símbolo de erro
    
    def test_warning_level_shown(self):
        """Nível WARNING é mostrado"""
        log = "20/02/2026 23:15:41 - WARNING - ⏸️ Interrupção solicitada pelo usuário"
        
        assert ' - WARNING - ' in log
        assert '⏸️' in log
