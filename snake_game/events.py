from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class GameEventType(Enum):
    STEP_ADVANCED = "step_advanced"
    FOOD_EATEN = "food_eaten"
    PLAYER_DIED = "player_died"
    STAGE_ADVANCED = "stage_advanced"
    POWERUP_COLLECTED = "powerup_collected"


@dataclass(frozen=True, slots=True)
class GameEvent:
    type: GameEventType
    payload: dict[str, int | float | str | bool] = field(default_factory=dict)


EventEmitter = Callable[[GameEvent], None]


class EventBus:
    def __init__(self) -> None:
        self._queue: deque[GameEvent] = deque()

    def emit(self, event: GameEvent) -> None:
        self._queue.append(event)

    def drain(self) -> list[GameEvent]:
        events = list(self._queue)
        self._queue.clear()
        return events

