"""Leadership OS — Entry point.

A local-first personal execution system that minimizes cognitive load.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running without `pip install -e .` by adding src/ to the path
_src_dir = str(Path(__file__).resolve().parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from leadership_os.app import main

if __name__ == "__main__":
    main()
