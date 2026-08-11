"""render.py — the conductor.

Does little more than: read JSON -> validate -> calculate metrics ->
build panel layouts -> render panels -> export image. No calculations
(metrics.py), no layout (layout.py), no graphics (graphics.py) belong
here — this module only sequences calls to those.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw

from . import export, metrics as metrics_mod, panels, validation
from .geometry import W, H
from .theme import load_theme

# Panel render order — matches the locked v1.2 draw order exactly.
# Adding a new card section means adding one entry here and a
# matching panels/<name>.py module; nothing else in this file changes.
PANEL_ORDER = [
    panels.header,
    panels.mission,
    panels.assessment,
    panels.trace,
    panels.verdict,
    panels.summary,
    panels.splits,
    panels.recovery,
    panels.elevation,
    panels.footer,
]


def parse_gpx(path) -> list[dict]:
    points = []
    for elem in ET.parse(path).getroot().iter():
        if not elem.tag.endswith("trkpt"):
            continue
        point = {
            "lat": float(elem.attrib["lat"]),
            "lon": float(elem.attrib["lon"]),
            "time": None,
            "ele": None,
            "hr": None,
            "cad": None,
        }
        for child in elem.iter():
            if child.tag.endswith("time") and child.text:
                try:
                    point["time"] = datetime.fromisoformat(child.text.replace("Z", "+00:00"))
                except ValueError:
                    pass
            elif child.tag.endswith("ele") and child.text:
                try:
                    point["ele"] = float(child.text)
                except ValueError:
                    pass
            elif child.tag.endswith("hr") and child.text:
                try:
                    point["hr"] = int(float(child.text))
                except ValueError:
                    pass
            elif child.tag.endswith("cad") and child.text:
                try:
                    point["cad"] = int(float(child.text))
                except ValueError:
                    pass
        points.append(point)
    return points


def render(config_path, gpx_path, output_path, theme_name: str = "default") -> Path:
    # 1. Read
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
    points = parse_gpx(gpx_path)

    # 2. Validate
    errors = validation.validate_config(cfg) + validation.validate_gpx_points(points)
    if errors:
        raise ValueError("Validation failed:\n" + "\n".join(f"- {e}" for e in errors))

    # 3. Calculate metrics
    paces = metrics_mod.smoothed_paces(points)
    splits = cfg.get("splits") or metrics_mod.split_rows(points)
    hr_recovery = metrics_mod.hr_recovery(cfg)
    cadence = metrics_mod.cadence_summary(points)
    elevation = metrics_mod.elevation_summary(points)
    computed_metrics = {
        "paces": paces,
        "splits": splits,
        "hr_recovery": hr_recovery,
        "cadence": cadence,
        "elevation": elevation,
    }

    # 4. Layout (panel boxes are the locked geometry; panels do their
    #    own internal text layout via layout.py as they draw)
    theme = load_theme(theme_name)

    # 5. Render panels
    img = Image.new("RGBA", (W, H), theme["bg"])
    draw = ImageDraw.Draw(img)
    for panel in PANEL_ORDER:
        draw = panel.render(img, draw, cfg, computed_metrics, theme, points=points, paces=paces)

    # 6. Export
    return export.export_png(img, output_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a Capability Engine mission snapshot card.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--gpx", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--theme", default="default")
    args = parser.parse_args()
    try:
        render(args.config, args.gpx, args.output, args.theme)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
