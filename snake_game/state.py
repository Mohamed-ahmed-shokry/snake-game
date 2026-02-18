from dataclasses import dataclass

from snake_game.types import Difficulty, Direction, GameStatus, MapMode, Point


@dataclass(slots=True)
class GameState:
    snake: list[Point]
    direction: Direction
    pending_direction: Direction | None
    food: Point
    score: int
    status: GameStatus
    steps_per_second: float
    speed_increment_per_food: float
    max_steps_per_second: float
    score_per_food: int
    difficulty: Difficulty
    map_mode: MapMode
    obstacles: set[Point]
    accumulator_seconds: float
