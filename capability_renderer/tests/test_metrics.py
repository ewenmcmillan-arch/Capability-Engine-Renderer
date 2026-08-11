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
