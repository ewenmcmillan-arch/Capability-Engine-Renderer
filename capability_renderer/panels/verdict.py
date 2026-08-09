from __future__ import annotations

from PIL import ImageDraw

from .. import graphics
from ..geometry import PANEL_BOXES
from ..layout import wrap_text


def render(img, draw: ImageDraw.ImageDraw, cfg: dict, metrics: dict, theme: dict, **_) -> ImageDraw.ImageDraw:
    box = PANEL_BOXES["verdict"]
    graphics.rounded_panel(draw, box, 18, theme["panel"], theme["green"], 2)

    graphics.text(draw, (700, 550), "COACH'S VERDICT", 21, theme["green"], True)
    graphics.text(draw, (700, 605), "STRENGTH", 17, theme["green"], True)

    y = 638
    for line in wrap_text(cfg["strength"], 330, 26, bold=True, max_lines=2):
        graphics.text(draw, (700, y), line, 26, theme["white"], True)
        y += 26 + 6
    graphics.divider(draw, (700, 696, 1036, 696), theme["green"], 2)

    graphics.text(draw, (700, 728), "NEXT FOCUS", 17, theme["green"], True)
    y = 762
    for line in wrap_text(cfg["next_focus"], 330, 20, max_lines=4):
        graphics.text(draw, (700, y), line, 20, theme["white"])
        y += 20 + 8
    graphics.divider(draw, (700, y + 18, 1036, y + 18), theme["green"], 2)

    graphics.text(draw, (700, y + 52), "NOTES", 17, theme["green"], True)
    notes = cfg.get("coach_notes", "Cadence solid. Heart rate well managed on the climbs. Good finish.")
    ny = y + 86
    for line in wrap_text(notes, 330, 18, max_lines=5):
        graphics.text(draw, (700, ny), line, 18, theme["white"])
        ny += 18 + 7
    return draw
