from __future__ import annotations

from PIL import ImageDraw

from .. import graphics
from ..geometry import PANEL_BOXES, TRACE_LEGEND_BOX, TRACE_PERCENT_BOX, TRACE_ROUTE_BOX, scale_route
from ..metrics import mission_pace_threshold_seconds


def _route_colours(cfg: dict, metrics: dict, paces, theme: dict):
    threshold = mission_pace_threshold_seconds(cfg["mission_pace_threshold"])
    tolerance = int(cfg.get("near_pace_tolerance_seconds", 10))
    colours = []
    for pace in paces:
        if pace is not None and pace <= threshold:
            colours.append(theme["green"])
        elif pace is not None and pace <= threshold + tolerance:
            colours.append(theme["orange"])
        else:
            colours.append(theme["grey"])
    return colours


def _draw_route_markers(draw, route, points, theme):
    from ..geometry import haversine
    import math
    start, finish = route[0], route[-1]
    separation_m = haversine(points[0]["lat"], points[0]["lon"], points[-1]["lat"], points[-1]["lon"])
    separation_px = math.hypot(start[0] - finish[0], start[1] - finish[1])
    same_place = separation_m <= 25 or separation_px <= 18

    if same_place:
        cx, cy = (start[0] + finish[0]) / 2, (start[1] + finish[1]) / 2
        graphics.marker(draw, (cx, cy), 15, theme["orange"], theme["white"], 3)
        graphics.marker(draw, (cx, cy), 7, theme["green"], theme["white"], 2)
    else:
        graphics.marker(draw, start, 11, theme["green"], theme["white"], 3)
        graphics.marker(draw, finish, 11, theme["orange"], theme["white"], 3)


def render(img, draw: ImageDraw.ImageDraw, cfg: dict, metrics: dict, theme: dict, points=None, paces=None, **_) -> ImageDraw.ImageDraw:
    box = PANEL_BOXES["trace"]
    graphics.rounded_panel(draw, box, 18, theme["panel_alt"], theme["blue"], 2)
    graphics.text(draw, (44, 550), "MISSION TRACE", 21, theme["blue"], True)

    graphics.rounded_panel(draw, TRACE_LEGEND_BOX, 14, theme["legend_bg"], theme["line"], 1)
    key_y = 630
    tolerance = int(cfg.get("near_pace_tolerance_seconds", 10))
    entries = [
        (theme["green"], "At mission pace", f"(≤ {cfg['mission_pace_threshold']}/mi)"),
        (theme["orange"], "Near mission pace", f"(+{tolerance} sec/mi)"),
        (theme["grey"], "Below mission pace", ""),
    ]
    for colour, line1, line2 in entries:
        graphics.legend_swatch(draw, (54, key_y + 10, 82, key_y + 10), colour, 8)
        graphics.text(draw, (96, key_y), line1, 14, theme["white"])
        if line2:
            graphics.text(draw, (96, key_y + 22), line2, 13, theme["muted"])
            key_y += 57
        else:
            key_y += 43

    # Marker row position derives from key_y (where the legend
    # entries actually finished stacking) rather than a hardcoded
    # literal — the original locked design used a fixed y=757/767
    # here, which collided with the "Below mission pace" label above
    # it whenever that entry's shorter pitch left less room than the
    # fixed value assumed. See geometry.TRACE_LEGEND_BOX's comment.
    marker_cy = key_y + 6 + 9
    graphics.marker(draw, (63, marker_cy), 9, theme["green"], theme["white"], 2)
    graphics.marker(draw, (89, marker_cy), 9, theme["orange"], theme["white"], 2)
    graphics.text(draw, (110, marker_cy - 10), "Start / finish", 13, theme["white"])

    graphics.grid(img, TRACE_ROUTE_BOX, theme["grid"])
    draw = ImageDraw.Draw(img)

    route = scale_route(points, TRACE_ROUTE_BOX, 26)
    colours = _route_colours(cfg, metrics, paces, theme)
    graphics.route_polyline(draw, route, colours, width=8)
    _draw_route_markers(draw, route, points, theme)

    graphics.progress_ring_label(
        draw, TRACE_PERCENT_BOX, theme["green"],
        f"{cfg['mission_percent']}%",
        ["of route at", "mission pace"],
        theme["white"],
    )
    return draw
