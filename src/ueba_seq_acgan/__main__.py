"""Command-line entry point for the local UEBA dashboard."""

import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from ueba_seq_acgan.dashboard import main

if __name__ == "__main__":
    main()
