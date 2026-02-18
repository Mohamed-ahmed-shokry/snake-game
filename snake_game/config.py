from dataclasses import dataclass, field

from snake_game.types import Difficulty, MapMode, ThemeId


@dataclass(frozen=True, slots=True)
class GameRules:
    base_steps_per_second: float
    speed_increment_per_food: float
    max_steps_per_second: float
    score_per_food: int


@dataclass(slots=True)
class UserSettings:
    difficulty: Difficulty = Difficulty.NORMAL
    map_mode: MapMode = MapMode.BOUNDED
    obstacles_enabled: bool = False
    muted: bool = False


@dataclass(slots=True)
class GraphicsSettings:
    theme_id: ThemeId = ThemeId.NEON
    ui_scale: float = 1.0
    show_grid: bool = True
    particles_enabled: bool = True
    screen_shake_enabled: bool = False
    reduced_motion: bool = False
    colorblind_mode: str = "off"


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
        if self.window_width % self.cell_size != 0:
            raise ValueError("window_width must be divisible by cell_size")
        if self.window_height % self.cell_size != 0:
            raise ValueError("window_height must be divisible by cell_size")
        if self.grid_width < 8 or self.grid_height < 8:
            raise ValueError("grid dimensions must be at least 8x8 cells")
        if self.max_steps_per_frame < 1:
            raise ValueError("max_steps_per_frame must be >= 1")
        if self.countdown_seconds < 0:
            raise ValueError("countdown_seconds must be >= 0")
        if self.obstacle_count < 0:
            raise ValueError("obstacle_count must be >= 0")
        if self.leaderboard_limit < 1:
            raise ValueError("leaderboard_limit must be >= 1")
        if self.stage_points_interval < 1:
            raise ValueError("stage_points_interval must be >= 1")
        if self.graphics.ui_scale <= 0:
            raise ValueError("graphics.ui_scale must be > 0")
