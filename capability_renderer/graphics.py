"""graphics.py — pure drawing.

Owns: every PIL draw call. Rounded panels, text, tables, metric
cards, the route polyline, watermark, logo/crest, progress bars,
icons. Every function here takes coordinates and values that were
already decided by layout.py / geometry.py — nothing in here decides
where anything goes or how text wraps.
"""
from __future__ import annotations

from typing import Iterable, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from . import typography
from .layout import TextBlock

Box = Tuple[int, int, int, int]
Point = Tuple[float, float]


def rounded_panel(draw: ImageDraw.ImageDraw, box: Box, radius: int = 18, fill=None, outline=None, width: int = 2) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text(draw: ImageDraw.ImageDraw, xy: Tuple[float, float], value, size: int, color, bold: bool = False, anchor: Optional[str] = None, condensed: bool = False) -> None:
    draw.text(xy, str(value), fill=color, font=typography.get_font(size, bold, condensed), anchor=anchor)


def wrapped_text(draw: ImageDraw.ImageDraw, block: TextBlock, color) -> int:
    """Draw a pre-wrapped TextBlock (from layout.py). Returns the y
    coordinate immediately below the drawn block."""
    y = block.y
    for line in block.lines:
        text(draw, (block.x, y), line, block.size, color, block.bold, condensed=block.condensed)
        y += block.size + block.line_gap
    return y


def divider(draw: ImageDraw.ImageDraw, xy: Tuple[float, float, float, float], color, width: int = 1) -> None:
    draw.line(xy, fill=color, width=width)


def legend_swatch(draw: ImageDraw.ImageDraw, xy: Tuple[float, float, float, float], color, width: int = 8) -> None:
    draw.line(xy, fill=color, width=width)


def marker(draw: ImageDraw.ImageDraw, centre: Point, radius: float, fill, outline, width: int = 2) -> None:
    cx, cy = centre
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=fill, outline=outline, width=width)


def route_polyline(draw: ImageDraw.ImageDraw, points: Sequence[Point], colours: Sequence, width: int = 8) -> None:
    """Draw a route as a sequence of coloured segments.

    colours[i] is the colour of the segment from points[i] to points[i+1].
    """
    for i in range(min(len(points) - 1, len(colours))):
        draw.line((*points[i], *points[i + 1]), fill=colours[i], width=width, joint="curve")


def grid(target: Image.Image, box: Box, colour, spacing: int = 42, diag_spacing: int = 95, diag_range: Tuple[int, int] = (-240, 360)) -> None:
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", target.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for x in range(x0 + 20, x1, spacing):
        d.line((x, y0, x, y1), fill=colour, width=1)
    for y in range(y0 + 20, y1, spacing):
        d.line((x0, y, x1, y), fill=colour, width=1)
    for offset in range(diag_range[0], diag_range[1], diag_spacing):
        d.line((x0, y1 + offset, x1, y0 + offset), fill=colour, width=1)
    target.alpha_composite(layer)


def crest(target: Image.Image, centre: Point, radius: float, opacity: int = 255, gold: bool = False) -> None:
    """Deterministic circular Capability Engine crest.

    Placeholder brand mark used until real logo assets
    (assets/logos/capability_master.svg / .png) are supplied — see
    validation.py's asset checks, which warn rather than fail when
    those files are absent so this vector fallback can stand in.
    """
    layer = Image.new("RGBA", target.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = centre
    rgb = (216, 181, 91) if gold else (120, 199, 45)
    colour = (*rgb, opacity)
    soft = (*rgb, max(15, int(opacity * 0.58)))
    width = max(2, int(radius) // 18)
    d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=colour, width=width)
    d.ellipse((cx - radius + 8, cy - radius + 8, cx + radius - 8, cy + radius - 8), outline=soft, width=max(1, width // 2))
    peaks = [
        (cx - radius * .58, cy + radius * .16),
        (cx - radius * .18, cy - radius * .34),
        (cx + radius * .02, cy - radius * .02),
        (cx + radius * .28, cy - radius * .45),
        (cx + radius * .62, cy + radius * .18),
    ]
    d.line(peaks, fill=colour, width=width, joint="curve")
    d.arc((cx - radius * .55, cy - radius * .05, cx + radius * .55, cy + radius * .66), 18, 165, fill=soft, width=max(2, width - 1))
    target.alpha_composite(layer)


def logo(target: Image.Image, centre: Point, radius: float, theme_colours: dict, asset_path=None, opacity: int = 255, gold: bool = False) -> None:
    """Draw the brand mark: real asset if available, crest() fallback otherwise."""
    if asset_path is not None and asset_path.exists():
        art = Image.open(asset_path).convert("RGBA")
        size = int(radius * 2)
        art = art.resize((size, size))
        target.alpha_composite(art, (int(centre[0] - radius), int(centre[1] - radius)))
        return
    crest(target, centre, radius, opacity, gold)


def progress_ring_label(draw: ImageDraw.ImageDraw, box: Box, colour, percent_text: str, lines: Iterable[str], text_colour) -> None:
    """The percent-complete box in the trace panel (rounded box + big % + caption lines)."""
    rounded_panel(draw, box, 14, "#02070c", colour, 2)
    cx = (box[0] + box[2]) / 2
    text(draw, (cx, box[1] + 28), percent_text, 42, colour, True, anchor="ma")
    y = box[1] + 75
    for line in lines:
        text(draw, (cx, y), line, 16, text_colour, anchor="ma")
        y += 23


def watermark(target: Image.Image, centre: Point, radius: float, opacity: int = 30) -> None:
    """Low-opacity crest behind panel text, per the locked design's watermark rule."""
    crest(target, centre, radius, opacity=opacity, gold=True)
