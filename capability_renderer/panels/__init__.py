"""panels/ — one renderer module per card section.

Every panel module exposes a single `render(img, draw, cfg, metrics,
theme, **kwargs) -> ImageDraw.ImageDraw` function. It draws its own
section and returns a (possibly refreshed) ImageDraw handle, because
compositing a transparency layer onto `img` (used for the crest and
route grid) invalidates the previous draw handle in PIL.

Adding a new card section — e.g. a nutrition panel — means adding
panels/nutrition.py with that same signature and registering it in
render.py's panel list. Nothing else changes.
"""
from . import header, mission, assessment, trace, verdict, summary, splits, recovery, elevation, footer

__all__ = [
    "header", "mission", "assessment", "trace", "verdict",
    "summary", "splits", "recovery", "elevation", "footer",
]
