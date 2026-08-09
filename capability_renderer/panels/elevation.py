from __future__ import annotations

from PIL import ImageDraw

from .. import graphics
from ..geometry import PANEL_BOXES


def render(img, draw: ImageDraw.ImageDraw, cfg: dict, metrics: dict, theme: dict, **_) -> ImageDraw.ImageDraw:
    box = PANEL_BOXES["elevation"]
    graphics.rounded_panel(draw, box, 18, theme["panel"], theme["blue"], 2)
    graphics.text(draw, (802, 1222), "ELEVATION", 20, theme["blue"], True)

    draw.line((972, 1246, 990, 1218, 1008, 1246), fill=theme["blue"], width=3)
    draw.line((990, 1246, 1012, 1226, 1034, 1246), fill=theme["blue"], width=3)

    graphics.text(draw, (802, 1284), "ELEVATION GAIN", 16, theme["muted"])
    graphics.text(draw, (802, 1326), cfg.get("elevation_gain", "—"), 31, theme["white"], True)
    graphics.divider(draw, (802, 1370, 1038, 1370), theme["blue"], 1)
    graphics.text(draw, (802, 1402), "MAX ELEVATION", 16, theme["muted"])
    graphics.text(draw, (802, 1444), cfg.get("max_elevation", "—"), 31, theme["white"], True)
    return draw
