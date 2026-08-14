from __future__ import annotations

from PIL import ImageDraw

from .. import graphics
from ..geometry import PANEL_BOXES


def render(img, draw: ImageDraw.ImageDraw, cfg: dict, metrics: dict, theme: dict, offset: int = 0, **_) -> ImageDraw.ImageDraw:
    box = PANEL_BOXES["recovery"]
    graphics.rounded_panel(draw, box, 18, theme["panel"], theme["blue"], 2)

    graphics.text(draw, (448, 1222 + offset), "♡", 36, theme["blue"])
    graphics.text(draw, (500, 1226 + offset), "HEART RATE RECOVERY", 18, theme["blue"], True)

    recovery = metrics.get("hr_recovery", {})
    if not recovery.get("available"):
        # No external reading was supplied (e.g. Huawei Health) —
        # show that plainly rather than falling back to the locked
        # design's old placeholder numbers (145/115/-17/-30), which
        # rendered as if they were real data for any session that
        # didn't have a recovery reading at all.
        graphics.text(draw, (466, 1300 + offset), "No recovery data", 17, theme["muted"], True)
        graphics.text(draw, (466, 1326 + offset), "supplied for this", 15, theme["muted"])
        graphics.text(draw, (466, 1346 + offset), "session.", 15, theme["muted"])
        return draw

    graphics.text(draw, (466, 1282 + offset), "Start/End", 15, theme["muted"])
    graphics.text(draw, (466, 1318 + offset), f"{recovery['start']} / {recovery['end']} bpm", 23, theme["white"], True)

    graphics.text(draw, (462, 1378 + offset), "1 MIN", 16, theme["blue"], True)
    graphics.text(draw, (620, 1378 + offset), "2 MIN", 16, theme["blue"], True)
    graphics.divider(draw, (458, 1410 + offset, 724, 1410 + offset), theme["line"], 1)
    graphics.text(draw, (462, 1436 + offset), f"{recovery['one_min']} bpm", 25, theme["white"], True)
    graphics.text(draw, (620, 1436 + offset), f"{recovery['two_min']} bpm", 25, theme["green"], True)
    return draw
