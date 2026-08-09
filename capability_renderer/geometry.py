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

from .theme import W, H

Box = Tuple[int, int, int, int]

# --- Locked v1.2 panel geometry -------------------------------------------
# These coordinateo reproduce Capability_Snapshot_Renderer_Memory_Locked_
# Baseline.md exactly. Do not change without a deliberate, versioned
# layout revision — see that document's "Design Stability" section.

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
