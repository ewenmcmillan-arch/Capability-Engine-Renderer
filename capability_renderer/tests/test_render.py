from pathlib import Path

import pytest
from PIL import Image

from capability_renderer.geometry import H, W
from capability_renderer.render import render

FIXTURE_GPX = Path(__file__).parent / "fixtures_sample.gpx"
FIXTURE_CFG = Path(__file__).parent / "fixtures_sample_config.json"


def test_render_end_to_end_produces_correctly_sized_png(tmp_path):
    output = tmp_path / "out.png"
    result_path = render(FIXTURE_CFG, FIXTURE_GPX, output)
    assert result_path.exists()
    with Image.open(result_path) as img:
        assert img.size == (W, H)


def test_render_rejects_config_missing_required_fields(tmp_path):
    import json
    bad_cfg = tmp_path / "bad.json"
    cfg = json.loads(FIXTURE_CFG.read_text())
    del cfg["score"]
    bad_cfg.write_text(json.dumps(cfg))
    with pytest.raises(ValueError, match="score"):
        render(bad_cfg, FIXTURE_GPX, tmp_path / "out.png")
