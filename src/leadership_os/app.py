"""KivyMD Application class for Leadership OS.

This module will be expanded in Phase 3 to include the full UI.
For now, it serves as a placeholder entry point.
"""

from __future__ import annotations

import sys


def main() -> None:
    """Launch Leadership OS (KivyMD GUI version)."""
    # Phase 3+ will initialize KivyMD app here
    # For now, delegate to the CLI entry point
    from leadership_os.__main__ import main as cli_main
    cli_main()


if __name__ == "__main__":
    main()
