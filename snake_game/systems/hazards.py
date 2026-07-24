from __future__ import annotations

import random
from dataclasses import dataclass

from snake_game.types import Point


@dataclass(slots=True)
class HazardSystem:
    enabled: bool = False
    obstacles_per_stage: int = 2
    last_stage: int = 1

    def __post_init__(self) -> None:
        if self.obstacles_per_stage < 0:
            raise ValueError("obstacles_per_stage must be >= 0")
        if self.last_stage < 1:
            raise ValueError("last_stage must be >= 1")

    def advance_to_stage(
        self,
        stage: int,
        obstacles: set[Point],
        forbidden_cells: set[Point],
        grid_width: int,
        grid_height: int,
        rng: random.Random,
    ) -> set[Point]:
        if stage <= self.last_stage:
            return set()

        stages_advanced = stage - self.last_stage
        self.last_stage = stage
        if not self.enabled or self.obstacles_per_stage == 0:
            return set()

        candidates = [
            (x, y)
            for y in range(grid_height)
            for x in range(grid_width)
            if (x, y) not in obstacles and (x, y) not in forbidden_cells
        ]
        rng.shuffle(candidates)
        obstacle_count = min(len(candidates), self.obstacles_per_stage * stages_advanced)
        added = set(candidates[:obstacle_count])
        obstacles.update(added)
        return added
