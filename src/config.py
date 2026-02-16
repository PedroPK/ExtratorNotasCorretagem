#!/usr/bin/env python3
"""
Módulo de Configuração - Carrega e gerencia configurações da aplicação
"""

import os
from pathlib import Path

class ConfigManager:
    """Gerenciador de configurações da aplicação"""
    
    # Configurações padrão
    DEFAULT_CONFIGS = {
        'pdf.password': '',
        'logging.level': 'INFO',
        'output.format': 'csv',
        'input.folder': '../resouces/inputNotasCorretagem',
        'output.folder': '../resouces/output',
        'logs.folder': '../resouces/output/logs'
    }
    
    def __init__(self, config_file='application.properties'):
        """
        Inicializa o gerenciador de configurações
        
        Args:
            config_file: Caminho para o arquivo de propriedades
        """
        self.configs = self.DEFAULT_CONFIGS.copy()
        self.config_file = config_file
        
        if os.path.exists(config_file):
            self._load_from_file(config_file)
    
    def _load_from_file(self, config_file):
        """Carrega configurações de um arquivo .properties"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    # Remove comentários e espaços em branco
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '=' in line:
                        key, value = line.split('=', 1)
                        self.configs[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️  Erro ao carregar {config_file}: {str(e)}")
    
    def get(self, key, default=None):
        """Obtém uma configuração"""
        return self.configs.get(key, default or self.DEFAULT_CONFIGS.get(key))
    
    def set(self, key, value):
        """Define uma configuração"""
        self.configs[key] = value
    
    def get_pdf_password(self):
        """Obtém a senha para PDFs protegidos"""
        password = self.get('pdf.password', '')
        return password if password else None
    
    def get_logging_level(self):
        """Obtém o nível de log"""
        return self.get('logging.level', 'INFO')
    
    def get_output_format(self):
        """Obtém o formato de saída"""
        return self.get('output.format', 'csv')
    
    def get_input_folder(self):
        """Obtém a pasta de entrada"""
        return self.get('input.folder')
    
    def get_output_folder(self):
        """Obtém a pasta de saída"""
        return self.get('output.folder')
    
    def get_logs_folder(self):
        """Obtém a pasta de logs"""
        return self.get('logs.folder')
    
    def resolve_path(self, relative_path):
        """
        Resolve um caminho relativo para absoluto
        
        Args:
            relative_path: Caminho relativo
            
        Returns:
            Caminho absoluto resolvido
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, relative_path)


# Instância global de configuração
_config_instance = None

def get_config():
    """Obtém a instância global de configuração"""
    global _config_instance
    if _config_instance is None:
        # Tenta encontrar application.properties
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'application.properties')
        
        # Se não encontrar, tenta um nível acima
        if not os.path.exists(config_path):
            config_path = os.path.join(os.path.dirname(script_dir), 'application.properties')
        
        _config_instance = ConfigManager(config_path if os.path.exists(config_path) else None)
    
    return _config_instance
