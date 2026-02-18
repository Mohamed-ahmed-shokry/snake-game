import pygame

from snake_game.config import GameConfig
from snake_game.state import GameState
from snake_game.types import GameStatus


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


def render_frame(
    screen: pygame.Surface,
    state: GameState,
    config: GameConfig,
    font: pygame.font.Font,
) -> None:
    screen.fill(config.background_color)
    _draw_grid(screen, config)

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

    score_surface = font.render(f"Score: {state.score}", True, config.text_color)
    screen.blit(score_surface, (12, 8))

    if state.status == GameStatus.PAUSED:
        pause_surface = font.render("Paused - Press P/Space to resume", True, config.text_color)
        pause_rect = pause_surface.get_rect(center=(config.window_width // 2, config.window_height // 2))
        screen.blit(pause_surface, pause_rect)
    elif state.status == GameStatus.GAME_OVER:
        message_surface = font.render("Game Over - Press R to restart", True, config.text_color)
        message_rect = message_surface.get_rect(center=(config.window_width // 2, config.window_height // 2))
        screen.blit(message_surface, message_rect)

