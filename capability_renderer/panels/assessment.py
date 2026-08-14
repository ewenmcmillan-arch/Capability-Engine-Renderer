from __future__ import annotations

from PIL import ImageDraw

from .. import graphics
from ..geometry import PANEL_BOXES
from ..layout import wrap_text
from ..theme import WATERMARK_DARK_PATH


def render(img, draw: ImageDraw.ImageDraw, cfg: dict, metrics: dict, theme: dict, **_) -> ImageDraw.ImageDraw:
    box = PANEL_BOXES["assessment"]
    graphics.rounded_panel(draw, box, 18, theme["panel"], theme["orange"], 2)
    graphics.watermark(img, (460, 314), 116, opacity=30, asset_path=WATERMARK_DARK_PATH)
    draw = ImageDraw.Draw(img)

    graphics.text(draw, (658, 160), "MISSION ASSESSMENT", 21, theme["orange"], True)
    graphics.text(draw, (658, 202), cfg["score"], 82, theme["orange"], True, condensed=True)
    graphics.text(draw, (862, 267), "/100", 34, theme["orange"], True)
    graphics.text(draw, (658, 302), str(cfg["status"]).upper(), 22, theme["orange"], True)
    graphics.divider(draw, (658, 340, 1036, 340), theme["orange"], 2)
    graphics.text(draw, (658, 360), "REASON", 18, theme["orange"], True)

    y = 394
    # max_lines=12 (not 6) — real AI-generated "2-3 sentence" reasons
    # routinely run to 8-11 lines at this panel's 350px width, and the
    # tighter cap was truncating mid-word ("...so pace at a fixe...").
    # Matches geometry._assessment_extra_height()'s own wrap_text()
    # call, so the panel grows to fit exactly what's about to be drawn
    # here rather than truncating text a taller box already made room
    # for.
    for line in wrap_text(cfg["reason"], 350, 18, max_lines=12):
        graphics.text(draw, (658, y), line, 18, theme["white"])
        y += 18 + 7
    return draw
