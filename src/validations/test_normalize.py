#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/src')

import re
import os
import zipfile
from config import get_config

def normalize_description(desc: str) -> str:
    """Test version with logging"""
    if not desc:
        return None
    
    s = desc.strip()
    print(f"1. Input: {repr(s)}")
    
    # Normaliza espaços
    s = re.sub(r"\s+", " ", s)
    print(f"2. After space normalize: {repr(s)}")
    
    # Remove prefixos numéricos tipo '1-' ou '01 -'
    s = re.sub(r"^\s*\d+[\-\s]*", "", s)
    print(f"3. After numeric prefix: {repr(s)}")
    
    # Remove "V FRACIONARIO"
    s = re.sub(r"^V(?:\s+FRACIONARIO|\s+FRACIONÁRIO)\b[\s]*", "", s, flags=re.IGNORECASE)
    print(f"4. After V FRACIONARIO: {repr(s)}")
    
    return s

# Test normalize
test_inputs = [
    "1-BOVESPA C FRACIONARIO SUZANO PAPEL ON NM 1 40,00 40,00 D",
    "V FRACIONARIO CEMIG PN N1",
    "EMBRAER ON NM"
]

for inp in test_inputs:
    print(f"\n=== Testing: {inp} ===")
    result = normalize_description(inp)
    print(f"Result: {repr(result)}\n")
