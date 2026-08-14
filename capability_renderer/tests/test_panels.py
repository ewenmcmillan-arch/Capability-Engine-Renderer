import json
from pathlib import Path

from PIL import Image, ImageDraw

from capability_renderer import metrics as metrics_mod, panels
from capability_renderer.geometry import H, W
from capability_renderer.render import PANEL_ORDER, parse_gpx
from capability_renderer.theme import load_theme

FIXTURE_GPX = Path(__file__).parent / "fixtures_sample.gpx"
FIXTURE_CFG = Path(__file__).parent / "fixtures_sample_config.json"


def _setup():
    cfg = json.loads(FIXTURE_CFG.read_text())
    points = parse_gpx(FIXTURE_GPX)
    paces = metrics_mod.smoothed_paces(points)
    theme = load_theme("default")
    img = Image.new("RGBA", (W, H), theme["bg"])
    draw = ImageDraw.Draw(img)
    return img, draw, cfg, points, paces, theme


def test_every_panel_renders_without_error():
    img, draw, cfg, points, paces, theme = _setup()
    computed = {"paces": paces}
    for name, panel in PANEL_ORDER:
        draw = panel.render(img, draw, cfg, computed, theme, points=points, paces=paces, offset=0)
        assert draw is not None


def test_panel_order_matches_locked_layout_sections():
    # PANEL_ORDER pairs each module with the PANEL_BOXES key
    # apply_dynamic_layout() reports an offset for (see render.py) —
    # module names still match the locked v1.2 draw order.
    names = [module.__name__.rsplit(".", 1)[-1] for _, module in PANEL_ORDER]
    assert names == [
        "header", "mission", "assessment", "trace", "verdict",
        "summary", "splits", "recovery", "elevation", "footer",
    ]


def test_new_panel_can_be_added_without_touching_others():
    """Guards the architectural promise: a new panel module only
    needs the (img, draw, cfg, metrics, theme, **kwargs) signature to
    slot into PANEL_ORDER — nothing else should need to change."""
    import inspect
    for panel in panels.__all__:
        module = getattr(panels, panel)
        sig = inspect.signature(module.render)
        params = list(sig.parameters)
        assert params[:3] == ["img", "draw", "cfg"]


def test_verdict_panel_notes_never_overflow_the_box_bottom():
    """Regression test for a real bug: a long next_focus (using its
    full max_lines=4 budget) pushed the NOTES section's start_y down
    enough that a fixed max_lines=5 on the notes text overflowed the
    panel's bottom border — found by rendering a real run with a
    longer-than-usual coach_notes string, not by synthetic testing."""
    from capability_renderer.geometry import PANEL_BOXES
    from capability_renderer.panels import verdict

    img, draw, cfg, points, paces, theme = _setup()
    cfg = dict(cfg)
    cfg["next_focus"] = "Push the final mile closer to opening pace rather than fading, and keep cadence higher on the descents."
    cfg["coach_notes"] = (
        "Real GPX plus genuine Huawei Watch GT6 heart rate recovery synced via "
        "Strava — the first render with real recovery data rather than the "
        "'no data supplied' fallback, and a notably long note to stress-test "
        "panel overflow handling."
    )
    verdict.render(img, draw, cfg, {}, theme)

    box = PANEL_BOXES["verdict"]
    # Sample the last few rows inside the panel, near its bottom edge —
    # a green pixel there (the panel's own border colour) with no text
    # drawn past it confirms nothing overflowed below box[3].
    below_box = img.crop((box[0], box[3] + 3, box[2], box[3] + 20))
    # A crude but effective check: text pixels are near-white (~243,246,248);
    # confirm no such pixel exists in the strip just below the border.
    px = below_box.convert("RGB").getdata()
    white_ish = [p for p in px if p[0] > 200 and p[1] > 200 and p[2] > 200]
    assert len(white_ish) == 0, f"Found {len(white_ish)} light/text-coloured pixels below the verdict panel's bottom border"


