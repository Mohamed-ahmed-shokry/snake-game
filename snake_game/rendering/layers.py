import math
from enum import Enum

import pygame

from snake_game.config import GameConfig
from snake_game.rendering.assets import RenderAssets
from snake_game.state import GameState
from snake_game.systems.powerups import PowerUpType
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
        arena = self.assets.arena_surface(
            self.config,
            self.theme.palette.background_top,
            self.theme.palette.background_bottom,
            self.theme.palette.accent,
        )
        target.blit(arena, (0, 0))

    def _draw_grid(self, target: pygame.Surface) -> None:
        if not self.config.graphics.show_grid:
            return
        grid = self.assets.grid_surface(self.config, self.theme.palette.grid)
        target.blit(grid, (0, 0))

    def _draw_arena_border(self, target: pygame.Surface, state: GameState, animation_seconds: float) -> None:
        width = self.config.window_width
        height = self.config.window_height
        if state.map_mode.value == "bounded":
            rail_color = tuple(max(18, channel // 2) for channel in self.theme.palette.obstacle)
            pygame.draw.rect(target, rail_color, pygame.Rect(1, 1, width - 2, height - 2), 5)
            pygame.draw.rect(
                target,
                self.theme.palette.obstacle,
                pygame.Rect(5, 5, width - 10, height - 10),
                2,
            )
            pygame.draw.rect(
                target,
                (*self.theme.palette.text, 65),
                pygame.Rect(7, 7, width - 14, height - 14),
                1,
            )
            return

        dash_length = max(10, self.config.cell_size)
        gap = max(6, self.config.cell_size // 2)
        pulse = 0 if self.config.graphics.reduced_motion else int((math.sin(animation_seconds * 4.0) + 1.0) * 35)
        portal_color = (*self.theme.palette.accent, 135 + pulse)
        for x in range(4, width - 4, dash_length + gap):
            pygame.draw.line(target, portal_color, (x, 4), (min(width - 4, x + dash_length), 4), 3)
            pygame.draw.line(
                target,
                portal_color,
                (x, height - 5),
                (min(width - 4, x + dash_length), height - 5),
                3,
            )
        for y in range(4, height - 4, dash_length + gap):
            pygame.draw.line(target, portal_color, (4, y), (4, min(height - 4, y + dash_length)), 3)
            pygame.draw.line(
                target,
                portal_color,
                (width - 5, y),
                (width - 5, min(height - 4, y + dash_length)),
                3,
            )

    def _draw_obstacle(self, target: pygame.Surface, cell: Point) -> None:
        cell_rect = self._cell_rect(*cell)
        inset = max(1, self.config.cell_size // 10)
        shape = cell_rect.inflate(-inset * 2, -inset * 2)
        shadow = shape.move(max(1, inset), max(1, inset))
        pygame.draw.rect(target, (8, 10, 14), shadow, border_radius=max(2, self.config.cell_size // 4))
        pygame.draw.rect(
            target,
            self.theme.palette.obstacle,
            shape,
            border_radius=max(2, self.config.cell_size // 4),
        )
        highlight = tuple(min(255, channel + 28) for channel in self.theme.palette.obstacle)
        pygame.draw.line(
            target,
            highlight,
            (shape.left + 3, shape.top + 3),
            (shape.right - 4, shape.top + 3),
            max(1, self.config.cell_size // 12),
        )

    def _draw_food(self, target: pygame.Surface, animation_seconds: float, position: Point) -> None:
        cell_rect = self._cell_rect(*position)
        pulse = 0 if self.config.graphics.reduced_motion else int(math.sin(animation_seconds * 5.0))
        radius = max(3, self.config.cell_size // 2 - 3 + pulse)
        shadow_center = (cell_rect.centerx + 2, cell_rect.centery + 2)
        pygame.draw.circle(target, (18, 8, 10), shadow_center, radius)
        pygame.draw.circle(target, self.theme.palette.food, cell_rect.center, radius)
        highlight_radius = max(1, radius // 4)
        pygame.draw.circle(
            target,
            (255, 220, 214),
            (cell_rect.centerx - radius // 3, cell_rect.centery - radius // 3),
            highlight_radius,
        )
        leaf_color = self.theme.palette.snake_head
        pygame.draw.ellipse(
            target,
            leaf_color,
            pygame.Rect(cell_rect.centerx, cell_rect.top + 1, max(3, radius), max(2, radius // 2)),
        )

    def _draw_powerup(
        self,
        target: pygame.Surface,
        animation_seconds: float,
        position: Point,
        powerup_type: PowerUpType,
    ) -> None:
        cell_rect = self._cell_rect(*position)
        pulse = 0.0 if self.config.graphics.reduced_motion else (math.sin(animation_seconds * 6.0) + 1.0) * 0.5
        radius = max(4, self.config.cell_size // 2 - 2)
        glow_radius = radius + 2 + int(pulse * 2)
        glow = pygame.Surface((glow_radius * 2 + 2, glow_radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(
            glow,
            (*self.theme.palette.powerup, 55),
            (glow_radius + 1, glow_radius + 1),
            glow_radius,
        )
        target.blit(glow, (cell_rect.centerx - glow_radius - 1, cell_rect.centery - glow_radius - 1))
        pygame.draw.circle(target, (18, 22, 30), cell_rect.center, radius)
        pygame.draw.circle(target, self.theme.palette.powerup, cell_rect.center, radius, max(2, radius // 3))

        center_x, center_y = cell_rect.center
        glyph_color = self.theme.palette.text
        glyph_radius = max(2, radius // 2)
        if powerup_type == PowerUpType.SHIELD:
            points = [
                (center_x, center_y - glyph_radius),
                (center_x + glyph_radius, center_y - glyph_radius // 2),
                (center_x + glyph_radius // 2, center_y + glyph_radius),
                (center_x, center_y + glyph_radius + 1),
                (center_x - glyph_radius // 2, center_y + glyph_radius),
                (center_x - glyph_radius, center_y - glyph_radius // 2),
            ]
            pygame.draw.polygon(target, glyph_color, points, max(1, radius // 4))
        elif powerup_type == PowerUpType.SLOW_TIME:
            pygame.draw.circle(target, glyph_color, (center_x, center_y), glyph_radius, max(1, radius // 4))
            pygame.draw.line(target, glyph_color, (center_x, center_y), (center_x, center_y - glyph_radius + 1), 1)
            pygame.draw.line(target, glyph_color, (center_x, center_y), (center_x + glyph_radius - 1, center_y), 1)
        elif powerup_type == PowerUpType.DOUBLE_SCORE:
            offset = max(2, glyph_radius // 2)
            pygame.draw.circle(target, glyph_color, (center_x - offset, center_y), max(2, glyph_radius // 2), 1)
            pygame.draw.circle(target, glyph_color, (center_x + offset, center_y), max(2, glyph_radius // 2), 1)
        else:
            pygame.draw.arc(
                target,
                glyph_color,
                pygame.Rect(
                    center_x - glyph_radius,
                    center_y - glyph_radius,
                    glyph_radius * 2,
                    glyph_radius * 2,
                ),
                math.pi * 0.15,
                math.pi * 1.25,
                max(1, radius // 4),
            )
            pygame.draw.circle(target, glyph_color, (center_x, center_y), max(1, glyph_radius // 3))

    def _draw_snake(
        self,
        target: pygame.Surface,
        state: GameState,
        active_powerup_types: set[PowerUpType],
        animation_seconds: float,
    ) -> None:
        inset = max(1, self.config.cell_size // 10)
        head_rect = self._cell_rect(*state.snake[0])
        head_center = head_rect.center
        motion_pulse = 0.0 if self.config.graphics.reduced_motion else (math.sin(animation_seconds * 7.0) + 1.0) * 0.5

        if PowerUpType.SHIELD in active_powerup_types:
            shield_layer = pygame.Surface(target.get_size(), pygame.SRCALPHA)
            shield_radius = self.config.cell_size // 2 + 4 + int(motion_pulse * 2)
            pygame.draw.circle(shield_layer, (120, 210, 255, 42), head_center, shield_radius)
            pygame.draw.circle(shield_layer, (120, 210, 255, 210), head_center, shield_radius, 2)
            target.blit(shield_layer, (0, 0))
        if PowerUpType.SLOW_TIME in active_powerup_types:
            slow_radius = self.config.cell_size // 2 + 2
            pygame.draw.arc(
                target,
                (112, 184, 255),
                pygame.Rect(
                    head_center[0] - slow_radius,
                    head_center[1] - slow_radius,
                    slow_radius * 2,
                    slow_radius * 2,
                ),
                animation_seconds % (math.pi * 2),
                animation_seconds % (math.pi * 2) + math.pi * 1.4,
                2,
            )
        if PowerUpType.DOUBLE_SCORE in active_powerup_types:
            sparkle_offset = self.config.cell_size // 2 + 3
            for offset_x, offset_y in ((-sparkle_offset, 0), (sparkle_offset, 0), (0, -sparkle_offset)):
                pygame.draw.circle(
                    target,
                    self.theme.palette.powerup,
                    (head_center[0] + offset_x, head_center[1] + offset_y),
                    max(1, self.config.cell_size // 12 + int(motion_pulse)),
                )
        if PowerUpType.PHASE in active_powerup_types:
            phase_layer = pygame.Surface(target.get_size(), pygame.SRCALPHA)
            phase_radius = self.config.cell_size // 2 + 5
            pygame.draw.circle(
                phase_layer,
                (*self.theme.palette.accent, 90),
                (head_center[0] - 3, head_center[1]),
                phase_radius,
                2,
            )
            pygame.draw.circle(
                phase_layer,
                (*self.theme.palette.powerup, 90),
                (head_center[0] + 3, head_center[1]),
                phase_radius,
                2,
            )
            target.blit(phase_layer, (0, 0))

        for index in range(len(state.snake) - 1):
            start = self._cell_rect(*state.snake[index]).center
            end = self._cell_rect(*state.snake[index + 1]).center
            if abs(start[0] - end[0]) <= self.config.cell_size and abs(start[1] - end[1]) <= self.config.cell_size:
                pygame.draw.line(
                    target,
                    self.theme.palette.snake_body,
                    start,
                    end,
                    max(3, self.config.cell_size - inset * 3),
                )

        for index in range(len(state.snake) - 1, -1, -1):
            cell_rect = self._cell_rect(*state.snake[index])
            shape = cell_rect.inflate(-inset * 2, -inset * 2)
            color = self.theme.palette.snake_head if index == 0 else self.theme.palette.snake_body
            radius = max(2, self.config.cell_size // (3 if index == 0 else 4))
            pygame.draw.rect(target, (7, 12, 11), shape.move(2, 2), border_radius=radius)
            pygame.draw.rect(target, color, shape, border_radius=radius)
            if index > 0:
                highlight = tuple(min(255, channel + 24) for channel in color)
                pygame.draw.line(
                    target,
                    highlight,
                    (shape.left + 3, shape.top + 3),
                    (shape.right - 4, shape.top + 3),
                    1,
                )

        direction_x, direction_y = state.direction.vector
        perpendicular_x, perpendicular_y = -direction_y, direction_x
        forward = max(2, self.config.cell_size // 5)
        spread = max(2, self.config.cell_size // 5)
        eye_radius = max(1, self.config.cell_size // 12)
        for side in (-1, 1):
            eye_x = head_rect.centerx + direction_x * forward + perpendicular_x * spread * side
            eye_y = head_rect.centery + direction_y * forward + perpendicular_y * spread * side
            pygame.draw.circle(target, (248, 252, 255), (eye_x, eye_y), eye_radius + 1)
            pygame.draw.circle(
                target,
                (12, 18, 20),
                (eye_x + direction_x, eye_y + direction_y),
                eye_radius,
            )

    def _draw_entities(
        self,
        target: pygame.Surface,
        state: GameState,
        powerup_position: Point | None,
        powerup_type: PowerUpType | None,
        active_powerup_types: set[PowerUpType],
        animation_seconds: float,
    ) -> None:
        for obstacle_x, obstacle_y in state.obstacles:
            self._draw_obstacle(target, (obstacle_x, obstacle_y))

        self._draw_food(target, animation_seconds, state.food)

        if powerup_position is not None and powerup_type is not None:
            self._draw_powerup(target, animation_seconds, powerup_position, powerup_type)

        self._draw_snake(target, state, active_powerup_types, animation_seconds)

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
        top_panel = pygame.Rect(8, 6, self.config.window_width - 16, 64)
        draw_panel(
            screen=target,
            rect=top_panel,
            fill=(20, 20, 20),
            border=self.theme.palette.grid,
            alpha=150,
            radius=12,
        )

        stats = [
            ("SCORE", state.score, self.theme.palette.snake_head),
            ("BEST", best_score, self.theme.palette.selected_text),
            ("STAGE", stage, self.theme.palette.accent),
        ]
        chip_x = 16
        for label, value, color in stats:
            text_surface = small_font.render(f"{label}  {value}", True, color)
            chip_rect = text_surface.get_rect(topleft=(chip_x + 10, 14)).inflate(20, 8)
            draw_panel(
                screen=target,
                rect=chip_rect,
                fill=(8, 12, 18),
                border=tuple(max(24, channel // 3) for channel in color),
                alpha=175,
                radius=chip_rect.height // 2,
            )
            target.blit(text_surface, text_surface.get_rect(center=chip_rect.center))
            chip_x = chip_rect.right + 8

        context_text = (
            f"{state.difficulty.label.upper()}  |  {state.map_mode.label.upper()}  |  "
            f"{'HAZARDS' if state.obstacles else 'CLEAR'}"
        )
        context_surface = small_font.render(context_text, True, self.theme.palette.text)
        context_rect = context_surface.get_rect(topright=(self.config.window_width - 18, 17))
        if context_rect.left > chip_x:
            target.blit(context_surface, context_rect)

        if active_effect_labels:
            effect_x = 18
            for label in active_effect_labels:
                effect_surface = small_font.render(label, True, self.theme.palette.accent)
                effect_rect = effect_surface.get_rect(topleft=(effect_x + 8, 43)).inflate(16, 4)
                if effect_rect.right > self.config.window_width - 16:
                    break
                draw_panel(
                    screen=target,
                    rect=effect_rect,
                    fill=(8, 16, 22),
                    border=self.theme.palette.accent,
                    alpha=150,
                    radius=effect_rect.height // 2,
                )
                target.blit(effect_surface, effect_surface.get_rect(center=effect_rect.center))
                effect_x = effect_rect.right + 6

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
            shade = pygame.Surface(target.get_size(), pygame.SRCALPHA)
            shade.fill((5, 8, 14, 105))
            target.blit(shade, (0, 0))
            pygame.draw.circle(
                target,
                (*self.theme.palette.accent, 55),
                (self.config.window_width // 2, self.config.window_height // 2),
                max(54, self.config.cell_size * 4),
            )
            _draw_centered_text(
                target,
                str(count_value),
                hud_font,
                self.theme.palette.accent,
                (self.config.window_width // 2, self.config.window_height // 2),
            )

        if state.status == GameStatus.PAUSED:
            shade = pygame.Surface(target.get_size(), pygame.SRCALPHA)
            shade.fill((4, 7, 12, 175))
            target.blit(shade, (0, 0))
            panel = pygame.Rect(
                self.config.window_width // 2 - 230,
                self.config.window_height // 2 - 78,
                460,
                156,
            )
            draw_panel(
                screen=target,
                rect=panel,
                fill=(12, 18, 26),
                border=self.theme.palette.accent,
                alpha=235,
                radius=18,
            )
            _draw_centered_text(
                target,
                "PAUSED",
                hud_font,
                self.theme.palette.accent,
                (self.config.window_width // 2, self.config.window_height // 2 - 24),
            )
            _draw_centered_text(
                target,
                "Press P or Space to resume  |  Esc for menu",
                small_font,
                self.theme.palette.text,
                (self.config.window_width // 2, self.config.window_height // 2 + 30),
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
        powerup_type: PowerUpType | None,
        active_effect_labels: list[str],
        active_powerup_types: set[PowerUpType] | None = None,
        animation_seconds: float = 0.0,
        stage_banner_text: str | None = None,
        stage_banner_alpha: int = 0,
        flash_alpha: int = 0,
        camera_offset: tuple[int, int] = (0, 0),
        particles: list[tuple[float, float, int, Color]] | None = None,
    ) -> None:
        world = pygame.Surface((self.config.window_width, self.config.window_height), pygame.SRCALPHA)
        self._draw_background(world)
        self._draw_grid(world)
        self._draw_arena_border(world, state, animation_seconds)
        self._draw_entities(
            world,
            state,
            powerup_position,
            powerup_type,
            active_powerup_types or set(),
            animation_seconds,
        )
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
        screen.fill(self.theme.palette.background_top)
        screen.blit(world, camera_offset)
