"""models/panel.py — a generic panel descriptor.

This is what makes adding a new card type (e.g. panels/nutrition.py)
not require touching render.py: a Panel just needs a name, a box,
and a render callable with a consistent signature.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Tuple

Box = Tuple[int, int, int, int]


@dataclass
class Panel:
    name: str
    box: Box
    render: Callable  # (draw, image, box, cfg, metrics, theme) -> None
