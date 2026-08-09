from __future__ import annotations

from PIL import ImageDraw

from .. import graphics
from ..geometry import PANEL_BOXES
from ..layout import stack_blocks


def render(img, draw: ImageDraw.ImageDraw, cfg: dict, metrics: dict, theme: dict, **_) -> ImageDraw.ImageDraw:
    box = PANEL_BOXES["mission"]
    graphics.rounded_panel(draw, box, 18, theme["panel"], theme["blue"], 2)

    graphics.text(draw, (44, 160), "MISSION", 21, theme["blue"], True)
    graphics.text(draw, (44, 202), cfg["mission"], 34, theme["white"], True, condensed=True)
    graphics.text(draw, (44, 246), cfg.get("mission_subtitle", ""), 22, theme["blue"], True)
    graphics.text(draw, (44, 296), "SUCCESS DEFINITION", 20, theme["blue"], True)

    items = cfg.get("success_definition", [])[:4]
    blocks = stack_blocks(items, x=72, start_y=334, width=500, size=18, max_lines_per_item=2, block_gap=5)
    for item, block in zip(items, blocks):
        graphics.text(draw, (46, block.y), "•", 22, theme["white"], True)
        graphics.wrapped_text(draw, block, theme["white"])
    return draw
