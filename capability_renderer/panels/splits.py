from __future__ import annotations

from PIL import ImageDraw

from .. import graphics
from ..geometry import PANEL_BOXES
from ..metrics import split_rows


def _format_pace(seconds):
    if seconds is None:
        return "—"
    minutes = int(seconds // 60)
    secs = int(round(seconds - minutes * 60))
    if secs == 60:
        minutes += 1
        secs = 0
    return f"{minutes}:{secs:02d}"


def render(img, draw: ImageDraw.ImageDraw, cfg: dict, metrics: dict, theme: dict, points=None, **_) -> ImageDraw.ImageDraw:
    box = PANEL_BOXES["splits"]
    graphics.rounded_panel(draw, box, 18, theme["panel"], theme["blue"], 2)
    graphics.text(draw, (40, 1222), "SPLITS", 20, theme["blue"], True)

    for label, x in [("MI", 42), ("PACE", 124), ("ELEV", 220), ("HR", 317)]:
        graphics.text(draw, (x, 1262), label, 15, theme["muted"])
    graphics.divider(draw, (40, 1290, 382, 1290), theme["line"], 1)

    rows = cfg.get("splits") or (split_rows(points) if points else [])
    y = 1315
    for row in rows[:4]:
        graphics.text(draw, (42, y), row["label"], 17, theme["white"])
        pace = row["pace"] if isinstance(row.get("pace"), str) else _format_pace(row.get("pace"))
        graphics.text(draw, (124, y), pace, 17, theme["white"])
        elev_value = row.get("elev")
        elev = elev_value if isinstance(elev_value, str) else ("—" if elev_value is None else f"{elev_value:+.0f} ft")
        graphics.text(draw, (220, y), elev, 17, theme["white"])
        hr_value = row.get("hr")
        hr = hr_value if isinstance(hr_value, str) else ("—" if hr_value is None else f"{hr_value} bpm")
        graphics.text(draw, (382, y), hr, 17, theme["white"], anchor="ra")
        y += 48
    return draw
