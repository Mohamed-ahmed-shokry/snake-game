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


def interpolate_snake_positions(state: GameState, movement_alpha: float) -> list[tuple[float, float]]:
    alpha = max(0.0, min(movement_alpha, 1.0))
    if not state.previous_snake:
        return [(float(x), float(y)) for x, y in state.snake]

    positions: list[tuple[float, float]] = []
    for index, (current_x, current_y) in enumerate(state.snake):
        previous_x, previous_y = state.previous_snake[min(index, len(state.previous_snake) - 1)]
        if abs(current_x - previous_x) > 1 or abs(current_y - previous_y) > 1:
            positions.append((float(current_x), float(current_y)))
            continue
        positions.append(
            (
                previous_x + (current_x - previous_x) * alpha,
                previous_y + (current_y - previous_y) * alpha,
            )
        )
    return positions


def calculate_danger_level(state: GameState, config: GameConfig) -> float:
    """Return a 0..1 proximity warning for nearby hazards and arena walls."""
    head_x, head_y = state.snake[0]
    nearest_hazard = min(
        (
            abs(head_x - hazard_x) + abs(head_y - hazard_y)
            for hazard_x, hazard_y in state.obstacles | set(state.snake[2:])
        ),
        default=99,
    )
    hazard_level = max(0.0, min(1.0, (3 - nearest_hazard) / 2))

    wall_level = 0.0
    if state.map_mode.value == "bounded":
        wall_distance = min(
            head_x,
            head_y,
            config.grid_width - 1 - head_x,
            config.grid_height - 1 - head_y,
        )
        wall_level = max(0.0, min(1.0, (2 - wall_distance) / 2))

    return max(hazard_level, wall_level)


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

    def _blit_glow(
        self,
        target: pygame.Surface,
        center: tuple[int, int],
        color: Color,
        radius: int,
        peak_alpha: int,
    ) -> None:
        glow = self.assets.glow_surface(radius, color, peak_alpha)
        target.blit(glow, glow.get_rect(center=center))

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

    def _draw_arena_energy(
        self,
        target: pygame.Surface,
        state: GameState,
        stage: int,
        animation_seconds: float,
        movement_alpha: float,
    ) -> None:
        atmosphere = pygame.Surface(target.get_size(), pygame.SRCALPHA)
        accent = self.theme.palette.accent
        motion_time = 0.0 if self.config.graphics.reduced_motion else animation_seconds

        if self.config.graphics.particles_enabled:
            mote_count = max(14, (self.config.window_width * self.config.window_height) // 26000)
            stage_speed = 10.0 + min(stage, 8) * 1.4
            for index in range(mote_count):
                x = (index * 137 + 61) % self.config.window_width
                base_y = (index * 211 + 89) % self.config.window_height
                y = round(
                    (base_y - motion_time * stage_speed * (1.0 + index % 3 * 0.18))
                    % self.config.window_height
                )
                shimmer = 0.5 + 0.5 * math.sin(motion_time * 2.0 + index * 1.7)
                alpha = 22 + round(shimmer * 32)
                radius = 1 + (index % 7 == 0)
                pygame.draw.circle(atmosphere, (*accent, alpha), (x, y), radius)

            scan_progress = 0.52 if self.config.graphics.reduced_motion else (motion_time * 0.075) % 1.0
            scan_y = round(self.config.window_height * scan_progress)
            scan_glow = max(14, self.config.cell_size)
            for offset in range(-scan_glow, scan_glow + 1, 2):
                strength = 1.0 - abs(offset) / (scan_glow + 1)
                pygame.draw.line(
                    atmosphere,
                    (*accent, round(26 * strength * strength)),
                    (0, scan_y + offset),
                    (self.config.window_width, scan_y + offset),
                )
            pygame.draw.line(
                atmosphere,
                (*accent, 78),
                (0, scan_y),
                (self.config.window_width, scan_y),
                1,
            )

        danger = calculate_danger_level(state, self.config)
        if danger > 0:
            interpolated_head = interpolate_snake_positions(state, movement_alpha)[0]
            head_center = (
                round((interpolated_head[0] + 0.5) * self.config.cell_size),
                round((interpolated_head[1] + 0.5) * self.config.cell_size),
            )
            pulse = (
                0.55
                if self.config.graphics.reduced_motion
                else 0.55 + 0.45 * (math.sin(animation_seconds * 9.0) + 1.0) / 2
            )
            warning_color = (255, 82, 92)
            warning_radius = round(self.config.cell_size * (0.8 + danger * 0.55 + pulse * 0.12))
            self._blit_glow(
                atmosphere,
                head_center,
                warning_color,
                warning_radius * 2,
                round(58 * danger * pulse),
            )
            pygame.draw.circle(
                atmosphere,
                (*warning_color, round(80 + danger * 120)),
                head_center,
                warning_radius,
                max(1, round(2 * danger)),
            )

            if danger >= 0.75:
                edge_depth = max(12, self.config.cell_size)
                for offset in range(edge_depth):
                    alpha = round(28 * danger * pulse * (1.0 - offset / edge_depth) ** 2)
                    pygame.draw.rect(
                        atmosphere,
                        (*warning_color, alpha),
                        pygame.Rect(
                            offset,
                            offset,
                            self.config.window_width - offset * 2,
                            self.config.window_height - offset * 2,
                        ),
                        1,
                    )

        target.blit(atmosphere, (0, 0))

    def _draw_obstacle(self, target: pygame.Surface, cell: Point) -> None:
        cell_rect = self._cell_rect(*cell)
        inset = max(1, self.config.cell_size // 10)
        shape = cell_rect.inflate(-inset * 2, -inset * 2)
        cut = max(2, shape.width // 5)
        points = [
            (shape.left + cut, shape.top),
            (shape.right - cut, shape.top),
            (shape.right, shape.top + cut),
            (shape.right, shape.bottom - cut),
            (shape.right - cut, shape.bottom),
            (shape.left + cut, shape.bottom),
            (shape.left, shape.bottom - cut),
            (shape.left, shape.top + cut),
        ]
        shadow_offset = max(2, inset)
        shadow_points = [(x + shadow_offset, y + shadow_offset) for x, y in points]
        pygame.draw.polygon(target, (7, 9, 13), shadow_points)
        pygame.draw.polygon(target, self.theme.palette.obstacle, points)

        highlight = tuple(min(255, channel + 28) for channel in self.theme.palette.obstacle)
        dark_facet = tuple(max(8, channel - 28) for channel in self.theme.palette.obstacle)
        top_facet = [
            points[0],
            points[1],
            points[2],
            (shape.centerx, shape.centery),
            points[7],
        ]
        side_facet = [
            points[2],
            points[3],
            points[4],
            (shape.centerx, shape.centery),
        ]
        pygame.draw.polygon(target, highlight, top_facet)
        pygame.draw.polygon(target, dark_facet, side_facet)
        pygame.draw.polygon(
            target,
            tuple(max(5, channel // 2) for channel in self.theme.palette.obstacle),
            points,
            max(1, self.config.cell_size // 16),
        )

        crack_sign = -1 if (cell[0] * 7 + cell[1] * 11) % 2 else 1
        crack_color = tuple(max(5, channel // 3) for channel in self.theme.palette.obstacle)
        crack_start = (shape.centerx - crack_sign * shape.width // 5, shape.top + shape.height // 4)
        crack_mid = (shape.centerx + crack_sign * shape.width // 10, shape.centery)
        crack_end = (shape.centerx - crack_sign * shape.width // 8, shape.bottom - shape.height // 5)
        pygame.draw.lines(
            target,
            crack_color,
            False,
            [crack_start, crack_mid, crack_end],
            max(1, self.config.cell_size // 18),
        )

    def _draw_food(self, target: pygame.Surface, animation_seconds: float, position: Point) -> None:
        cell_rect = self._cell_rect(*position)
        pulse = 0 if self.config.graphics.reduced_motion else int(math.sin(animation_seconds * 5.0))
        radius = max(3, self.config.cell_size // 2 - 3 + pulse)
        glow_radius = radius + max(4, self.config.cell_size // 4)
        glow = pygame.Surface((glow_radius * 2 + 2, glow_radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(
            glow,
            (*self.theme.palette.food, 46),
            (glow_radius + 1, glow_radius + 1),
            glow_radius,
        )
        target.blit(glow, (cell_rect.centerx - glow_radius - 1, cell_rect.centery - glow_radius - 1))
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
        type_colors = {
            PowerUpType.SHIELD: self.theme.palette.accent,
            PowerUpType.SLOW_TIME: (112, 184, 255),
            PowerUpType.DOUBLE_SCORE: self.theme.palette.powerup,
            PowerUpType.PHASE: (194, 127, 255),
        }
        ring_color = type_colors[powerup_type]
        glow_radius = radius + 2 + int(pulse * 2)
        glow = pygame.Surface((glow_radius * 2 + 2, glow_radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(
            glow,
            (*ring_color, 62),
            (glow_radius + 1, glow_radius + 1),
            glow_radius,
        )
        target.blit(glow, (cell_rect.centerx - glow_radius - 1, cell_rect.centery - glow_radius - 1))
        pygame.draw.circle(target, (18, 22, 30), cell_rect.center, radius)
        pygame.draw.circle(target, ring_color, cell_rect.center, radius, max(2, radius // 3))

        if not self.config.graphics.reduced_motion:
            orbit_radius = radius + max(3, self.config.cell_size // 6)
            for orbit_index in range(3):
                angle = animation_seconds * 2.4 + orbit_index * (math.pi * 2 / 3)
                orbit_position = (
                    round(cell_rect.centerx + math.cos(angle) * orbit_radius),
                    round(cell_rect.centery + math.sin(angle) * orbit_radius),
                )
                pygame.draw.circle(target, ring_color, orbit_position, max(1, self.config.cell_size // 14))

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
        movement_alpha: float,
    ) -> None:
        base_inset = max(1, self.config.cell_size // 10)
        positions = interpolate_snake_positions(state, movement_alpha)
        centers = [
            (
                round((cell_x + 0.5) * self.config.cell_size),
                round((cell_y + 0.5) * self.config.cell_size),
            )
            for cell_x, cell_y in positions
        ]
        head_rect = pygame.Rect(0, 0, self.config.cell_size, self.config.cell_size)
        head_rect.center = centers[0]
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

        for index in range(len(centers) - 1):
            start = centers[index]
            end = centers[index + 1]
            if abs(start[0] - end[0]) <= self.config.cell_size and abs(start[1] - end[1]) <= self.config.cell_size:
                taper = index / max(1, len(centers) - 1)
                connector_width = max(
                    3,
                    self.config.cell_size - base_inset * 3 - round(taper * self.config.cell_size * 0.16),
                )
                pygame.draw.line(
                    target,
                    (6, 12, 10),
                    (start[0] + 2, start[1] + 3),
                    (end[0] + 2, end[1] + 3),
                    connector_width,
                )
                pygame.draw.line(
                    target,
                    self.theme.palette.snake_body,
                    start,
                    end,
                    connector_width,
                )

        for index in range(len(centers) - 1, -1, -1):
            taper = index / max(1, len(centers) - 1)
            inset = base_inset + round(taper * self.config.cell_size * 0.11)
            cell_rect = pygame.Rect(0, 0, self.config.cell_size, self.config.cell_size)
            cell_rect.center = centers[index]
            shape = cell_rect.inflate(-inset * 2, -inset * 2)
            color = self.theme.palette.snake_head if index == 0 else self.theme.palette.snake_body
            shadow_shape = shape.move(max(2, base_inset), max(2, base_inset))
            pygame.draw.ellipse(target, (6, 11, 10), shadow_shape)
            pygame.draw.ellipse(target, color, shape)
            outline = tuple(max(5, channel // 2) for channel in color)
            pygame.draw.ellipse(target, outline, shape, max(1, self.config.cell_size // 18))
            if index > 0:
                highlight = tuple(min(255, channel + 24) for channel in color)
                sheen = pygame.Rect(
                    shape.left + shape.width // 4,
                    shape.top + max(2, shape.height // 6),
                    max(2, shape.width // 2),
                    max(2, shape.height // 4),
                )
                pygame.draw.ellipse(
                    target,
                    highlight,
                    sheen,
                )

        head_shape = head_rect.inflate(-base_inset * 2, -base_inset * 2)
        direction_x, direction_y = state.direction.vector
        if direction_x:
            head_shape.inflate_ip(max(2, self.config.cell_size // 8), 0)
        else:
            head_shape.inflate_ip(0, max(2, self.config.cell_size // 8))
        pygame.draw.ellipse(target, (6, 11, 10), head_shape.move(2, 3))
        pygame.draw.ellipse(target, self.theme.palette.snake_head, head_shape)
        pygame.draw.ellipse(
            target,
            tuple(max(8, channel // 2) for channel in self.theme.palette.snake_head),
            head_shape,
            max(1, self.config.cell_size // 18),
        )
        head_highlight = pygame.Rect(
            head_shape.left + head_shape.width // 4,
            head_shape.top + max(2, head_shape.height // 7),
            max(3, head_shape.width // 3),
            max(2, head_shape.height // 5),
        )
        pygame.draw.ellipse(
            target,
            tuple(min(255, channel + 38) for channel in self.theme.palette.snake_head),
            head_highlight,
        )

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

        mouth_forward = max(3, self.config.cell_size // 3)
        mouth_half = max(2, self.config.cell_size // 9)
        mouth_center = (
            head_rect.centerx + direction_x * mouth_forward,
            head_rect.centery + direction_y * mouth_forward,
        )
        pygame.draw.line(
            target,
            (18, 70, 42),
            (
                mouth_center[0] - perpendicular_x * mouth_half,
                mouth_center[1] - perpendicular_y * mouth_half,
            ),
            (
                mouth_center[0] + perpendicular_x * mouth_half,
                mouth_center[1] + perpendicular_y * mouth_half,
            ),
            max(1, self.config.cell_size // 16),
        )
        if not self.config.graphics.reduced_motion and math.sin(animation_seconds * 4.2) > 0.82:
            tongue_start = (
                mouth_center[0] + direction_x * 2,
                mouth_center[1] + direction_y * 2,
            )
            tongue_end = (
                tongue_start[0] + direction_x * max(4, self.config.cell_size // 4),
                tongue_start[1] + direction_y * max(4, self.config.cell_size // 4),
            )
            pygame.draw.line(target, self.theme.palette.food, tongue_start, tongue_end, 2)

    def _draw_entities(
        self,
        target: pygame.Surface,
        state: GameState,
        powerup_position: Point | None,
        powerup_type: PowerUpType | None,
        active_powerup_types: set[PowerUpType],
        animation_seconds: float,
        movement_alpha: float,
    ) -> None:
        interpolated_head = interpolate_snake_positions(state, movement_alpha)[0]
        head_center = (
            round((interpolated_head[0] + 0.5) * self.config.cell_size),
            round((interpolated_head[1] + 0.5) * self.config.cell_size),
        )
        self._blit_glow(
            target,
            head_center,
            self.theme.palette.snake_head,
            self.config.cell_size * 2,
            34,
        )
        self._blit_glow(
            target,
            self._cell_rect(*state.food).center,
            self.theme.palette.food,
            self.config.cell_size * 2,
            48,
        )
        if powerup_position is not None:
            self._blit_glow(
                target,
                self._cell_rect(*powerup_position).center,
                self.theme.palette.powerup,
                self.config.cell_size * 2,
                54,
            )

        for obstacle_x, obstacle_y in state.obstacles:
            self._draw_obstacle(target, (obstacle_x, obstacle_y))

        self._draw_food(target, animation_seconds, state.food)

        if powerup_position is not None and powerup_type is not None:
            self._draw_powerup(target, animation_seconds, powerup_position, powerup_type)

        self._draw_snake(
            target,
            state,
            active_powerup_types,
            animation_seconds,
            movement_alpha,
        )

    def _draw_particles(
        self,
        target: pygame.Surface,
        particles: list[tuple[float, float, int, Color, int]],
    ) -> None:
        particle_layer = pygame.Surface(target.get_size(), pygame.SRCALPHA)
        for x, y, radius, color, alpha in particles:
            pygame.draw.circle(
                particle_layer,
                (*color, max(0, min(255, alpha))),
                (int(x), int(y)),
                max(1, int(radius)),
            )
        target.blit(particle_layer, (0, 0))

    def _draw_hud(
        self,
        target: pygame.Surface,
        state: GameState,
        small_font: pygame.font.Font,
        best_score: int,
        stage: int,
        active_effect_labels: list[str],
    ) -> None:
        top_panel = pygame.Rect(8, 6, self.config.window_width - 16, 70)
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

        stage_progress = (state.score % self.config.stage_points_interval) / self.config.stage_points_interval
        progress_track = pygame.Rect(18, top_panel.bottom - 8, self.config.window_width - 36, 3)
        pygame.draw.rect(target, (8, 12, 18), progress_track, border_radius=2)
        if stage_progress > 0:
            progress_fill = progress_track.copy()
            progress_fill.width = max(2, round(progress_track.width * stage_progress))
            pygame.draw.rect(target, self.theme.palette.accent, progress_fill, border_radius=2)

    def _draw_stage_banner(
        self,
        target: pygame.Surface,
        text: str,
        hud_font: pygame.font.Font,
        small_font: pygame.font.Font,
        alpha: int,
    ) -> None:
        safe_alpha = max(0, min(alpha, 210))
        if safe_alpha <= 0:
            return

        center = (self.config.window_width // 2, self.config.window_height // 2)
        elapsed = 1.0 - safe_alpha / 210
        reveal = min(1.0, 0.18 + elapsed * 5.0)
        layer = pygame.Surface(target.get_size(), pygame.SRCALPHA)
        layer.fill((3, 7, 12, round(68 * safe_alpha / 210)))

        ring_base = max(70, self.config.cell_size * 4)
        ring_radius = round(ring_base + elapsed * self.config.cell_size * 8)
        pygame.draw.circle(
            layer,
            (*self.theme.palette.accent, round(safe_alpha * 0.28)),
            center,
            ring_radius,
            2,
        )
        pygame.draw.circle(
            layer,
            (*self.theme.palette.selected_text, round(safe_alpha * 0.16)),
            center,
            ring_radius + max(10, self.config.cell_size),
            1,
        )

        panel_width = min(650, self.config.window_width - 80)
        panel = pygame.Rect(0, 0, round(panel_width * reveal), 174)
        panel.center = center
        draw_panel(
            screen=layer,
            rect=panel,
            fill=(8, 15, 24),
            border=self.theme.palette.accent,
            alpha=round(225 * safe_alpha / 210),
            radius=18,
        )

        accent_half_width = round((panel_width // 2 - 42) * reveal)
        line_y = center[1] - 46
        pygame.draw.line(
            layer,
            (*self.theme.palette.accent, safe_alpha),
            (center[0] - accent_half_width, line_y),
            (center[0] - 56, line_y),
            2,
        )
        pygame.draw.line(
            layer,
            (*self.theme.palette.accent, safe_alpha),
            (center[0] + 56, line_y),
            (center[0] + accent_half_width, line_y),
            2,
        )
        pygame.draw.polygon(
            layer,
            (*self.theme.palette.selected_text, safe_alpha),
            [
                (center[0], line_y - 6),
                (center[0] + 6, line_y),
                (center[0], line_y + 6),
                (center[0] - 6, line_y),
            ],
        )

        eyebrow = small_font.render("SYSTEM  //  STAGE ADVANCE", True, self.theme.palette.accent)
        title = hud_font.render(text.upper(), True, self.theme.palette.text)
        subtitle = small_font.render(
            "SPEED UP  //  ARENA EVOLVED",
            True,
            self.theme.palette.selected_text,
        )
        for surface, y in (
            (eyebrow, center[1] - 65),
            (title, center[1] - 8),
            (subtitle, center[1] + 58),
        ):
            surface.set_alpha(round(255 * safe_alpha / 210))
            layer.blit(surface, surface.get_rect(center=(center[0], y)))

        target.blit(layer, (0, 0))

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
            self._draw_stage_banner(
                target,
                stage_banner_text,
                hud_font,
                small_font,
                stage_banner_alpha,
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
        movement_alpha: float = 1.0,
        stage_banner_text: str | None = None,
        stage_banner_alpha: int = 0,
        flash_alpha: int = 0,
        camera_offset: tuple[int, int] = (0, 0),
        particles: list[tuple[float, float, int, Color, int]] | None = None,
    ) -> None:
        world = pygame.Surface((self.config.window_width, self.config.window_height), pygame.SRCALPHA)
        self._draw_background(world)
        self._draw_grid(world)
        self._draw_arena_border(world, state, animation_seconds)
        self._draw_arena_energy(world, state, stage, animation_seconds, movement_alpha)
        self._draw_entities(
            world,
            state,
            powerup_position,
            powerup_type,
            active_powerup_types or set(),
            animation_seconds,
            movement_alpha,
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
