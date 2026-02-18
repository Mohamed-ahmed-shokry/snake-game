from enum import Enum

import pygame

from snake_game.config import GameConfig
from snake_game.rendering.assets import RenderAssets
from snake_game.state import GameState
from snake_game.types import GameStatus, Point
from snake_game.ui.components import draw_panel
from snake_game.ui.theme import UiTheme

type Color = tuple[int, int, int]


class RenderLayer(Enum):
    BACKGROUND = 0
    GRID = 1
    ENTITIES = 2
    PARTICLES = 3
    HUD = 4
    OVERLAY = 5


def _draw_centered_text(
    screen: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: Color,
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

    def _cell_rect(self, cell_x: int, cell_y: int) -> pygame.Rect:
        return pygame.Rect(
            cell_x * self.config.cell_size,
            cell_y * self.config.cell_size,
            self.config.cell_size,
            self.config.cell_size,
        )

    def _draw_background(self, target: pygame.Surface) -> None:
        gradient = self.assets.background_gradient(
            self.config.window_width,
            self.config.window_height,
            self.theme.palette.background_top,
            self.theme.palette.background_bottom,
        )
        target.blit(gradient, (0, 0))

    def _draw_grid(self, target: pygame.Surface) -> None:
        if not self.config.graphics.show_grid:
            return
        grid = self.assets.grid_surface(self.config, self.theme.palette.grid)
        target.blit(grid, (0, 0))

    def _draw_entities(self, target: pygame.Surface, state: GameState, powerup_position: Point | None) -> None:
        for obstacle_x, obstacle_y in state.obstacles:
            obstacle_rect = self._cell_rect(obstacle_x, obstacle_y)
            pygame.draw.rect(target, self.theme.palette.obstacle, obstacle_rect, border_radius=6)

        food_rect = self._cell_rect(state.food[0], state.food[1])
        pygame.draw.circle(target, self.theme.palette.food, food_rect.center, self.config.cell_size // 2 - 2)

        if powerup_position is not None:
            power_rect = self._cell_rect(powerup_position[0], powerup_position[1])
            pygame.draw.circle(target, self.theme.palette.powerup, power_rect.center, self.config.cell_size // 2 - 2)

        for index, (cell_x, cell_y) in enumerate(state.snake):
            cell_rect = self._cell_rect(cell_x, cell_y)
            color = self.theme.palette.snake_head if index == 0 else self.theme.palette.snake_body
            radius = 8 if index == 0 else 5
            pygame.draw.rect(target, color, cell_rect.inflate(-2, -2), border_radius=radius)

    def _draw_particles(
        self,
        target: pygame.Surface,
        particles: list[tuple[float, float, int, Color]],
    ) -> None:
        for x, y, radius, color in particles:
            pygame.draw.circle(target, color, (int(x), int(y)), max(1, int(radius)))

    def _draw_hud(
        self,
        target: pygame.Surface,
        state: GameState,
        small_font: pygame.font.Font,
        best_score: int,
        stage: int,
        active_effect_labels: list[str],
    ) -> None:
        top_panel = pygame.Rect(8, 6, self.config.window_width - 16, 54)
        draw_panel(
            screen=target,
            rect=top_panel,
            fill=(20, 20, 20),
            border=self.theme.palette.grid,
            alpha=150,
            radius=12,
        )

        hud_parts = [
            f"Score {state.score}",
            f"Best {best_score}",
            f"Stage {stage}",
            state.difficulty.label,
            state.map_mode.label,
            "Obs On" if state.obstacles else "Obs Off",
        ]
        hud_text = "  |  ".join(hud_parts)
        score_surface = small_font.render(hud_text, True, self.theme.palette.text)
        target.blit(score_surface, (18, 14))

        if active_effect_labels:
            effects_text = "Effects: " + "   ".join(active_effect_labels)
            effects_surface = small_font.render(effects_text, True, self.theme.palette.accent)
            target.blit(effects_surface, (18, 36))

    def _draw_overlays(
        self,
        target: pygame.Surface,
        state: GameState,
        hud_font: pygame.font.Font,
        small_font: pygame.font.Font,
        countdown_remaining: float,
        stage_banner_text: str | None,
        stage_banner_alpha: int,
        flash_alpha: int,
    ) -> None:
        if countdown_remaining > 0 and state.status == GameStatus.RUNNING:
            count_value = max(1, int(countdown_remaining) + 1)
            _draw_centered_text(
                target,
                str(count_value),
                hud_font,
                self.theme.palette.accent,
                (self.config.window_width // 2, self.config.window_height // 2),
            )

        if state.status == GameStatus.PAUSED:
            _draw_centered_text(
                target,
                "Paused - Press P/Space to resume",
                small_font,
                self.theme.palette.text,
                (self.config.window_width // 2, self.config.window_height // 2),
            )

        if stage_banner_text and stage_banner_alpha > 0:
            banner = pygame.Surface((self.config.window_width, 56), pygame.SRCALPHA)
            banner.fill((*self.theme.palette.accent, max(0, min(stage_banner_alpha, 255))))
            target.blit(banner, (0, self.config.window_height // 2 - 28))
            _draw_centered_text(
                target,
                stage_banner_text,
                small_font,
                self.theme.palette.background_top,
                (self.config.window_width // 2, self.config.window_height // 2),
            )

        if flash_alpha > 0:
            flash = pygame.Surface((self.config.window_width, self.config.window_height), pygame.SRCALPHA)
            flash.fill((255, 255, 255, max(0, min(flash_alpha, 180))))
            target.blit(flash, (0, 0))

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
        stage_banner_text: str | None = None,
        stage_banner_alpha: int = 0,
        flash_alpha: int = 0,
        camera_offset: tuple[int, int] = (0, 0),
        particles: list[tuple[float, float, int, Color]] | None = None,
    ) -> None:
        world = pygame.Surface((self.config.window_width, self.config.window_height), pygame.SRCALPHA)
        self._draw_background(world)
        self._draw_grid(world)
        self._draw_entities(world, state, powerup_position)
        if particles:
            self._draw_particles(world, particles)
        self._draw_hud(world, state, small_font, best_score, stage, active_effect_labels)
        self._draw_overlays(
            world,
            state,
            hud_font,
            small_font,
            countdown_remaining,
            stage_banner_text,
            stage_banner_alpha,
            flash_alpha,
        )
        screen.blit(world, camera_offset)

