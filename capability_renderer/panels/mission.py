from __future__ import annotations

from PIL import ImageDraw

from .. import graphics
from ..geometry import PANEL_BOXES
from ..layout import fit_single_line, stack_blocks

# Title and subtitle are single-line labels drawn without any wrap —
# a long AI-generated mission name/subtitle just kept drawing past the
# panel's right edge (612) with nothing to clip it, and once it
# crossed into the assessment panel's box (628-1066) the tail was only
# hidden where assessment's own background happened to paint over it,
# leaving a stray fragment visible past x=1066. Shrinking the font to
# fit (rather than wrapping to a second line) avoids having to also
# push SUCCESS DEFINITION's fixed start_y down to match.
TITLE_MAX_WIDTH = 520
SUBTITLE_MAX_WIDTH = 520


def render(img, draw: ImageDraw.ImageDraw, cfg: dict, metrics: dict, theme: dict, **_) -> ImageDraw.ImageDraw:
    box = PANEL_BOXES["mission"]
    graphics.rounded_panel(draw, box, 18, theme["panel"], theme["blue"], 2)

    graphics.text(draw, (44, 160), "MISSION", 21, theme["blue"], True)

    title, title_size = fit_single_line(str(cfg["mission"]), TITLE_MAX_WIDTH, 34, min_size=20, bold=True, condensed=True)
    graphics.text(draw, (44, 202), title, title_size, theme["white"], True, condensed=True)

    subtitle, subtitle_size = fit_single_line(str(cfg.get("mission_subtitle", "")), SUBTITLE_MAX_WIDTH, 22, min_size=14, bold=True)
    graphics.text(draw, (44, 246), subtitle, subtitle_size, theme["blue"], True)

    graphics.text(draw, (44, 296), "SUCCESS DEFINITION", 20, theme["blue"], True)

    items = cfg.get("success_definition", [])[:4]
    blocks = stack_blocks(items, x=72, start_y=334, width=500, size=18, max_lines_per_item=2, block_gap=5)
    for item, block in zip(items, blocks):
        graphics.text(draw, (46, block.y), "•", 22, theme["white"], True)
        graphics.wrapped_text(draw, block, theme["white"])
    return draw
