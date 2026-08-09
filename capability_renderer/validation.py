"""validation.py — checks.

Owns: validating the incoming JSON config, the parsed GPX points,
referenced image assets, and version compatibility between the
config and this renderer. Every check function returns a list of
human-readable error strings (empty list = valid) rather than
raising, so render.py can decide whether to abort or proceed with
warnings.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Sequence

from .theme import CARD_LAYOUT_VERSION

REQUIRED_CONFIG_FIELDS = [
    "date",
    "report_id",
    "mission",
    "score",
    "status",
    "reason",
    "mission_pace_threshold",
    "mission_percent",
    "distance",
    "time",
    "avg_max_hr",
    "best_quarter",
    "mission_pace_value",
    "mission_pace_unit",
    "strength",
    "next_focus",
]


def validate_config(cfg: dict) -> List[str]:
    """Check the mission-card JSON has every field the locked panels
    read directly (as opposed to fields with in-code fallbacks)."""
    errors = []
    for field in REQUIRED_CONFIG_FIELDS:
        if field not in cfg:
            errors.append(f"Missing required config field: '{field}'")
    if "mission_pace_threshold" in cfg:
        value = cfg["mission_pace_threshold"]
        if not isinstance(value, str) or ":" not in value:
            errors.append("mission_pace_threshold must be a 'MM:SS' string")
    if "score" in cfg and not isinstance(cfg["score"], (int, float, str)):
        errors.append("score must be a number or numeric string")
    return errors


def validate_gpx_points(points: Sequence[dict]) -> List[str]:
    """Check the parsed GPX has enough points to render a route and splits."""
    errors = []
    if len(points) < 2:
        errors.append("GPX contains fewer than two track points")
    missing_coords = [i for i, p in enumerate(points) if p.get("lat") is None or p.get("lon") is None]
    if missing_coords:
        errors.append(f"{len(missing_coords)} GPX point(s) missing lat/lon")
    return errors


def validate_assets(paths: Sequence[Path]) -> List[str]:
    """Check that referenced asset files exist. Missing brand assets
    are treated as warnings by callers (graphics.crest() provides a
    vector fallback), so this only reports — it never blocks a render."""
    warnings = []
    for path in paths:
        if not path.exists():
            warnings.append(f"Asset not found (fallback will be used): {path}")
    return warnings


def validate_version(config_renderer_version: str | None) -> List[str]:
    """Warn if a config was authored against a different card-layout
    version than this renderer implements, so a mismatch is visible
    instead of silently producing an unexpected layout."""
    if config_renderer_version and config_renderer_version != CARD_LAYOUT_VERSION:
        return [
            f"Config was authored for layout v{config_renderer_version}, "
            f"this renderer implements the locked v{CARD_LAYOUT_VERSION} layout"
        ]
    return []
