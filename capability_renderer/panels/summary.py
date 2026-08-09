from __future__ import annotations

from PIL import ImageDraw

from .. import graphics
from ..geometry import PANEL_BOXES, metric_cell_box


def render(img, draw: ImageDraw.ImageDraw, cfg: dict, metrics: dict, theme: dict, **_) -> ImageDraw.ImageDraw:
    box = PANEL_BOXES["metrics_strip"]
    graphics.rounded_panel(draw, box, 18, theme["panel"], theme["blue"], 2)

    cells = [
        ("DISTANCE", cfg["distance"], "mi"),
        ("TIME", cfg["time"], cfg.get("time_unit", "moving time")),
        ("AVG / MAX HR", cfg["avg_max_hr"], "bpm"),
        ("BEST ¼ MILE", cfg["best_quarter"], "mm:ss"),
        ("MISSION PACE", cfg["mission_pace_value"], cfg["mission_pace_unit"]),
    ]
    for i, (label, value, unit) in enumerate(cells):
        x0, y0, x1, y1 = metric_cell_box(i, len(cells), box)
        if i:
            graphics.divider(draw, (x0, box[1] + 18, x0, box[3] - 18), theme["line"], 1)
        cx = (x0 + x1) / 2
        graphics.text(draw, (cx, box[1] + 24), label, 16, theme["blue"], True, anchor="ma")
        graphics.text(draw, (cx, box[1] + 68), value, 34, theme["white"], True, anchor="ma", condensed=True)
        graphics.text(draw, (cx, box[1] + 115), unit, 15, theme["white"], anchor="ma")
    return draw
