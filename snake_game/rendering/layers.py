from enum import Enum

import pygame

from snake_game.config import GameConfig
from snake_game.rendering.assets import RenderAssets
from snake_game.state import GameState
from snake_game.types import GameStatus, Point
from snake_game.ui.theme import UiTheme


class RenderLayer(Enum):
    BACKGROUND = 0
    GRID = 1
    ENTITIES = 2
    HUD = 3
    OVERLAY = 4


def _draw_centered_text(
    screen: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    center: tuple[int, int],
) -> None:
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=center)
    screen.blit(surface, rect)


class PlayfieldRenderer:
    def __init__(self, config: GameConfig, theme: UiTheme, assets: RenderAssets) -> None:
        self.config = config
        self.theme = theme
        self.assets = assets

    def _draw_cell(
        self,
        screen: pygame.Surface,
        cell_x: int,
        cell_y: int,
        color: tuple[int, int, int],
    ) -> None:
        rect = pygame.Rect(
            cell_x * self.config.cell_size,
            cell_y * self.config.cell_size,
            self.config.cell_size,
            self.config.cell_size,
        )
        pygame.draw.rect(screen, color, rect)

    def _draw_background(self, screen: pygame.Surface) -> None:
        gradient = self.assets.background_gradient(
            self.config.window_width,
            self.config.window_height,
            self.theme.palette.background_top,
            self.theme.palette.background_bottom,
        )
        screen.blit(gradient, (0, 0))

    def _draw_grid(self, screen: pygame.Surface) -> None:
        if not self.config.graphics.show_grid:
            return
        grid = self.assets.grid_surface(self.config, self.theme.palette.grid)
        screen.blit(grid, (0, 0))

    def _draw_entities(self, screen: pygame.Surface, state: GameState, powerup_position: Point | None) -> None:
        for obstacle_x, obstacle_y in state.obstacles:
            self._draw_cell(screen, obstacle_x, obstacle_y, self.theme.palette.obstacle)

        self._draw_cell(screen, state.food[0], state.food[1], self.theme.palette.food)
        if powerup_position is not None:
            self._draw_cell(screen, powerup_position[0], powerup_position[1], self.theme.palette.powerup)

        for index, (cell_x, cell_y) in enumerate(state.snake):
            color = self.theme.palette.snake_head if index == 0 else self.theme.palette.snake_body
            self._draw_cell(screen, cell_x, cell_y, color)

    def _draw_hud(
        self,
        screen: pygame.Surface,
        state: GameState,
        small_font: pygame.font.Font,
        best_score: int,
        stage: int,
        active_effect_labels: list[str],
    ) -> None:
        hud_parts = [
            f"Score: {state.score}",
            f"Best: {best_score}",
            f"Stage: {stage}",
            f"Difficulty: {state.difficulty.label}",
            f"Mode: {state.map_mode.label}",
            f"Obstacles: {'On' if state.obstacles else 'Off'}",
        ]
        hud_text = "   ".join(hud_parts)
        score_surface = small_font.render(hud_text, True, self.theme.palette.text)
        screen.blit(score_surface, (12, 8))

        if active_effect_labels:
            effects_text = "Effects: " + " | ".join(active_effect_labels)
            effects_surface = small_font.render(effects_text, True, self.theme.palette.accent)
            screen.blit(effects_surface, (12, 32))

    def _draw_overlays(
        self,
        screen: pygame.Surface,
        state: GameState,
        hud_font: pygame.font.Font,
        small_font: pygame.font.Font,
        countdown_remaining: float,
    ) -> None:
        if countdown_remaining > 0 and state.status == GameStatus.RUNNING:
            count_value = max(1, int(countdown_remaining) + 1)
            _draw_centered_text(
                screen,
                str(count_value),
                hud_font,
                self.theme.palette.accent,
                (self.config.window_width // 2, self.config.window_height // 2),
            )

        if state.status == GameStatus.PAUSED:
            _draw_centered_text(
                screen,
                "Paused - Press P/Space to resume",
                small_font,
                self.theme.palette.text,
                (self.config.window_width // 2, self.config.window_height // 2),
            )

    def render(
        self,
        screen: pygame.Surface,
        state: GameState,
        hud_font: pygame.font.Font,
        small_font: pygame.font.Font,
        countdown_remaining: float,
        best_score: int,
        stage: int,
        powerup_position: Point | None,
        active_effect_labels: list[str],
    ) -> None:
        self._draw_background(screen)
        self._draw_grid(screen)
        self._draw_entities(screen, state, powerup_position)
        self._draw_hud(screen, state, small_font, best_score, stage, active_effect_labels)
        self._draw_overlays(screen, state, hud_font, small_font, countdown_remaining)

