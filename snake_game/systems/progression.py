from __future__ import annotations

from dataclasses import dataclass

from snake_game.events import EventEmitter, GameEvent, GameEventType


@dataclass(slots=True)
class StageProgression:
    points_per_stage: int
    current_stage: int = 1

    def stage_for_score(self, score: int) -> int:
        return max(1, (score // self.points_per_stage) + 1)

    def update_from_score(self, score: int, emit: EventEmitter | None = None) -> bool:
        target_stage = self.stage_for_score(score)
        if target_stage <= self.current_stage:
            return False

        for stage in range(self.current_stage + 1, target_stage + 1):
            self.current_stage = stage
            if emit is not None:
                emit(
                    GameEvent(
                        type=GameEventType.STAGE_ADVANCED,
                        payload={"stage": stage, "score": score},
                    )
                )
        return True

