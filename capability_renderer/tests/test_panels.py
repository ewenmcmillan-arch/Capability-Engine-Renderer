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
    for panel in PANEL_ORDER:
        draw = panel.render(img, draw, cfg, computed, theme, points=points, paces=paces)
        assert draw is not None


def test_panel_order_matches_locked_layout_sections():
    names = [p.__name__.rsplit(".", 1)[-1] for p in PANEL_ORDER]
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
