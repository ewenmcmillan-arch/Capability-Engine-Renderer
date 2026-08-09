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


def test_split_rows_covers_whole_route_in_at_most_four_rows():
    points = _points()
    rows = metrics.split_rows(points)
    assert 1 <= len(rows) <= 4
    for row in rows:
        assert "label" in row and "pace" in row and "elev" in row and "hr" in row


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
