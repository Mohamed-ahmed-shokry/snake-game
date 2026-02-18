from enum import Enum

type Point = tuple[int, int]


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def vector(self) -> Point:
        return self.value


class GameStatus(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    GAME_OVER = "game_over"

