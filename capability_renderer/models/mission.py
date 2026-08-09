"""models/mission.py — typed view of the mission-card config.

A thin dataclass wrapper over the raw JSON dict, giving panels typed
attribute access instead of repeated cfg["..."] / cfg.get("...", ...)
lookups. Construction never fails on a missing optional field —
validation.validate_config() is what enforces required fields, this
model just carries them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Mission:
    date: str
    report_id: str
    mission: str
    score: str
    status: str
    reason: str
    strength: str
    next_focus: str
    mission_subtitle: str = ""
    success_definition: List[str] = field(default_factory=list)
    coach_notes: str = ""

    @classmethod
    def from_config(cls, cfg: dict) -> "Mission":
        return cls(
            date=cfg["date"],
            report_id=cfg["report_id"],
            mission=cfg["mission"],
            score=str(cfg["score"]),
            status=cfg["status"],
            reason=cfg["reason"],
            strength=cfg["strength"],
            next_focus=cfg["next_focus"],
            mission_subtitle=cfg.get("mission_subtitle", ""),
            success_definition=cfg.get("success_definition", []),
            coach_notes=cfg.get("coach_notes", "Cadence solid. Heart rate well managed on the climbs. Good finish."),
        )
