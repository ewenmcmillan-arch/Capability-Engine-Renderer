from __future__ import annotations

from PIL import ImageDraw

from .. import graphics
from ..geometry import PANEL_BOXES


def render(img, draw: ImageDraw.ImageDraw, cfg: dict, metrics: dict, theme: dict, offset: int = 0, **_) -> ImageDraw.ImageDraw:
    box = PANEL_BOXES["elevation"]
    graphics.rounded_panel(draw, box, 18, theme["panel"], theme["blue"], 2)
    graphics.text(draw, (802, 1222 + offset), "ELEVATION", 20, theme["blue"], True)

    draw.line((972, 1246 + offset, 990, 1218 + offset, 1008, 1246 + offset), fill=theme["blue"], width=3)
    draw.line((990, 1246 + offset, 1012, 1226 + offset, 1034, 1246 + offset), fill=theme["blue"], width=3)

    # Computed from the GPX (metrics.elevation_summary), not config text —
    # elevation is derivable from the track in principle, unlike HR
    # recovery, so there's no legitimate case for a human-supplied
    # override here. "—" only when the GPX carries no elevation data
    # at all (elevation_summary returns None for both fields then).
    elevation = metrics.get("elevation", {})
    gain_ft = elevation.get("gain_ft")
    max_ft = elevation.get("max_ft")
    gain_text = "—" if gain_ft is None else f"{gain_ft:.0f} ft"
    max_text = "—" if max_ft is None else f"{max_ft:.0f} ft"

    graphics.text(draw, (802, 1284 + offset), "ELEVATION GAIN", 16, theme["muted"])
    graphics.text(draw, (802, 1326 + offset), gain_text, 31, theme["white"], True)
    graphics.divider(draw, (802, 1370 + offset, 1038, 1370 + offset), theme["blue"], 1)
    graphics.text(draw, (802, 1402 + offset), "MAX ELEVATION", 16, theme["muted"])
    graphics.text(draw, (802, 1444 + offset), max_text, 31, theme["white"], True)
    return draw
