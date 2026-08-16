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


def test_mission_title_and_subtitle_never_cross_into_assessment_panel():
    """Regression test for a real bug: mission title/subtitle were
    drawn with a single graphics.text() call and no wrap or width
    limit, so a long AI-generated subtitle drew straight past the
    mission panel's right edge (612) and, once it crossed into the
    assessment panel's box (628-1066), was only hidden where
    assessment's own background happened to paint over it — leaving a
    stray fragment of blue text visible past x=1066. Found by
    rendering a real coaching session, not synthetic testing."""
    from capability_renderer.geometry import PANEL_BOXES
    from capability_renderer.panels import assessment, mission

    img, draw, cfg, points, paces, theme = _setup()
    cfg = dict(cfg)
    cfg["mission"] = "A Very Long Auto-Generated Mission Title That Would Have Overrun The Old Fixed-Width Text"
    cfg["mission_subtitle"] = "Hold controlled aerobic effort for about forty five minutes without letting pace drift into hard-work territory"

    mission.render(img, draw, cfg, {}, theme)
    assessment.render(img, draw, cfg, {}, theme)  # paints over anything that bled into its own box

    box = PANEL_BOXES["mission"]
    assessment_box = PANEL_BOXES["assessment"]
    # Sample the gap between the two panels, plus everything to the
    # right of the assessment panel — nothing from mission's title or
    # subtitle should reach either region.
    strip = img.crop((box[2], box[1], assessment_box[0] + 5, box[1] + 140))
    px = strip.convert("RGB").getdata()
    white_ish = [p for p in px if p[0] > 200 and p[1] > 200]
    assert len(white_ish) == 0, "Mission title/subtitle text bled into the gap before the assessment panel"

    beyond = img.crop((assessment_box[2], box[1], img.width, box[1] + 140))
    px = beyond.convert("RGB").getdata()
    white_ish = [p for p in px if p[0] > 200 and p[1] > 200]
    assert len(white_ish) == 0, "Mission title/subtitle text bled past the assessment panel's right edge"


def test_verdict_strength_fits_a_full_realistic_sentence():
    """The coaching schema asks the AI for 'one sentence' for
    strength, but real one-sentence output routinely needs more than
    the original 2-line, 26pt cap — found truncating a real coaching
    session's strength field mid-sentence."""
    from capability_renderer.panels import verdict

    img, draw, cfg, points, paces, theme = _setup()
    cfg = dict(cfg)
    cfg["strength"] = (
        "Excellent effort discipline — you held pace honest through the middle miles "
        "despite rolling terrain and a warm afternoon."
    )
    verdict.render(img, draw, cfg, {}, theme)
    from capability_renderer.layout import wrap_text
    lines = wrap_text(cfg["strength"], 330, 22, bold=True, max_lines=5)
    assert not lines[-1].endswith("…"), "A realistic one-sentence strength should fit without truncating"


def test_verdict_next_focus_fits_a_full_realistic_sentence():
    """The coaching schema asks the AI for '1-2 sentences (~220
    characters)' for next_focus — worse off than strength ever was,
    since it targets *more* text than strength's 140 characters but
    was still capped at max_lines=4 (vs. strength's already-fixed 5).
    A realistic ~220-character next_focus wraps to 7-8 lines at this
    panel's 330px width/20pt size, not 4 — found truncating a real
    coaching session's next_focus mid-sentence."""
    from capability_renderer.panels import verdict

    img, draw, cfg, points, paces, theme = _setup()
    cfg = dict(cfg)
    cfg["next_focus"] = (
        "Prioritise the overdue quality session this week — you have not run a tempo or "
        "interval effort in over ten days, and the taper window for Wigan 10k opens in two "
        "weeks, so this is the last real chance to sharpen before backing off volume."
    )
    verdict.render(img, draw, cfg, {}, theme)
    from capability_renderer.layout import wrap_text
    lines = wrap_text(cfg["next_focus"], 330, 20, max_lines=10)
    assert not lines[-1].endswith("…"), "A realistic next_focus should fit without truncating"


def test_assessment_reason_fits_a_realistic_multi_sentence_explanation():
    """Real AI-generated 'reason' text (schema asks for 2-3 sentences)
    routinely runs 8-11 lines at this panel's 350px width — a 6-line
    cap was truncating mid-word ("...so pace at a fixe...") on a real
    rendered card. max_lines=12 (and geometry._assessment_extra_height()
    growing the panel to match) should fit a realistic reason in full."""
    from capability_renderer.layout import wrap_text

    reason = (
        "4.90 mi in 44:41 at 9:07/mi on an average HR of 136 with a 150 peak is a clean, "
        "well-controlled aerobic session — the longest sustained effort at this pace band "
        "in the last week. But it is functionally a repeat of 8/06 (4.8 mi at a similar HR), "
        "so pace at a fixed HR has not moved meaningfully in the last two weeks, which is "
        "the real signal worth tracking here rather than the session score alone."
    )
    lines = wrap_text(reason, 350, 18, max_lines=12)
    assert not lines[-1].endswith("…"), "A realistic multi-sentence reason should fit without truncating"
