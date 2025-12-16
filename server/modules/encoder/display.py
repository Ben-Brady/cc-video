from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MonitorDisplay:
    rows: int
    columns: int

    monitorWidth: int
    monitorHeight: int

