from __future__ import annotations

from PIL import ImageDraw

from .. import graphics
from ..geometry import PANEL_BOXES
from ..layout import wrap_text


def render(img, draw: ImageDraw.ImageDraw, cfg: dict, metrics: dict, theme: dict, **_) -> ImageDraw.ImageDraw:
    box = PANEL_BOXES["assessment"]
    graphics.rounded_panel(draw, box, 18, theme["panel"], theme["orange"], 2)
    graphics.watermark(img, (460, 314), 116, opacity=30)
    draw = ImageDraw.Draw(img)

    graphics.text(draw, (658, 160), "MISSION ASSESSMENT", 21, theme["orange"], True)
    graphics.text(draw, (658, 202), cfg["score"], 82, theme["orange"], True, condensed=True)
    graphics.text(draw, (862, 267), "/100", 34, theme["orange"], True)
    graphics.text(draw, (658, 302), str(cfg["status"]).upper(), 22, theme["orange"], True)
    graphics.divider(draw, (658, 340, 1036, 340), theme["orange"], 2)
    graphics.text(draw, (658, 360), "REASON", 18, theme["orange"], True)

    y = 394
    for line in wrap_text(cfg["reason"], 350, 18, max_lines=4):
        graphics.text(draw, (658, y), line, 18, theme["white"])
        y += 18 + 7
    return draw
