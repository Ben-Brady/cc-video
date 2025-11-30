from __future__ import annotations
from dataclasses import dataclass


@dataclass
class MonitorDisplay:
    rows: int
    columns: int

    monitorWidth: int
    monitorHeight: int

    @staticmethod
    def from_display_string(monitor_str: str) -> "MonitorDisplay|None":
        parts = monitor_str.split("-")
        if len(parts) != 4:
            return None

        monitorRows = int(parts[0])
        monitorColumns = int(parts[1])
        monitorWidth = int(parts[2])
        monitorHeight = int(parts[3])

        return MonitorDisplay(
            rows=monitorRows,
            columns=monitorColumns,
            monitorWidth=monitorWidth,
            monitorHeight=monitorHeight,
        )
