from dataclasses import dataclass

from snake_game.types import Direction, GameStatus, Point


@dataclass(slots=True)
class GameState:
    snake: list[Point]
    direction: Direction
    pending_direction: Direction | None
    food: Point
    score: int
    status: GameStatus
    steps_per_second: float
    accumulator_seconds: float

