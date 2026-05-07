from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AdviserMode = Literal["off", "explain", "fix_plan", "patch_proposal"]


@dataclass(frozen=True)
class AdviserRequest:
    mode: AdviserMode
    diagnostics: dict[str, object]


@dataclass(frozen=True)
class AdviserResponse:
    problem: str
    why_it_matters: str
    fix: str
    risk: str
    mode: AdviserMode
    applied: bool = False
