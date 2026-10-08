from pathlib import Path

import pytest

from capability_renderer import metrics
from capability_renderer.render import parse_gpx

FIXTURE_GPX = Path(__file__).parent / "fixtures_sample.gpx"


def _points():
    return parse_gpx(FIXTURE_GPX)


def test_parse_gpx_reads_all_points_with_time_ele_hr_cad():
    points = _points()
    assert len(points) == 6
    assert all(p["time"] is not None for p in points)
    assert all(p["ele"] is not None for p in points)
    assert all(p["hr"] is not None for p in points)
    assert all(p["cad"] is not None for p in points)


def test_smoothed_paces_returns_one_value_per_segment():
    points = _points()
    paces = metrics.smoothed_paces(points)
    assert len(paces) == len(points) - 1
    assert any(p is not None for p in paces)


def test_split_rows_covers_whole_route():
    points = _points()
    rows = metrics.split_rows(points)
    assert len(rows) >= 1
    for row in rows:
        assert "label" in row and "pace" in row and "elev" in row and "hr" in row


def test_split_rows_returns_one_row_per_mile_uncapped():
    """split_rows() itself has no row-count cap — that's the splits
    panel's display concern (see panels/splits.py), not a metrics
    one. A synthetic 8-mile route should yield 8 full-mile rows plus
    no partial-mile remainder (it lands exactly on a mile mark)."""
    import datetime as dt
    import math

    from capability_renderer.metrics import MILE_METRES

    start = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    # Walk due north (no longitude change) so haversine distance is
    # simple and predictable: for a pure latitude change it reduces to
    # radius * delta_phi. Derive degrees-per-metre from the exact same
    # radius geometry.haversine() uses, so mile marks land exactly.
    metres_per_degree = 6_371_000 * math.pi / 180
    points = []
    for i in range(9):  # 0..8 miles, one point per mile mark
        lat = i * (MILE_METRES / metres_per_degree)
        points.append({
            "lat": lat, "lon": 0.0,
            "time": start + dt.timedelta(minutes=9 * i),
            "ele": 100.0, "hr": 140, "cad": 160,
        })
    rows = metrics.split_rows(points)
    # Row count is the actual regression concern here (used to be
    # hard-capped at 4 regardless of distance). Only the first 7
    # labels are asserted exactly — floating-point drift in the
    # synthetic route's cumulative distance means the 8th can land a
    # hair short of an exact mile mark, which correctly produces a
    # fractional-mile label (e.g. "1.00") rather than "8". That's the
    # same real-world behaviour a genuine GPX route has, since actual
    # routes essentially never end on an exact mile boundary either.
    assert len(rows) == 8
    assert [r["label"] for r in rows[:7]] == [str(n) for n in range(1, 8)]


def test_elevation_summary_reports_gain_and_max():
    points = _points()
    summary = metrics.elevation_summary(points)
    assert summary["gain_ft"] is not None
    assert summary["max_ft"] is not None
    assert summary["max_ft"] >= summary["gain_ft"] or summary["gain_ft"] >= 0


def test_mission_pace_threshold_seconds_parses_mm_ss():
    assert metrics.mission_pace_threshold_seconds("9:00") == 540
    assert metrics.mission_pace_threshold_seconds("10:30") == 630


def test_hr_recovery_reads_config_with_fallbacks():
    result = metrics.hr_recovery({"hr_recovery_start": "150"})
    assert result["available"] is True
    assert result["start"] == "150"
    assert result["end"] == "—"


def test_hr_recovery_unavailable_when_no_fields_supplied():
    result = metrics.hr_recovery({"mission": "irrelevant other field"})
    assert result == {"available": False}


@pytest.mark.parametrize("fn_name", ["vo2_estimate", "training_load", "fatigue", "efficiency"])
def test_unimplemented_metrics_raise_not_implemented_with_reason(fn_name):
    fn = getattr(metrics, fn_name)
    with pytest.raises(NotImplementedError):
        fn({}, _points())


def test_cadence_summary_averages_recorded_values():
    points = _points()
    result = metrics.cadence_summary(points)
    assert result["avg_spm"] is not None
    assert result["max_spm"] is not None
    assert result["max_spm"] >= result["avg_spm"]


def test_cadence_summary_returns_none_when_gpx_has_no_cadence_extension():
    points = [{"lat": 0, "lon": 0, "time": None, "ele": None, "hr": None, "cad": None}] * 3
    result = metrics.cadence_summary(points)
    assert result == {"avg_spm": None, "max_spm": None}


# --- Moving-time splits. Found live (2026-10-08): a run with ~2 min of
# short stops showed splits of 9:43 and 10:12 where Strava showed 9:06
# and 9:02 — split_rows() used elapsed clock time, so every stop was
# counted as very slow running.

def _straight_route(intervals_s, metres_per_step):
    """Points heading due north, one per interval; metres_per_step may
    be a list (per step) or a single value."""
    import datetime as dt
    import math

    start = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    deg_per_metre = 1 / (6_371_000 * math.pi / 180)
    steps = metres_per_step if isinstance(metres_per_step, list) else [metres_per_step] * len(intervals_s)
    points = [{"lat": 0.0, "lon": 0.0, "time": start, "ele": 100.0, "hr": 140, "cad": 170}]
    lat, t = 0.0, start
    for seconds, metres in zip(intervals_s, steps):
        lat += metres * deg_per_metre
        t += dt.timedelta(seconds=seconds)
        points.append({"lat": lat, "lon": 0.0, "time": t, "ele": 100.0, "hr": 140, "cad": 170})
    return points


def test_split_pace_excludes_a_pause_gap():
    # 1 mile at 3 m/s in 1s samples, with a 90s stop (one gap between
    # two points ~1m apart) in the middle. Moving pace must match the
    # same mile with no stop.
    n = round(metrics.MILE_METRES / 3)
    no_stop = _straight_route([1] * n, 3.0)
    intervals = [1] * n
    steps = [3.0] * n
    intervals[n // 2], steps[n // 2] = 90, 1.0
    with_stop = _straight_route(intervals, steps)

    clean = metrics.split_rows(no_stop)[0]["pace"]
    paused = metrics.split_rows(with_stop)[0]["pace"]
    assert paused == pytest.approx(clean, abs=2)


def test_split_pace_excludes_near_stationary_samples():
    # 20s of standing still (0.2 m/s GPS drift) at a crossing, logged as
    # normal 1s samples — Strava doesn't count these as moving either.
    n = round(metrics.MILE_METRES / 3)
    no_stop = _straight_route([1] * n, 3.0)
    standing = _straight_route([1] * (n + 20), [3.0] * (n // 2) + [0.2] * 20 + [3.0] * (n - n // 2))

    clean = metrics.split_rows(no_stop)[0]["pace"]
    stopped = metrics.split_rows(standing)[0]["pace"]
    assert stopped == pytest.approx(clean, abs=2)


def test_smart_recording_intervals_are_not_mistaken_for_pauses():
    # A watch logging every 5s: 5s is its normal interval, not a stop,
    # so nothing should be removed (threshold scales with the median).
    points = _straight_route([5] * 400, 15.0)
    moving = metrics.moving_durations(points)
    assert all(d == 5 for d in moving)
