#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/pedropk/Downloads/Apps/Development/IDEs/VsWorkspace/ExtratorNotasCorretagem/src')

from config import get_config

cfg = get_config()
input_folder = cfg.get_input_folder()
print(f"Input folder from config: {input_folder}")

resolved = cfg.resolve_path(input_folder)
print(f"Resolved path: {resolved}")

import os
print(f"Folder exists: {os.path.exists(resolved)}")
print(f"Is directory: {os.path.isdir(resolved)}")

if os.path.isdir(resolved):
    print(f"Contents:")
    for f in os.listdir(resolved)[:20]:
        print(f"  - {f}")
