# capability_renderer

Deterministic Pillow-based renderer for Capability Engine report
cards. Currently produces the mission-snapshot card (locked v1.2
layout); architected to produce other Capability Engine report types
(nutrition, blood pressure, race preview, ...) via `panels/`.

## Data flow

```
JSON + GPX
    │
    ▼
validation.py
    │
    ▼
metrics.py
    │
    ▼
layout.py (used internally by panels as they draw)
    │
    ▼
panels/  ──▶  graphics.py
    │
    ▼
export.py
    │
    ▼
PNG (PDF/SVG planned, v1.5)
```

## Run

```bash
pip install -r requirements.txt
python -m capability_renderer.render --config sample_run.json --gpx run.gpx --output snapshot.png
```

## Test

```bash
PYTHONPATH=. pytest capability_renderer/tests -q
```

## Adding a new report type

Add `panels/<name>.py` with:

```python
def render(img, draw, cfg, metrics, theme, **kwargs):
    ...
    return draw
```

Add its box to `geometry.PANEL_BOXES`, add it to `PANEL_ORDER` in
`render.py`. Nothing else in the package needs to change — the
renderer itself doesn't know what kind of report it's drawing.

## Status

This is the structural refactor of the original single-file
`render.py` / `render-2.py` (v1.2, locked layout) into this package.
See `CHANGELOG.md` for what changed and what's still a known gap.
Roadmap: v1.4 automatic layout / responsive panels / brand assets;
v1.5 theme engine / SVG export; v1.6 interactive dashboards; v2.0
full renderer framework.
