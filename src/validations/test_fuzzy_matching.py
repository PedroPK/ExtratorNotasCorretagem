#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/src')

import re

def _normalize_text_for_comparison(text: str) -> str:
    text = text.upper().strip()
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('-', ' ')
    text = re.sub(r'[^A-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def _extract_words_from_asset_name(text: str) -> set:
    stopwords = {"ON", "PN", "NM", "N1", "N2", "ED", "EDUC", "PREFER", "ORDINARIA"}
    text = _normalize_text_for_comparison(text)
    words = set(text.split())
    significant_words = words - stopwords
    if significant_words:
        return significant_words
    return words

def _fuzzy_match_asset_name(cell_text: str, mapping_name: str) -> bool:
    cell_words = _extract_words_from_asset_name(cell_text)
    mapping_words = _extract_words_from_asset_name(mapping_name)
    
    if not mapping_words:
        return False
    
    common_words = cell_words.intersection(mapping_words)
    match_percentage = len(common_words) / len(mapping_words)
    
    return match_percentage >= 0.70 or len(common_words) >= 2

# Test cases
test_cases = [
    ("SUZANO PAPEL ON NM", "SUZANO ON NM", True),
    ("SUZANO PAPEL ON NM", "SUZANOPAPEL ONNM", True),
    ("SUZANO PAPEL ON NM", "Suzano ON NM", True),
    ("SUZANO PAPEL ON NM", "PETROBRAS ON", False),
    ("1-BOVESPA C FRACIONARIO 01/00 SUZANO PAPEL ON NM", "Suzano ON NM", True),
    ("EMBRAER ON NM", "Embraer ON NM", True),
]

print("Testing fuzzy matching logic:\n")
for cell_text, mapping_name, expected in test_cases:
    result = _fuzzy_match_asset_name(cell_text, mapping_name)
    status = "✓" if result == expected else "✗"
    print(f"{status} Cell: '{cell_text}' vs Map: '{mapping_name}'")
    print(f"   Expected: {expected}, Got: {result}")
    print(f"   Cell words: {_extract_words_from_asset_name(cell_text)}")
    print(f"   Map words: {_extract_words_from_asset_name(mapping_name)}")
    print()
