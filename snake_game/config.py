from dataclasses import dataclass


@dataclass(slots=True)
class GameConfig:
    window_width: int = 800
    window_height: int = 600
    cell_size: int = 20
    render_fps: int = 60
    base_steps_per_second: float = 8.0
    speed_increment_per_food: float = 0.35
    max_steps_per_second: float = 18.0
    max_steps_per_frame: int = 5

    background_color: tuple[int, int, int] = (16, 18, 22)
    grid_color: tuple[int, int, int] = (30, 34, 42)
    snake_head_color: tuple[int, int, int] = (106, 219, 130)
    snake_body_color: tuple[int, int, int] = (55, 179, 92)
    food_color: tuple[int, int, int] = (233, 88, 81)
    text_color: tuple[int, int, int] = (236, 239, 244)

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
        if self.base_steps_per_second <= 0:
            raise ValueError("base_steps_per_second must be > 0")
        if self.max_steps_per_second < self.base_steps_per_second:
            raise ValueError("max_steps_per_second must be >= base_steps_per_second")
        if self.max_steps_per_frame < 1:
            raise ValueError("max_steps_per_frame must be >= 1")

