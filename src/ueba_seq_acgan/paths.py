"""Resource resolution helper for development and PyInstaller bundled execution."""

from __future__ import annotations

import sys
from pathlib import Path


def get_base_dir() -> Path:
    """Return base directory: sys._MEIPASS for PyInstaller onefile or workspace root."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    # Default to current working directory or directory containing src
    current = Path.cwd()
    if (current / "src" / "ueba_seq_acgan").exists() or (current / "configs").exists():
        return current
    pkg_dir = Path(__file__).resolve().parent.parent.parent
    return pkg_dir


def resolve_resource(rel_path: str | Path) -> Path:
    """Resolve a relative resource path against the base directory."""
    path_obj = Path(rel_path)
    if path_obj.is_absolute() and path_obj.exists():
        return path_obj

    base = get_base_dir()
    candidate = base / path_obj
    if candidate.exists():
        return candidate

    # Fallback to local cwd if different
    cwd_candidate = Path.cwd() / path_obj
    if cwd_candidate.exists():
        return cwd_candidate

    return candidate
