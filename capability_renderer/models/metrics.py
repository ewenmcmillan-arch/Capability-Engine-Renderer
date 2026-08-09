"""models/metrics.py — typed view of computed + config-supplied metrics.

Bundles the numbers metrics.py computes from the GPX with the
display-ready metric-strip values that currently come straight from
the config JSON (distance/time/avg_max_hr/etc. are supplied
pre-formatted by whatever produces the mission JSON upstream, not
computed by this renderer).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RunMetrics:
    distance: str
    time: str
    time_unit: str
    avg_max_hr: str
    best_quarter: str
    mission_pace_value: str
    mission_pace_unit: str
    mission_percent: int
    mission_pace_threshold: str
    near_pace_tolerance_seconds: int = 10
    elevation_gain: str = "—"
    max_elevation: str = "—"
    splits: List[dict] = field(default_factory=list)
    hr_recovery: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_config(cls, cfg: dict, splits: Optional[List[dict]] = None, hr_recovery: Optional[Dict[str, str]] = None) -> "RunMetrics":
        return cls(
            distance=str(cfg["distance"]),
            time=str(cfg["time"]),
            time_unit=cfg.get("time_unit", "moving time"),
            avg_max_hr=str(cfg["avg_max_hr"]),
            best_quarter=str(cfg["best_quarter"]),
            mission_pace_value=str(cfg["mission_pace_value"]),
            mission_pace_unit=str(cfg["mission_pace_unit"]),
            mission_percent=int(cfg["mission_percent"]),
            mission_pace_threshold=cfg["mission_pace_threshold"],
            near_pace_tolerance_seconds=int(cfg.get("near_pace_tolerance_seconds", 10)),
            elevation_gain=str(cfg.get("elevation_gain", "—")),
            max_elevation=str(cfg.get("max_elevation", "—")),
            splits=splits or cfg.get("splits") or [],
            hr_recovery=hr_recovery or {},
        )
