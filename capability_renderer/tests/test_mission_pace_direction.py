from capability_renderer.panels.trace import _legend_entries, _pace_distance, _route_colours
from capability_renderer.theme import load_theme


def test_pace_distance_band_is_symmetric():
    # Default/legacy behaviour — deviation in either direction counts,
    # matching what a config with no mission_pace_direction at all
    # (an older saved config) should still do.
    threshold = 555  # 9:15/mi in seconds
    assert _pace_distance(540, threshold, "band") == 15  # 15s faster
    assert _pace_distance(570, threshold, "band") == 15  # 15s slower


def test_pace_distance_ceiling_never_penalises_running_faster():
    # Real bug this fixes: a mission whose success definition is
    # "average pace at or under 9:15/mi" was still scored with the
    # symmetric band, so running well under target read as "off
    # mission pace" instead of success.
    threshold = 555
    assert _pace_distance(480, threshold, "ceiling") == 0  # 75s faster — still "on target"
    assert _pace_distance(555, threshold, "ceiling") == 0  # exactly at threshold
    assert _pace_distance(570, threshold, "ceiling") == 15  # 15s slower — genuinely off


def test_pace_distance_floor_never_penalises_running_slower():
    # Mirror image — a long run's "don't go faster than 10:00/mi".
    threshold = 600
    assert _pace_distance(650, threshold, "floor") == 0  # 50s slower — still fine
    assert _pace_distance(600, threshold, "floor") == 0
    assert _pace_distance(580, threshold, "floor") == 20  # 20s faster — genuinely off


def test_route_colours_defaults_to_band_when_direction_missing():
    # Older saved configs never had this field — must render exactly
    # as they always did.
    theme = load_theme("default")
    cfg = {"mission_pace_threshold": "9:15", "near_pace_tolerance_seconds": 10}
    colours = _route_colours(cfg, {}, [540, 555, 570, 600], theme)
    assert colours == [theme["orange"], theme["green"], theme["orange"], theme["grey"]]


def test_route_colours_ceiling_marks_faster_paces_green():
    theme = load_theme("default")
    cfg = {"mission_pace_threshold": "9:15", "near_pace_tolerance_seconds": 10, "mission_pace_direction": "ceiling"}
    # 480 = well under threshold (fast), 570 = 15s slower (off)
    colours = _route_colours(cfg, {}, [480, 555, 570], theme)
    assert colours == [theme["green"], theme["green"], theme["orange"]]


def test_legend_entries_reflect_ceiling_direction_not_a_symmetric_band():
    theme = load_theme("default")
    cfg = {"mission_pace_threshold": "9:15", "mission_pace_direction": "ceiling"}
    entries = _legend_entries(cfg, 10, theme)
    green_note = entries[0][2]
    assert "±" not in green_note  # not falsely claiming a symmetric band
    assert "9:15" in green_note


def test_legend_entries_default_band_unchanged():
    theme = load_theme("default")
    cfg = {"mission_pace_threshold": "9:15"}
    entries = _legend_entries(cfg, 10, theme)
    assert entries[0][2] == "(±10s of 9:15/mi)"
    assert entries[1][2] == "(±20s)"
