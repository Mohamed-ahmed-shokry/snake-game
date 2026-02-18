import pygame

from snake_game.config import GameConfig
from snake_game.state import GameState
from snake_game.types import GameStatus


def draw_centered_text(
    screen: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    center: tuple[int, int],
) -> None:
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=center)
    screen.blit(surface, rect)


def draw_menu_list(
    screen: pygame.Surface,
    lines: list[str],
    selected_index: int,
    top_y: int,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    selected_color: tuple[int, int, int],
    center_x: int,
) -> None:
    for index, line in enumerate(lines):
        text = f"> {line}" if index == selected_index else line
        text_color = selected_color if index == selected_index else color
        draw_centered_text(screen, text, font, text_color, (center_x, top_y + index * 38))


def _draw_cell(
    screen: pygame.Surface,
    cell_x: int,
    cell_y: int,
    cell_size: int,
    color: tuple[int, int, int],
) -> None:
    rect = pygame.Rect(cell_x * cell_size, cell_y * cell_size, cell_size, cell_size)
    pygame.draw.rect(screen, color, rect)


def _draw_grid(screen: pygame.Surface, config: GameConfig) -> None:
    for x in range(0, config.window_width, config.cell_size):
        pygame.draw.line(screen, config.grid_color, (x, 0), (x, config.window_height), 1)
    for y in range(0, config.window_height, config.cell_size):
        pygame.draw.line(screen, config.grid_color, (0, y), (config.window_width, y), 1)


def draw_playfield(
    screen: pygame.Surface,
    state: GameState,
    config: GameConfig,
    hud_font: pygame.font.Font,
    small_font: pygame.font.Font,
    countdown_remaining: float,
) -> None:
    screen.fill(config.background_color)
    _draw_grid(screen, config)

    for obstacle_x, obstacle_y in state.obstacles:
        _draw_cell(screen, obstacle_x, obstacle_y, config.cell_size, config.obstacle_color)

    _draw_cell(
        screen=screen,
        cell_x=state.food[0],
        cell_y=state.food[1],
        cell_size=config.cell_size,
        color=config.food_color,
    )

    for index, (cell_x, cell_y) in enumerate(state.snake):
        color = config.snake_head_color if index == 0 else config.snake_body_color
        _draw_cell(screen, cell_x, cell_y, config.cell_size, color)

    hud_parts = [
        f"Score: {state.score}",
        f"Difficulty: {state.difficulty.label}",
        f"Mode: {state.map_mode.label}",
        f"Obstacles: {'On' if state.obstacles else 'Off'}",
    ]
    hud_text = "   ".join(hud_parts)
    score_surface = small_font.render(hud_text, True, config.text_color)
    screen.blit(score_surface, (12, 8))

    if countdown_remaining > 0 and state.status == GameStatus.RUNNING:
        count_value = max(1, int(countdown_remaining) + 1)
        draw_centered_text(
            screen,
            str(count_value),
            hud_font,
            config.accent_color,
            (config.window_width // 2, config.window_height // 2),
        )

    if state.status == GameStatus.PAUSED:
        draw_centered_text(
            screen,
            "Paused - Press P/Space to resume",
            small_font,
            config.text_color,
            (config.window_width // 2, config.window_height // 2),
        )
