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


class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"

    @property
    def label(self) -> str:
        return self.value.capitalize()


class MapMode(Enum):
    BOUNDED = "bounded"
    WRAP = "wrap"

    @property
    def label(self) -> str:
        return self.value.capitalize()


class SceneId(Enum):
    MENU = "menu"
    SETTINGS = "settings"
    PLAY = "play"
    GAME_OVER = "game_over"
