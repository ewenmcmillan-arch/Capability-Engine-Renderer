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
