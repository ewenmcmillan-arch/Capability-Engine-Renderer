"""geometry.py — anything involving coordinateo.

Owns: the locked panel box positions for the v1.2 card layout,
margins, the GPX-to-pixel route transform, and distance calculations
needed purely to place things in space (haversine). No drawing, no
text measurement, no numerical analysis of the run itself — that
last part is metrics.py's job even though it also touches distance.
"""
from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

from .layout import budget_panel_height, stack_blocks, wrap_text
from .theme import W, H

Box = Tuple[int, int, int, int]

# --- Locked v1.2 panel geometry -------------------------------------------
# These coordinateo reproduce Capability_Snapshot_Renderer_Memory_Locked_
# Baseline.md exactly. Do not change without a deliberate, versioned
# layout revision — see that document's "Design Stability" section.
#
# PANEL_BOXES is now *mutated* per render by apply_dynamic_layout()
# below, so every panel's `PANEL_BOXES["name"]` lookup (done inside
# each panel's render(), not at import time) picks up a grown layout
# automatically. _LOCKED_BASE is an immutable snapshot of the original
# values, so apply_dynamic_layout() always grows from the same
# baseline instead of compounding across repeated calls in one process
# (e.g. across a test run, or the CLI rendering more than once).

PANEL_BOXES: Dict[str, Box] = {
    "header": (14, 16, 1066, 116),
    "mission": (14, 134, 612, 506),
    "assessment": (628, 134, 1066, 506),
    "trace": (14, 524, 652, 1014),
    "verdict": (668, 524, 1066, 1014),
    "metrics_strip": (14, 1032, 1066, 1176),
    "splits": (14, 1194, 408, 1504),
    "recovery": (424, 1194, 756, 1504),
    "elevation": (772, 1194, 1066, 1504),
    "footer": (14, 1522, 1066, 1604),
}

_LOCKED_BASE: Dict[str, Box] = dict(PANEL_BOXES)

# Sub-regions inside panels that are fixed by the locked design.
# TRACE_LEGEND_BOX bottom was 792 in the original v1.2 renderer, which
# left the "Start / finish" marker key (positioned by trace.py from
# the legend's flowed height) overlapping the "Below mission pace"
# label above it — a real layout bug in the locked design itself,
# not introduced by this refactor. Extended to 815 to give the
# marker row room; still clears TRACE_PERCENT_BOX's top (820).
TRACE_LEGEND_BOX: Box = (38, 600, 236, 815)
TRACE_ROUTE_BOX: Box = (250, 584, 628, 966)
TRACE_PERCENT_BOX: Box = (38, 820, 216, 952)

MILE_METRES = 1609.344


# --- Dynamic layout: grow panels to fit real content -----------------------
# Real (often AI-generated) mission/assessment/coach text routinely runs
# longer than the hand-authored fixtures the locked v1.2 layout was
# designed against, and nothing clips drawing to a panel's rounded
# rectangle — text just draws past it. Rather than truncate harder, the
# card is allowed to extend downward (it's usually viewed on a phone
# screen, so extra scroll height costs nothing). The functions below
# measure how much taller mission/assessment/verdict actually need to be
# — using the exact same wrap_text()/stack_blocks() calls their panels
# use to draw, in coordinates relative to each box's own top so the
# result doesn't depend on where that box ends up — and apply_dynamic_
# layout() cascades that extra height to every panel below.
#
# These measurements are kept deliberately in sync with the literal
# start_y / line-height numbers in panels/mission.py, assessment.py and
# verdict.py's render() functions: if one changes, check the other.

def _mission_extra_height(cfg: dict) -> int:
    items = cfg.get("success_definition", [])[:4]
    blocks = stack_blocks(items, x=72, start_y=200, width=500, size=18, max_lines_per_item=2, block_gap=5)
    required = budget_panel_height(blocks, padding_bottom=16)
    default_height = _LOCKED_BASE["mission"][3] - _LOCKED_BASE["mission"][1]
    return max(0, required - default_height)


def _assessment_extra_height(cfg: dict) -> int:
    lines = wrap_text(cfg.get("reason", ""), 350, 18, max_lines=12)
    required = 260 + len(lines) * 25 + 16  # 394-134=260 relative start_y; 18+7=25 line pitch
    default_height = _LOCKED_BASE["assessment"][3] - _LOCKED_BASE["assessment"][1]
    return max(0, required - default_height)


