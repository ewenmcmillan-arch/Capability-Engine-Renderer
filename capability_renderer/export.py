"""export.py — turn a finished canvas into an output file.

Owns: PNG export today; PDF and SVG are on the v1.5 roadmap
(theme engine, SVG export) and stubbed here so render.py's
data-flow (panels -> graphics -> export -> PNG/PDF/SVG) already has
the seam, even though only PNG is implemented yet.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image


def export_png(image: Image.Image, output_path: str | Path, quality: int = 95) -> Path:
    output_path = Path(output_path)
    image.convert("RGB").save(output_path, quality=quality)
    return output_path


def export_pdf(image: Image.Image, output_path: str | Path) -> Path:
    raise NotImplementedError("PDF export is planned for v1.5 (theme engine, SVG export)")


def export_svg(layout_plan, theme, output_path: str | Path) -> Path:
    raise NotImplementedError("SVG export is planned for v1.5 — requires panels to emit vector primitives, not just draw onto a raster canvas")
