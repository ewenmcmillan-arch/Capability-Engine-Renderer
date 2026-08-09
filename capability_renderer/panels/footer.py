from __future__ import annotations

from PIL import ImageDraw

from .. import graphics
from ..geometry import PANEL_BOXES
from ..theme import CARD_LAYOUT_VERSION


def render(img, draw: ImageDraw.ImageDraw, cfg: dict, metrics: dict, theme: dict, **_) -> ImageDraw.ImageDraw:
    box = PANEL_BOXES["footer"]
    graphics.rounded_panel(draw, box, 18, theme["panel"], theme["line"], 2)
    graphics.crest(img, (58, 1563), 27, 225, gold=True)
    draw = ImageDraw.Draw(img)

    graphics.text(draw, (96, 1542), "CAPABILITY ENGINE", 17, theme["white"], True)
    graphics.text(draw, (96, 1573), "VERIFIED ANALYSIS", 17, theme["green"], True)
    graphics.text(draw, (540, 1565), "CAPABILITY SNAPSHOT", 20, theme["gold"], True, anchor="ma")
    graphics.text(draw, (1034, 1543), cfg["report_id"], 14, theme["muted"], anchor="ra")
    graphics.text(draw, (1034, 1571), "Actual GPX-derived course trace", 13, theme["blue"], anchor="ra")
    graphics.text(draw, (1034, 1591), f"Renderer v{CARD_LAYOUT_VERSION}", 12, theme["muted"], anchor="ra")
    return draw