def test_splits_panel_shows_all_rows_without_overflowing():
    """Regression test: split_rows() used to hard-cap at 4 rows to
    match the panel's fixed layout, silently dropping the back half
    of any run longer than ~4 miles — found by rendering a real
    8-mile run. The panel now shrinks row spacing/font to fit every
    split rather than truncating, and must never overflow its box."""
    from capability_renderer.geometry import PANEL_BOXES
    from capability_renderer.panels import splits

    img, draw, cfg, points, paces, theme = _setup()
    cfg = dict(cfg)
    cfg["splits"] = [
        {"label": str(n), "pace": 540 + n, "elev": 10 - n, "hr": 130 + n}
        for n in range(1, 9)  # 8 miles — the case that used to get truncated to 4
    ]
    splits.render(img, draw, cfg, {}, theme)

    box = PANEL_BOXES["splits"]
    below_box = img.crop((box[0], box[3] + 3, box[2], box[3] + 20))
    px = below_box.convert("RGB").getdata()
    white_ish = [p for p in px if p[0] > 200 and p[1] > 200 and p[2] > 200]
    assert len(white_ish) == 0, f"Found {len(white_ish)} light/text-coloured pixels below the splits panel's bottom border"


def test_dynamic_layout_keeps_locked_height_for_short_content():
    """The locked v1.2 fixture's content already fits the original
    boxes, so apply_dynamic_layout() must add zero extra height —
    pixel-parity guard: this shouldn't regress the common case."""
    from capability_renderer.geometry import H, apply_dynamic_layout

    cfg = json.loads(FIXTURE_CFG.read_text())
    offsets, canvas_height = apply_dynamic_layout(cfg)
    assert canvas_height == H
    assert all(v == 0 for v in offsets.values())


def test_dynamic_layout_grows_canvas_for_long_content_without_overflow():
    """Real (often AI-generated) mission/assessment/coach text runs
    longer than the locked fixture's — the whole card should grow
    downward to fit it rather than let panels draw past their own
    borders. Renders the full pipeline (not just one panel) so the
    cascade through every panel below mission/assessment/verdict is
    exercised end to end."""
    from capability_renderer import render as render_mod
    from capability_renderer.geometry import H, PANEL_BOXES

    cfg = json.loads(FIXTURE_CFG.read_text())
    cfg["success_definition"] = [
        "Hold every mile within ten seconds of the prescribed recovery pace band all the way round",
        "Keep cadence steady above 170 spm even as fatigue accumulates in the closing miles",
        "Finish with heart rate recovery of at least twenty five beats within two minutes",
        "Avoid any single mile split drifting more than thirty seconds off the mission target",
    ]
    cfg["reason"] = (
        "Splits were tight to the recovery band for most of the run, drifting only in the "
        "final mile as fatigue set in on the last climb, a normal pattern for this profile."
    )
    cfg["strength"] = "Excellent pacing discipline through the middle miles on rolling terrain"
    cfg["next_focus"] = (
        "Work on maintaining composure and pace control in the closing stages, particularly "
        "on climbs, where today showed the first signs of drift under fatigue."
    )
    cfg["coach_notes"] = (
        "Cadence solid throughout. Heart rate recovery well managed on the climbs, and the "
        "aerobic engine looked strong across the whole session given the humidity today."
    )
    points = render_mod.parse_gpx(FIXTURE_GPX)

    img, draw, _cfg, _points, paces, theme = _setup()
    computed = {"paces": paces}
    offsets, canvas_height = render_mod.apply_dynamic_layout(cfg)
    assert canvas_height > H, "long content should grow the canvas, not just get clipped"

    from PIL import Image as PILImage
    grown_img = PILImage.new("RGBA", (W, canvas_height), theme["bg"])
    grown_draw = ImageDraw.Draw(grown_img)
    for name, panel in PANEL_ORDER:
        grown_draw = panel.render(
            grown_img, grown_draw, cfg, computed, theme,
            points=points, paces=paces, offset=offsets[name],
        )

    # Nothing should draw past the final panel's (grown) bottom edge.
    footer_box = PANEL_BOXES["footer"]
    below_footer = grown_img.crop((footer_box[0], footer_box[3] + 3, footer_box[2], min(footer_box[3] + 20, canvas_height)))
    px = below_footer.convert("RGB").getdata()
    white_ish = [p for p in px if p[0] > 200 and p[1] > 200 and p[2] > 200]
    assert len(white_ish) == 0, f"Found {len(white_ish)} light/text-coloured pixels below the grown card's footer"
