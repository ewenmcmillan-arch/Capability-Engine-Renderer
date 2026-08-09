"""models/theme.py — typed view of a loaded colour theme."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Theme:
    name: str
    colors: Dict[str, str]

    def __getitem__(self, key: str) -> str:
        return self.colors[key]

    @classmethod
    def load(cls, name: str = "default") -> "Theme":
        from ..theme import load_theme
        return cls(name=name, colors=load_theme(name))
