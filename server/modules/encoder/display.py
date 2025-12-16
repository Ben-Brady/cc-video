from __future__ import annotations
from dataclasses import dataclass


@dataclass
class MonitorDisplay:
    rows: int
    columns: int

    monitorWidth: int
    monitorHeight: int

