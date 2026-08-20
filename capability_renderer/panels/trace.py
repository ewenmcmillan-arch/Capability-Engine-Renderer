from __future__ import annotations

from PIL import ImageDraw

from .. import graphics
from ..geometry import PANEL_BOXES, TRACE_LEGEND_BOX, TRACE_PERCENT_BOX, TRACE_ROUTE_BOX, scale_route
from ..metrics import mission_pace_threshold_seconds


def _pace_distance(pace: float, threshold: int, direction: str) -> float:
    """How far `pace` sits from the "good" side of `threshold`, given
    the mission's own pace_direction — 0 means fully on the good side
    (never penalised, however far past the threshold that goes),
    positive means genuinely off, in seconds/mile.

    - "ceiling" (e.g. "average pace at or under 9:15/mi"): any pace at
      or faster than the threshold is 0 — running faster than asked
      is success, not something to mark down for being far from the
      threshold. Only running *slower* than threshold counts against
      it.
    - "floor" (e.g. a long run's "don't go faster than 10:00/mi"):
      the mirror image — at or slower than threshold is 0, only
      running *faster* counts against it.
    - "band" (default, e.g. a recovery mission's "hold pace honest and
      even without pressing"): the original symmetric behaviour —
      distance in *either* direction counts, since neither faster nor
      slower than the target is what the mission is asking for.

    Real bug this fixes: a mission whose own success_definition reads
    "average pace at or under 9:15/mi" (a ceiling) was still scored
    with the old symmetric band, so an athlete who ran fast intervals
    well under target saw those miles marked "off mission pace" —
    the "% at mission pace" badge could read as low as 15% on a run
    that had already satisfied its own stated success definition on
    average. See mission_percent() in the web app's renderer_bridge.py,
    which applies this exact same function so the panel's colours and
    the progress-ring percentage always agree."""
    diff = pace - threshold
    if direction == "ceiling":
        return max(0.0, diff)
    if direction == "floor":
        return max(0.0, -diff)
    return abs(diff)


def _route_colours(cfg: dict, metrics: dict, paces, theme: dict):
    """Colour each segment by how far its pace sits from the "good"
    side of the mission threshold — see _pace_distance() for what
    "good side" means for this mission's own pace_direction (ceiling/
    floor/band). Defaults to "band" (the original behaviour) when a
    config doesn't carry the field at all, so an older saved config
    renders exactly as it always did."""
    threshold = mission_pace_threshold_seconds(cfg["mission_pace_threshold"])
    tolerance = int(cfg.get("near_pace_tolerance_seconds", 10))
    direction = cfg.get("mission_pace_direction") or "band"
    colours = []
    for pace in paces:
        if pace is None:
            colours.append(theme["grey"])
            continue
        diff = _pace_distance(pace, threshold, direction)
        if diff <= tolerance:
            colours.append(theme["green"])
        elif diff <= tolerance * 2:
            colours.append(theme["orange"])
        else:
            colours.append(theme["grey"])
    return colours


def _legend_entries(cfg: dict, tolerance: int, theme: dict):
    """Legend text describing the same _pace_distance() rule the
    route's actually coloured with — kept in sync deliberately (see
    _route_colours()'s docstring): a "ceiling" mission's legend
    shouldn't claim a symmetric ±Ns band when running faster than
    threshold is never actually penalised."""
    direction = cfg.get("mission_pace_direction") or "band"
    mission_pace = cfg["mission_pace_threshold"]
    # Kept roughly the same length as the "band" case's original text
    # below — this renders in TRACE_LEGEND_BOX, a fixed-width sub-
    # region with no wrapping, so a much longer string would run past
    # its edge.
    if direction == "ceiling":
        green_note = f"(≤ {mission_pace}/mi, +{tolerance}s)"
        orange_note = f"(+{tolerance}-{tolerance * 2}s slower)"
    elif direction == "floor":
        green_note = f"(≥ {mission_pace}/mi, -{tolerance}s)"
        orange_note = f"({tolerance}-{tolerance * 2}s faster)"
    else:
        green_note = f"(±{tolerance}s of {mission_pace}/mi)"
        orange_note = f"(±{tolerance * 2}s)"
    return [
        (theme["green"], "At mission pace", green_note),
        (theme["orange"], "Near mission pace", orange_note),
        (theme["grey"], "Off mission pace", ""),
    ]


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


def _shift_box(box, offset: int):
    x0, y0, x1, y1 = box
    return (x0, y0 + offset, x1, y1 + offset)


def render(img, draw: ImageDraw.ImageDraw, cfg: dict, metrics: dict, theme: dict, points=None, paces=None, offset: int = 0, **_) -> ImageDraw.ImageDraw:
    box = PANEL_BOXES["trace"]
    graphics.rounded_panel(draw, box, 18, theme["panel_alt"], theme["blue"], 2)
    graphics.text(draw, (44, 550 + offset), "MISSION TRACE", 21, theme["blue"], True)

    # offset shifts this whole panel's sub-regions down when
    # mission/assessment above it grew — TRACE_LEGEND_BOX/ROUTE_BOX/
    # PERCENT_BOX are otherwise-fixed sub-regions, unlike box itself
    # (already grown by geometry.apply_dynamic_layout).
    legend_box = _shift_box(TRACE_LEGEND_BOX, offset)
    route_box = _shift_box(TRACE_ROUTE_BOX, offset)
    percent_box = _shift_box(TRACE_PERCENT_BOX, offset)

    graphics.rounded_panel(draw, legend_box, 14, theme["legend_bg"], theme["line"], 1)
    key_y = 630 + offset
    tolerance = int(cfg.get("near_pace_tolerance_seconds", 10))
    entries = _legend_entries(cfg, tolerance, theme)
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

    graphics.grid(img, route_box, theme["grid"])
    draw = ImageDraw.Draw(img)

    route = scale_route(points, route_box, 26)
    colours = _route_colours(cfg, metrics, paces, theme)
    graphics.route_polyline(draw, route, colours, width=8)
    _draw_route_markers(draw, route, points, theme)

    graphics.progress_ring_label(
        draw, percent_box, theme["green"],
        f"{cfg['mission_percent']}%",
        ["of route at", "mission pace"],
        theme["white"],
    )
    return draw
