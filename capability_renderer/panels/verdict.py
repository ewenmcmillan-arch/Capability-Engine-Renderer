from __future__ import annotations

from PIL import ImageDraw

from .. import graphics
from ..geometry import PANEL_BOXES
from ..layout import lines_that_fit, wrap_text


def render(img, draw: ImageDraw.ImageDraw, cfg: dict, metrics: dict, theme: dict, **_) -> ImageDraw.ImageDraw:
    box = PANEL_BOXES["verdict"]
    graphics.rounded_panel(draw, box, 18, theme["panel"], theme["green"], 2)

    graphics.text(draw, (700, 550), "COACH'S VERDICT", 21, theme["green"], True)
    graphics.text(draw, (700, 605), "STRENGTH", 17, theme["green"], True)

    y = 638
    for line in wrap_text(cfg["strength"], 330, 26, bold=True, max_lines=2):
        graphics.text(draw, (700, y), line, 26, theme["white"], True)
        y += 26 + 6
    # Divider position now derives from where STRENGTH's text actually
    # ended, instead of a hardcoded y=696 — that value only looked right
    # by coincidence for a single-line strength; a two-line strength
    # (e.g. "Beat this route's previous pace") ran its text right up
    # against the divider with no breathing room. +10 gives it space;
    # everything below cascades from this point the same way NEXT FOCUS
    # -> NOTES already did.
    divider1_y = y - 6 + 10
    graphics.divider(draw, (700, divider1_y, 1036, divider1_y), theme["green"], 2)

    graphics.text(draw, (700, divider1_y + 32), "NEXT FOCUS", 17, theme["green"], True)
    y = divider1_y + 66
    for line in wrap_text(cfg["next_focus"], 330, 20, max_lines=4):
        graphics.text(draw, (700, y), line, 20, theme["white"])
        y += 20 + 8
    graphics.divider(draw, (700, y + 18, 1036, y + 18), theme["green"], 2)

    graphics.text(draw, (700, y + 52), "NOTES", 17, theme["green"], True)
    notes = cfg.get("coach_notes", "Cadence solid. Heart rate well managed on the climbs. Good finish.")
    ny = y + 86
    # Available lines depend on how much room STRENGTH/NEXT FOCUS already
    # used above — a fixed max_lines=5 here overflowed the panel's fixed
    # bottom edge (1014) whenever NEXT FOCUS ran to its own max of 4 lines,
    # pushing NOTES lower than a fixed cap accounted for. Budget from the
    # actual remaining space instead, same principle as
    # layout.budget_panel_height().
    line_height = 18 + 7
    max_lines = lines_that_fit(ny, box[3], line_height)
    for line in wrap_text(notes, 330, 18, max_lines=max_lines):
        graphics.text(draw, (700, ny), line, 18, theme["white"])
        ny += line_height
    return draw
