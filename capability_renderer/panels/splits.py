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


# Row spacing/font at the locked v1.2 size — unchanged for the common
# case (≤4 splits: anything up to a 5K-ish run) so existing renders
# stay pixel-identical.
DEFAULT_PITCH = 48
DEFAULT_FONT = 17

# Below this, split text stops being legible — never shrink past it.
MIN_PITCH = 20
MIN_FONT = 12

START_Y = 1315
BOTTOM_MARGIN = 10  # keep the last row clear of the panel's rounded bottom edge


def _fit_rows(count: int, available_height: float) -> tuple[int, float, int]:
    """How many of `count` splits fit in available_height, and at
    what row pitch / font size.

    Shows every row uncapped (the old hardcoded 4-row limit) at the
    default spacing when they fit. Beyond that, shrinks pitch and
    font together to fit more rows in the same fixed panel — down to
    MIN_PITCH, where text stops being legible. If there are still
    more splits than fit even at MIN_PITCH (a half-marathon or
    longer), caps the row count there rather than overflowing into
    the footer panel below.
    """
    if count <= 0:
        return 0, DEFAULT_PITCH, DEFAULT_FONT
    if count * DEFAULT_PITCH <= available_height:
        return count, DEFAULT_PITCH, DEFAULT_FONT

    max_rows = max(1, int(available_height // MIN_PITCH))
    shown = min(count, max_rows)
    pitch = available_height / shown
    font_size = max(MIN_FONT, min(DEFAULT_FONT, int(pitch) - 10))
    return shown, pitch, font_size


def render(img, draw: ImageDraw.ImageDraw, cfg: dict, metrics: dict, theme: dict, points=None, **_) -> ImageDraw.ImageDraw:
    box = PANEL_BOXES["splits"]
    graphics.rounded_panel(draw, box, 18, theme["panel"], theme["blue"], 2)
    graphics.text(draw, (40, 1222), "SPLITS", 20, theme["blue"], True)

    for label, x in [("MI", 42), ("PACE", 124), ("ELEV", 220), ("HR", 317)]:
        graphics.text(draw, (x, 1262), label, 15, theme["muted"])
    graphics.divider(draw, (40, 1290, 382, 1290), theme["line"], 1)

    rows = cfg.get("splits") or (split_rows(points) if points else [])
    available = box[3] - BOTTOM_MARGIN - START_Y
    shown, pitch, font_size = _fit_rows(len(rows), available)

    y = START_Y
    for row in rows[:shown]:
        graphics.text(draw, (42, y), row["label"], font_size, theme["white"])
        pace = row["pace"] if isinstance(row.get("pace"), str) else _format_pace(row.get("pace"))
        graphics.text(draw, (124, y), pace, font_size, theme["white"])
        elev_value = row.get("elev")
        elev = elev_value if isinstance(elev_value, str) else ("—" if elev_value is None else f"{elev_value:+.0f} ft")
        graphics.text(draw, (220, y), elev, font_size, theme["white"])
        hr_value = row.get("hr")
        hr = hr_value if isinstance(hr_value, str) else ("—" if hr_value is None else f"{hr_value} bpm")
        graphics.text(draw, (382, y), hr, font_size, theme["white"], anchor="ra")
        y += pitch
    return draw
