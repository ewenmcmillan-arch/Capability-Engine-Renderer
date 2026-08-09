"""models/route.py — the parsed, authoritative GPX route.

The GPX is the single source of truth for route geometry — see the
locked baseline's "GPX Rules": never invent route geometry, never
alter route topology. This model exists so panels pass one object
around instead of a raw list-of-dicts plus separately-computed paces.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RoutePoint:
    lat: float
    lon: float
    time: Optional[object] = None  # datetime, kept loosely typed to avoid an import cycle
    ele: Optional[float] = None
    hr: Optional[int] = None
    cad: Optional[int] = None  # steps/min, single-foot convention (Garmin TrackPointExtension) — not doubled to full strides


@dataclass
class Route:
    points: List[RoutePoint]
    smoothed_paces: List[Optional[float]]

    @property
    def start(self) -> RoutePoint:
        return self.points[0]

    @property
    def finish(self) -> RoutePoint:
        return self.points[-1]