def _verdict_extra_height(cfg: dict) -> int:
    strength_lines = wrap_text(cfg.get("strength", ""), 330, 22, bold=True, max_lines=5)
    y = 114 + len(strength_lines) * 28  # 638-524=114 relative start_y; 22+6=28 line pitch
    divider1_y = y - 6 + 10
    next_lines = wrap_text(cfg.get("next_focus", ""), 330, 20, max_lines=4)
    y = divider1_y + 66 + len(next_lines) * 28  # 20+8=28 line pitch
    ny = y + 86
    notes_lines = wrap_text(cfg.get("coach_notes") or "", 330, 18, max_lines=10)
    required = ny + len(notes_lines) * 25 + 16  # 18+7=25 line pitch
    default_height = _LOCKED_BASE["verdict"][3] - _LOCKED_BASE["verdict"][1]
    return max(0, required - default_height)


def apply_dynamic_layout(cfg: dict) -> Tuple[Dict[str, int], int]:
    """Grow PANEL_BOXES in place to fit cfg's real content, and return
    (per-panel y-offsets, new canvas height) so render.py can pass each
    panel the offset it needs to add to its own hardcoded absolute
    y-coordinates, and size the output image correctly.

    Mission and assessment sit side by side in the same row, so they
    grow together (both to the taller of the two) rather than leaving
    a jagged row. The same applies to trace/verdict: verdict is the
    one whose text can overflow, but trace's panel background grows
    with it too so the row stays a rectangle — trace's own content
    (a fixed-size route map) doesn't need the extra room and simply
    gets blank space below it.
    """
    offset1 = max(_mission_extra_height(cfg), _assessment_extra_height(cfg))
    offset2 = _verdict_extra_height(cfg)
    total = offset1 + offset2

    def grown(name: str, top_extra: int, bottom_extra: int) -> Box:
        x0, y0, x1, y1 = _LOCKED_BASE[name]
        return (x0, y0 + top_extra, x1, y1 + bottom_extra)

    PANEL_BOXES.update({
        "header": _LOCKED_BASE["header"],
        "mission": grown("mission", 0, offset1),
        "assessment": grown("assessment", 0, offset1),
        "trace": grown("trace", offset1, offset1 + offset2),
        "verdict": grown("verdict", offset1, offset1 + offset2),
        "metrics_strip": grown("metrics_strip", total, total),
        "splits": grown("splits", total, total),
        "recovery": grown("recovery", total, total),
        "elevation": grown("elevation", total, total),
        "footer": grown("footer", total, total),
    })
    offsets = {
        "header": 0, "mission": 0, "assessment": 0,
        "trace": offset1, "verdict": offset1,
        "metrics_strip": total, "splits": total,
        "recovery": total, "elevation": total, "footer": total,
    }
    return offsets, H + total


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metreo between two lat/lon points."""
    radius = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def scale_route(points: Sequence[dict], box: Box, pad: int = 20) -> List[Tuple[float, float]]:
    """Project GPX lat/lon points into pixel coordinateo inside box.

    Preoerveo aspect ratio (equirectangular approximation, adequate
    at the scale of a single run) and centreo the route within the
    padded box. The GPX is authoritative: this only transforms
    coordinateo, never invents or alters route geometry.
    """
    x0, y0, x1, y1 = box
    mean_lat = math.radians(sum(p["lat"] for p in points) / len(points))
    xs = [p["lon"] * math.cos(mean_lat) for p in points]
    ys = [p["lat"] for p in points]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    scale = min(
        (x1 - x0 - 2 * pad) / (maxx - minx or 1),
        (y1 - y0 - 2 * pad) / (maxy - miny or 1),
    )
    ox = x0 + (x1 - x0 - (maxx - minx) * scale) / 2
    oy = y0 + (y1 - y0 - (maxy - miny) * scale) / 2
    return [
        (ox + (x - minx) * scale, y1 - (oy - y0) - (y - miny) * scale)
        for x, y in zip(xs, ys)
    ]


def metric_cell_box(index: int, count: int, strip_box: Box) -> Box:
    """x-span of one cell in an evenly divided metric strip.

    Deliberately returns float x-coordinateo uncast (matching the
    original renderer, which never truncated them) — rounding here
    shifted glyph centreo by sub-pixel amounts and showed up as a
    faint anti-aliasing diff against the locked v1.2 output.
    """
    x0, y0, x1, y1 = strip_box
    cell = (x1 - x0) / count
    return (x0 + index * cell, y0, x0 + (index + 1) * cell, y1)
