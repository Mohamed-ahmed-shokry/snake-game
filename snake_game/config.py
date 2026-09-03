import math
from dataclasses import dataclass, field
from pathlib import Path

import pygame

from snake_game.types import Difficulty, Direction, MapMode, ThemeId

COLORBLIND_MODES: tuple[str, ...] = ("off", "deuteranopia", "tritanopia", "high_contrast")
DEFAULT_COLORBLIND_MODE = "off"
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600

DEFAULT_KEY_BINDINGS: dict[str, int] = {
    "move_up": pygame.K_UP,
    "move_down": pygame.K_DOWN,
    "move_left": pygame.K_LEFT,
    "move_right": pygame.K_RIGHT,
    "move_up_alt": pygame.K_w,
    "move_down_alt": pygame.K_s,
    "move_left_alt": pygame.K_a,
    "move_right_alt": pygame.K_d,
    "pause": pygame.K_p,
    "pause_alt": pygame.K_SPACE,
    "mute": pygame.K_m,
    "fullscreen": pygame.K_F11,
    "help": pygame.K_h,
    "menu_back": pygame.K_ESCAPE,
    "confirm": pygame.K_RETURN,
    "confirm_alt": pygame.K_SPACE,
}


def _is_finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _coerce_key(value: object, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    return default


def normalize_colorblind_mode(value: object, default: str = DEFAULT_COLORBLIND_MODE) -> str:
    if not isinstance(value, str):
        return default

    normalized = value.strip().lower()
    if normalized in {"", "none"}:
        return DEFAULT_COLORBLIND_MODE
    if normalized in COLORBLIND_MODES:
        return normalized
    return default


@dataclass(frozen=True, slots=True)
class GameRules:
    base_steps_per_second: float
    speed_increment_per_food: float
    max_steps_per_second: float
    score_per_food: int


@dataclass(slots=True)
class KeyBindings:
    move_up: int = pygame.K_UP
    move_down: int = pygame.K_DOWN
    move_left: int = pygame.K_LEFT
    move_right: int = pygame.K_RIGHT
    move_up_alt: int = pygame.K_w
    move_down_alt: int = pygame.K_s
    move_left_alt: int = pygame.K_a
    move_right_alt: int = pygame.K_d
    pause: int = pygame.K_p
    pause_alt: int = pygame.K_SPACE
    mute: int = pygame.K_m
    fullscreen: int = pygame.K_F11
    help: int = pygame.K_h
    menu_back: int = pygame.K_ESCAPE
    confirm: int = pygame.K_RETURN
    confirm_alt: int = pygame.K_SPACE

    def to_dict(self) -> dict[str, int]:
        return {
            "move_up": self.move_up,
            "move_down": self.move_down,
            "move_left": self.move_left,
            "move_right": self.move_right,
            "move_up_alt": self.move_up_alt,
            "move_down_alt": self.move_down_alt,
            "move_left_alt": self.move_left_alt,
            "move_right_alt": self.move_right_alt,
            "pause": self.pause,
            "pause_alt": self.pause_alt,
            "mute": self.mute,
            "fullscreen": self.fullscreen,
            "help": self.help,
            "menu_back": self.menu_back,
            "confirm": self.confirm,
            "confirm_alt": self.confirm_alt,
        }

    @classmethod
    def from_dict(cls, data: object) -> "KeyBindings":
        if not isinstance(data, dict):
            return cls()
        return cls(
            move_up=_coerce_key(data.get("move_up"), pygame.K_UP),
            move_down=_coerce_key(data.get("move_down"), pygame.K_DOWN),
            move_left=_coerce_key(data.get("move_left"), pygame.K_LEFT),
            move_right=_coerce_key(data.get("move_right"), pygame.K_RIGHT),
            move_up_alt=_coerce_key(data.get("move_up_alt"), pygame.K_w),
            move_down_alt=_coerce_key(data.get("move_down_alt"), pygame.K_s),
            move_left_alt=_coerce_key(data.get("move_left_alt"), pygame.K_a),
            move_right_alt=_coerce_key(data.get("move_right_alt"), pygame.K_d),
            pause=_coerce_key(data.get("pause"), pygame.K_p),
            pause_alt=_coerce_key(data.get("pause_alt"), pygame.K_SPACE),
            mute=_coerce_key(data.get("mute"), pygame.K_m),
            fullscreen=_coerce_key(data.get("fullscreen"), pygame.K_F11),
            help=_coerce_key(data.get("help"), pygame.K_h),
            menu_back=_coerce_key(data.get("menu_back"), pygame.K_ESCAPE),
            confirm=_coerce_key(data.get("confirm"), pygame.K_RETURN),
            confirm_alt=_coerce_key(data.get("confirm_alt"), pygame.K_SPACE),
        )

    def get_direction_keys(self) -> dict[int, Direction]:
        from snake_game.types import Direction

        return {
            self.move_up: Direction.UP,
            self.move_down: Direction.DOWN,
            self.move_left: Direction.LEFT,
            self.move_right: Direction.RIGHT,
            self.move_up_alt: Direction.UP,
            self.move_down_alt: Direction.DOWN,
            self.move_left_alt: Direction.LEFT,
            self.move_right_alt: Direction.RIGHT,
        }


@dataclass(slots=True)
class UserSettings:
    difficulty: Difficulty = Difficulty.NORMAL
    map_mode: MapMode = MapMode.BOUNDED
    obstacles_enabled: bool = False
    muted: bool = False
    key_bindings: KeyBindings = field(default_factory=KeyBindings)


@dataclass(slots=True)
class GraphicsSettings:
    theme_id: ThemeId = ThemeId.NEON
    ui_scale: float = 1.0
    show_grid: bool = True
    particles_enabled: bool = True
    screen_shake_enabled: bool = False
    reduced_motion: bool = False
    colorblind_mode: str = DEFAULT_COLORBLIND_MODE


RULES_BY_DIFFICULTY: dict[Difficulty, GameRules] = {
    Difficulty.EASY: GameRules(
        base_steps_per_second=6.0,
        speed_increment_per_food=0.20,
        max_steps_per_second=12.0,
        score_per_food=1,
    ),
    Difficulty.NORMAL: GameRules(
        base_steps_per_second=8.0,
        speed_increment_per_food=0.35,
        max_steps_per_second=18.0,
        score_per_food=2,
    ),
    Difficulty.HARD: GameRules(
        base_steps_per_second=10.0,
        speed_increment_per_food=0.50,
        max_steps_per_second=24.0,
        score_per_food=3,
    ),
}


def rules_for_difficulty(difficulty: Difficulty) -> GameRules:
    return RULES_BY_DIFFICULTY[difficulty]


@dataclass(slots=True)
class GameConfig:
    window_width: int = 800
    window_height: int = 600
    cell_size: int = 20
    render_fps: int = 60
    max_steps_per_frame: int = 5
    countdown_seconds: float = 3.0
    obstacle_count: int = 14
    leaderboard_limit: int = 10
    stage_points_interval: int = 25
    data_file: str = "data/save.json"
    graphics: GraphicsSettings = field(default_factory=GraphicsSettings)

    background_color: tuple[int, int, int] = (16, 18, 22)
    grid_color: tuple[int, int, int] = (30, 34, 42)
    snake_head_color: tuple[int, int, int] = (106, 219, 130)
    snake_body_color: tuple[int, int, int] = (55, 179, 92)
    obstacle_color: tuple[int, int, int] = (113, 123, 143)
    food_color: tuple[int, int, int] = (233, 88, 81)
    powerup_color: tuple[int, int, int] = (247, 198, 85)
    accent_color: tuple[int, int, int] = (93, 198, 240)
    text_color: tuple[int, int, int] = (236, 239, 244)
    selected_text_color: tuple[int, int, int] = (255, 215, 86)

    @property
    def grid_width(self) -> int:
        return self.window_width // self.cell_size

    @property
    def grid_height(self) -> int:
        return self.window_height // self.cell_size

    def validate(self) -> None:
        for field_name in (
            "window_width",
            "window_height",
            "cell_size",
            "render_fps",
            "max_steps_per_frame",
            "obstacle_count",
            "leaderboard_limit",
            "stage_points_interval",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{field_name} must be an integer")
        if self.window_width <= 0:
            raise ValueError("window_width must be > 0")
        if self.window_height <= 0:
            raise ValueError("window_height must be > 0")
        if self.window_width < MIN_WINDOW_WIDTH:
            raise ValueError(f"window_width must be >= {MIN_WINDOW_WIDTH}")
        if self.window_height < MIN_WINDOW_HEIGHT:
            raise ValueError(f"window_height must be >= {MIN_WINDOW_HEIGHT}")
        if self.cell_size <= 0:
            raise ValueError("cell_size must be > 0")
        if self.window_width % self.cell_size != 0:
            raise ValueError("window_width must be divisible by cell_size")
        if self.window_height % self.cell_size != 0:
            raise ValueError("window_height must be divisible by cell_size")
        if self.grid_width < 8 or self.grid_height < 8:
            raise ValueError("grid dimensions must be at least 8x8 cells")
        if self.render_fps < 1:
            raise ValueError("render_fps must be >= 1")
        if self.max_steps_per_frame < 1:
            raise ValueError("max_steps_per_frame must be >= 1")
        if not _is_finite_number(self.countdown_seconds) or self.countdown_seconds < 0:
            raise ValueError("countdown_seconds must be finite and >= 0")
        if self.obstacle_count < 0:
            raise ValueError("obstacle_count must be >= 0")
        if self.leaderboard_limit < 1:
            raise ValueError("leaderboard_limit must be >= 1")
        if self.stage_points_interval < 1:
            raise ValueError("stage_points_interval must be >= 1")
        if not isinstance(self.data_file, str) or not self.data_file.strip():
            raise ValueError("data_file must not be empty")
        if Path(self.data_file).is_dir():
            raise ValueError("data_file must point to a file, not a directory")
        if not isinstance(self.graphics, GraphicsSettings):
            raise ValueError("graphics must be a GraphicsSettings instance")
        if not isinstance(self.graphics.theme_id, ThemeId):
            raise ValueError("graphics.theme_id must be a ThemeId")
        if not _is_finite_number(self.graphics.ui_scale) or self.graphics.ui_scale <= 0:
            raise ValueError("graphics.ui_scale must be finite and > 0")
        if (
            not isinstance(self.graphics.colorblind_mode, str)
            or self.graphics.colorblind_mode not in COLORBLIND_MODES
        ):
            raise ValueError("graphics.colorblind_mode must be a supported mode")
