from __future__ import annotations

from PIL import ImageDraw

from .. import graphics
from ..geometry import PANEL_BOXES
from ..theme import CARD_LAYOUT_VERSION, MASTER_LOGO_PATH


def render(img, draw: ImageDraw.ImageDraw, cfg: dict, metrics: dict, theme: dict, **_) -> ImageDraw.ImageDraw:
    box = PANEL_BOXES["header"]
    graphics.rounded_panel(draw, box, 18, theme["panel"], theme["line"], 2)
    graphics.logo(img, (64, 65), 35, theme, asset_path=MASTER_LOGO_PATH, opacity=235, gold=True)
    draw = ImageDraw.Draw(img)

    graphics.text(draw, (112, 34), "CAPABILITY ENGINE", 38, theme["white"], True, condensed=True)
    graphics.text(draw, (112, 78), f"QUALITY SESSION  •  SNAPSHOT RENDERER v{CARD_LAYOUT_VERSION}", 16, theme["gold"], True)
    graphics.text(draw, (1034, 39), str(cfg["date"]).upper(), 15, theme["muted"], anchor="ra")
    graphics.text(draw, (1034, 73), cfg["report_id"], 15, theme["muted"], anchor="ra")
    return draw
