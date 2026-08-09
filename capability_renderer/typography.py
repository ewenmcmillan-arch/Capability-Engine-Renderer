"""typography.py — everything about fonts.

Owns: loading fonts from disk with graceful fallback, caching loaded
fonts so repeated calls are cheap, and measuring text width/height.
Does not decide *where* text goes (layout.py) or draw it (graphics.py).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from PIL import ImageFont

# Bundled-font search path — checked before falling back to system fonts.
BUNDLED_FONT_DIR = Path(__file__).resolve().parent / "assets" / "fonts"

_SYSTEM_CANDIDATES = {
    (True, True): [   # bold, condensed
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSansNarrow-Bold.ttf",
    ],
    (False, True): [  # regular, condensed
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSansNarrow-Regular.ttf",
    ],
    (True, False): [  # bold, standard
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ],
    (False, False): [  # regular, standard
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ],
}


def _bundled_candidates(bold: bool, condensed: bool) -> List[str]:
    stem = "Bold" if bold else "Regular"
    weight = "Condensed" if condensed else "Standard"
    return [str(BUNDLED_FONT_DIR / f"{weight}-{stem}.ttf")]


@lru_cache(maxsize=None)
def get_font(size: int, bold: bool = False, condensed: bool = False):
    """Return a cached PIL font for (size, bold, condensed).

    Search order: bundled asset font -> matching system font ->
    next-best system font (condensed falls back to standard) ->
    PIL's built-in default as a last resort so rendering never
    crashes purely for a missing font file.
    """
    candidates: List[str] = _bundled_candidates(bold, condensed)
    if condensed:
        candidates += _SYSTEM_CANDIDATES[(bold, True)]
    candidates += _SYSTEM_CANDIDATES[(bold, False)]

    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def text_width(text: str, font) -> float:
    """Measure rendered width of text in the given font.

    Uses PIL's font.getlength when available (no draw context
    needed), falling back to a getbbox-based estimate for very old
    Pillow versions.
    """
    text = str(text)
    if hasattr(font, "getlength"):
        return font.getlength(text)
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def line_height(size: int) -> int:
    """A simple, predictable line height for stacking text blocks."""
    return int(size * 1.0)
