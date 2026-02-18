from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

from snake_game.types import Point


class PowerUpType(Enum):
    SHIELD = "shield"
    SLOW_TIME = "slow_time"
    DOUBLE_SCORE = "double_score"
    PHASE = "phase"

    @property
    def label(self) -> str:
        if self == PowerUpType.SLOW_TIME:
            return "Slow"
        if self == PowerUpType.DOUBLE_SCORE:
            return "Double"
        if self == PowerUpType.SHIELD:
            return "Shield"
        return "Phase"


@dataclass(slots=True)
class SpawnedPowerUp:
    type: PowerUpType
    position: Point
    remaining_seconds: float


@dataclass(slots=True)
class ActivePowerUp:
    type: PowerUpType
    remaining_seconds: float


@dataclass(slots=True)
class PowerUpSystem:
    spawn_chance_per_food: float = 0.30
    spawn_lifetime_seconds: float = 10.0
    slow_time_multiplier: float = 0.65
    double_score_multiplier: int = 2
    available_spawn_types: tuple[PowerUpType, ...] = (
        PowerUpType.SHIELD,
        PowerUpType.SLOW_TIME,
        PowerUpType.DOUBLE_SCORE,
        PowerUpType.PHASE,
    )
    effect_duration_seconds: dict[PowerUpType, float] = field(
        default_factory=lambda: {
            PowerUpType.SLOW_TIME: 6.0,
            PowerUpType.DOUBLE_SCORE: 6.0,
            PowerUpType.SHIELD: 10.0,
            PowerUpType.PHASE: 8.0,
        }
    )
    spawned: SpawnedPowerUp | None = None
    active_effects: list[ActivePowerUp] = field(default_factory=list)

    def maybe_spawn(
        self,
        rng: random.Random,
        occupied_cells: set[Point],
        grid_width: int,
        grid_height: int,
    ) -> SpawnedPowerUp | None:
        if self.spawned is not None:
            return None
        if not self.available_spawn_types:
            return None
        if rng.random() > self.spawn_chance_per_food:
            return None

        candidates = [
            (x, y)
            for y in range(grid_height)
            for x in range(grid_width)
            if (x, y) not in occupied_cells
        ]
        if not candidates:
            return None

        chosen_type = rng.choice(list(self.available_spawn_types))
        chosen_position = rng.choice(candidates)
        self.spawned = SpawnedPowerUp(
            type=chosen_type,
            position=chosen_position,
            remaining_seconds=self.spawn_lifetime_seconds,
        )
        return self.spawned

    def collect_at(self, cell: Point) -> ActivePowerUp | None:
        if self.spawned is None or self.spawned.position != cell:
            return None

        collected_type = self.spawned.type
        self.spawned = None
        duration = self.effect_duration_seconds.get(collected_type, 5.0)

        for active in self.active_effects:
            if active.type == collected_type:
                active.remaining_seconds = max(active.remaining_seconds, duration)
                return active

        new_effect = ActivePowerUp(type=collected_type, remaining_seconds=duration)
        self.active_effects.append(new_effect)
        return new_effect

    def consume_effect(self, power_type: PowerUpType) -> bool:
        for index, effect in enumerate(self.active_effects):
            if effect.type == power_type:
                del self.active_effects[index]
                return True
        return False

    def is_active(self, power_type: PowerUpType) -> bool:
        return any(effect.type == power_type for effect in self.active_effects)

    def absorb_fatal_collision(self, reason: str) -> bool:
        if reason not in {"wall", "obstacle", "self_collision"}:
            return False
        return self.consume_effect(PowerUpType.SHIELD)

    def score_multiplier(self) -> int:
        if self.is_active(PowerUpType.DOUBLE_SCORE):
            return self.double_score_multiplier
        return 1

    def speed_multiplier(self) -> float:
        if self.is_active(PowerUpType.SLOW_TIME):
            return self.slow_time_multiplier
        return 1.0

    def phase_active(self) -> bool:
        return self.is_active(PowerUpType.PHASE)

    def active_effect_labels(self) -> list[str]:
        labels: list[str] = []
        for effect in self.active_effects:
            labels.append(f"{effect.type.label} {effect.remaining_seconds:0.1f}s")
        return labels

    def update(self, delta_seconds: float) -> None:
        elapsed = max(0.0, delta_seconds)
        if self.spawned is not None:
            self.spawned.remaining_seconds -= elapsed
            if self.spawned.remaining_seconds <= 0:
                self.spawned = None

        if not self.active_effects:
            return
        for effect in self.active_effects:
            effect.remaining_seconds -= elapsed
        self.active_effects = [effect for effect in self.active_effects if effect.remaining_seconds > 0.0]
