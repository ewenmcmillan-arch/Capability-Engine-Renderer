"""metrics.py — everything numerical.

Owns: every derived number computed from GPX points or config —
smoothed pace, splits, best-effort segments, HR recovery, elevation
gain. Nothing in this module draws, wraps text, or picks
coordinates; it returns plain numbers/dicts for layout.py and the
panels to consume.

Some metrics named in the target architecture (VO2 estimate, training
load, fatigue, efficiency) aren't computable from the current
GPX/JSON schema yet — see the stubs at the bottom, which raise
NotImplementedError with a clear reason rather than silently
returning a fake number. Cadence *is* computable (see
cadence_summary() below) now that parse_gpx() reads the GPX's
gpxtpx:cad extension.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from .geometry import MILE_METRES, haversine


def smoothed_paces(points: Sequence[dict], radius: int = 3) -> List[Optional[float]]:
    """Seconds-per-mile pace for each GPX segment, smoothed over a
    rolling window of `radius` segments either side. Segments with
    implausible pace (>1800 s/mi, i.e. slower than 30 min/mile —
    almost always a GPS/time glitch) are excluded from the window."""
    raw: List[Optional[float]] = []
    for a, b in zip(points, points[1:]):
        distance = haversine(a["lat"], a["lon"], b["lat"], b["lon"])
        elapsed = (b["time"] - a["time"]).total_seconds() if a["time"] and b["time"] else None
        raw.append(elapsed / (distance / MILE_METRES) if distance > 1 and elapsed and elapsed > 0 else None)

    smoothed: List[Optional[float]] = []
    for i in range(len(raw)):
        values = [raw[j] for j in range(max(0, i - radius), min(len(raw), i + radius + 1)) if raw[j] and raw[j] < 1800]
        smoothed.append(sum(values) / len(values) if values else None)
    return smoothed


def split_rows(points: Sequence[dict]) -> List[dict]:
    """Per-mile splits (label, pace seconds, elevation change ft, avg HR),
    computed purely from GPX — the GPX is authoritative, nothing here
    invents distance or time. Returns one row per full mile plus a
    final partial-mile remainder, for the whole route — no cap here.
    The splits panel decides how many of these it can fit legibly;
    see panels/splits.py's own row-count cap for why that's a
    display concern, not a metrics one."""
    cumulative = [0.0]
    for a, b in zip(points, points[1:]):
        cumulative.append(cumulative[-1] + haversine(a["lat"], a["lon"], b["lat"], b["lon"]))
    total = cumulative[-1]

    marks: List[float] = []
    marker = MILE_METRES
    while marker < total:
        marks.append(marker)
        marker += MILE_METRES
    marks.append(total)

    rows: List[dict] = []
    start_i, start_d = 0, 0.0
    start_t, start_e = points[0]["time"], points[0]["ele"]
    for number, mark in enumerate(marks, 1):
        index = next((i for i, v in enumerate(cumulative) if v >= mark), len(cumulative) - 1)
        segment_distance = mark - start_d
        end_t, end_e = points[index]["time"], points[index]["ele"]
        elapsed = (end_t - start_t).total_seconds() if start_t and end_t else None
        pace = elapsed / (segment_distance / MILE_METRES) if elapsed and segment_distance else None
        heart_rates = [p["hr"] for p in points[start_i:index + 1] if p["hr"]]
        rows.append({
            "label": str(number) if mark < total else f"{segment_distance / MILE_METRES:.2f}",
            "pace": pace,
            "elev": None if start_e is None or end_e is None else (end_e - start_e) * 3.28084,
            "hr": round(sum(heart_rates) / len(heart_rates)) if heart_rates else None,
        })
        start_i, start_d, start_t, start_e = index, mark, end_t, end_e
    return rows


def best_segment_pace(points: Sequence[dict], segment_metres: float) -> Optional[float]:
    """Fastest pace (seconds/mile) sustained over any contiguous
    segment of the given distance — generalises 'best 1/4 mile',
    'best 1/2 mile', 'best mile' onto one function."""
    cumulative = [0.0]
    for a, b in zip(points, points[1:]):
        cumulative.append(cumulative[-1] + haversine(a["lat"], a["lon"], b["lat"], b["lon"]))
    total = cumulative[-1]
    if total < segment_metres:
        return None

    best: Optional[float] = None
    j = 0
    for i in range(len(cumulative)):
        target = cumulative[i] + segment_metres
        if target > total:
            break
        j = max(j, i)
        while cumulative[j] < target:
            j += 1
        t0, t1 = points[i]["time"], points[j]["time"]
        if t0 is None or t1 is None:
            continue
        elapsed = (t1 - t0).total_seconds()
        if elapsed <= 0:
            continue
        pace = elapsed / (segment_metres / MILE_METRES)
        if best is None or pace < best:
            best = pace
    return best


def elevation_summary(points: Sequence[dict]) -> Dict[str, Optional[float]]:
    """Total gain (ft, positive deltas only) and max elevation (ft)."""
    elevations = [p["ele"] for p in points if p["ele"] is not None]
    if not elevations:
        return {"gain_ft": None, "max_ft": None}
    gain_m = sum(max(0.0, b - a) for a, b in zip(elevations, elevations[1:]))
    return {"gain_ft": gain_m * 3.28084, "max_ft": max(elevations) * 3.28084}


def mission_pace_threshold_seconds(mission_pace_threshold: str) -> int:
    """Parse a 'MM:SS' mission-pace threshold string into seconds/mile."""
    mm, ss = mission_pace_threshold.split(":")
    return int(mm) * 60 + int(ss)


def hr_recovery(cfg: dict) -> Dict[str, object]:
    """HR recovery figures for the recovery panel.

    Sourced from the config JSON (hr_recovery_start/end/1min/2min) by
    design, not computed from the GPX — this is a genuinely external
    measurement (Huawei Health app, heart rate monitored for two
    minutes after the run stops), not something the run's GPX track
    could derive even in principle: the watch/app keeps sampling
    after GPS recording ends. Whatever upstream process builds the
    mission-card config is expected to supply these four fields from
    that source.

    Returns {"available": False} if none of the four fields are
    present, rather than silently falling back to placeholder
    numbers — the original locked renderer defaulted to '145' /
    '115' / '-17' / '-30' when the fields were absent, which meant a
    session with no real recovery reading rendered fabricated data
    indistinguishable from a genuine one. panels/recovery.py must
    check "available" and render a "no data" state instead of
    drawing anything when it's False.
    """
    keys = ["hr_recovery_start", "hr_recovery_end", "hr_recovery_1min", "hr_recovery_2min"]
    if not any(k in cfg for k in keys):
        return {"available": False}
    return {
        "available": True,
        "start": str(cfg.get("hr_recovery_start", "—")),
        "end": str(cfg.get("hr_recovery_end", "—")),
        "one_min": str(cfg.get("hr_recovery_1min", "—")),
        "two_min": str(cfg.get("hr_recovery_2min", "—")),
    }


# --- Not yet implemented ---------------------------------------------------
# Listed in the target architecture but not computable from the current
# GPX/JSON schema. Each raises with a specific reason so a panel that
# tries to use one fails loudly in development rather than rendering a
# silently wrong number.

def cadence_summary(points: Sequence[dict]) -> Dict[str, Optional[float]]:
    """Average and max cadence directly from the GPX's gpxtpx:cad
    extension (present on Garmin/Strava-exported tracks with a
    footpod or watch cadence sensor).

    Reported as-recorded (steps per minute for one foot, per the
    Garmin TrackPointExtension convention — not doubled to full
    strides/min), so a value in the 70-95 range for an easy run is
    normal, not low. Returns None values if the GPX has no cadence
    extension at all, rather than raising — cadence is optional
    sensor data, unlike lat/lon/time which every GPX must have.
    """
    values = [p["cad"] for p in points if p.get("cad") is not None]
    if not values:
        return {"avg_spm": None, "max_spm": None}
    return {"avg_spm": round(sum(values) / len(values)), "max_spm": max(values)}


def vo2_estimate(cfg: dict, points: Sequence[dict]) -> float:
    raise NotImplementedError("VO2 estimate requires age/resting-HR/max-HR inputs not yet in the config schema")


def training_load(cfg: dict, points: Sequence[dict]) -> float:
    raise NotImplementedError("training load requires a rolling history of sessions, not just the current one")


def fatigue(cfg: dict, points: Sequence[dict]) -> float:
    raise NotImplementedError("fatigue requires a rolling history of sessions, not just the current one")


def efficiency(cfg: dict, points: Sequence[dict]) -> float:
    raise NotImplementedError("efficiency requires power or a validated economy model not yet defined for this project")
