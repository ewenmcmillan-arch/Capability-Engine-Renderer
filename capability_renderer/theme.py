"""theme.py — colour schemes and canvas constants.

Owns: named colour palettes, canvas dimensions, and loading a theme
by name from assets/themes/*.json. Nothing in this module draws or
measures anything; it only supplies values other modules read.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

# Canvas dimensions for the locked v1.2 mission-card layout.
# (Design-locked per Capability_Snapshot_Renderer_Memory_Locked_Baseline.md)
W, H = 1080, 1620

VERSION = "1.4.0-dev"  # renderer package version (distinct from card layout version)
CARD_LAYOUT_VERSION = "1.2"  # the locked visual layout this renderer reproduces

ASSET_DIR = Path(__file__).resolve().parent / "assets"
THEME_DIR = ASSET_DIR / "themes"
LOGO_DIR = ASSET_DIR / "logos"

MASTER_LOGO_PATH = LOGO_DIR / "capability_master.png"
FAVICON_PATH = LOGO_DIR / "favicon.png"
WATERMARK_DARK_PATH = LOGO_DIR / "watermark_dark.png"
WATERMARK_LIGHT_PATH = LOGO_DIR / "watermark_light.png"

# Built-in fallback palette — used if no theme JSON is found on disk.
# This is the exact palette from the locked v1.2 baseline.
DEFAULT_COLORS: Dict[str, str] = {
    "bg": "#02070c",
    "panel": "#06111a",
    "panel_alt": "#07131d",
    "blue": "#2599f3",
    "orange": "#ff970f",
    "green": "#78c72d",
    "white": "#f3f6f8",
    "muted": "#b9c0c7",
    "grey": "#c4c9ce",
    "line": "#52606a",
    "gold": "#d8b55b",
    "grid": "#173044",
    "legend_bg": "#04101a",
}


def load_theme(name: str = "default") -> Dict[str, str]:
    """Load a theme's colour palette by name.

    Looks for assets/themes/<name>.json first; falls back to the
    built-in DEFAULT_COLORS if the file is missing or unreadable so
    rendering never hard-fails purely because a theme asset is absent.
    """
    path = THEME_DIR / f"{name}.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            colours = data.get("colors") or data.get("colours")
            if isinstance(colours, dict):
                merged = dict(DEFAULT_COLORS)
                merged.update(colours)
                return merged
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_COLORS)
