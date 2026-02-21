#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/src')

from collect_asset_descriptions import collect_descriptions_from_path

try:
    descs = collect_descriptions_from_path(year=2018)
    print(f"Descrições encontradas: {len(descs)}")
    for d in descs[:20]:
        print(f"  - {d}")
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()
