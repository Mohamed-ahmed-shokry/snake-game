from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class HazardSystem:
    enabled: bool = False
    tick_counter: int = 0

    def update(self) -> None:
        if not self.enabled:
            return
        self.tick_counter += 1

