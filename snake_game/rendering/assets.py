from dataclasses import dataclass, field

import pygame

from snake_game.config import GameConfig
from snake_game.rendering.effects import build_vertical_gradient_surface

type Color = tuple[int, int, int]


@dataclass(slots=True)
class RenderAssets:
    _grid_cache: dict[tuple[int, int, int, Color], pygame.Surface] = field(default_factory=dict)
    _gradient_cache: dict[tuple[int, int, Color, Color], pygame.Surface] = field(default_factory=dict)
    _arena_cache: dict[tuple[int, int, int, Color, Color, Color], pygame.Surface] = field(default_factory=dict)
    _glow_cache: dict[tuple[int, Color, int], pygame.Surface] = field(default_factory=dict)

    def grid_surface(self, config: GameConfig, grid_color: Color) -> pygame.Surface:
        key = (config.window_width, config.window_height, config.cell_size, grid_color)
        cached = self._grid_cache.get(key)
        if cached is not None:
            return cached

        surface = pygame.Surface((config.window_width, config.window_height), pygame.SRCALPHA)
        major_color = tuple(min(255, channel + 14) for channel in grid_color)
        for x in range(0, config.window_width, config.cell_size):
            is_major = (x // config.cell_size) % 5 == 0
            pygame.draw.line(
                surface,
                (*major_color, 145) if is_major else (*grid_color, 92),
                (x, 0),
                (x, config.window_height),
                2 if is_major else 1,
            )
        for y in range(0, config.window_height, config.cell_size):
            is_major = (y // config.cell_size) % 5 == 0
            pygame.draw.line(
                surface,
                (*major_color, 145) if is_major else (*grid_color, 92),
                (0, y),
                (config.window_width, y),
                2 if is_major else 1,
            )
        self._grid_cache[key] = surface
        return surface

    def background_gradient(self, width: int, height: int, top_color: Color, bottom_color: Color) -> pygame.Surface:
        key = (width, height, top_color, bottom_color)
        cached = self._gradient_cache.get(key)
        if cached is not None:
            return cached
        surface = build_vertical_gradient_surface(width, height, top_color, bottom_color)
        self._gradient_cache[key] = surface
        return surface

    def arena_surface(
        self,
        config: GameConfig,
        top_color: Color,
        bottom_color: Color,
        accent_color: Color,
    ) -> pygame.Surface:
        key = (
            config.window_width,
            config.window_height,
            config.cell_size,
            top_color,
            bottom_color,
            accent_color,
        )
        cached = self._arena_cache.get(key)
        if cached is not None:
            return cached

        surface = self.background_gradient(
            config.window_width,
            config.window_height,
            top_color,
            bottom_color,
        ).copy()
        atmosphere = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        tile_alpha = 10
        for cell_y in range(config.grid_height):
            for cell_x in range(config.grid_width):
                if (cell_x + cell_y) % 2:
                    pygame.draw.rect(
                        atmosphere,
                        (*accent_color, tile_alpha),
                        pygame.Rect(
                            cell_x * config.cell_size,
                            cell_y * config.cell_size,
                            config.cell_size,
                            config.cell_size,
                        ),
                    )

        speck_count = max(12, (config.window_width * config.window_height) // 22000)
        for index in range(speck_count):
            x = (index * 97 + 43) % config.window_width
            y = (index * 173 + 71) % config.window_height
            radius = 1 + (index % 3 == 0)
            alpha = 20 + (index * 11) % 28
            pygame.draw.circle(atmosphere, (*accent_color, alpha), (x, y), radius)

        edge_depth = max(18, config.cell_size * 2)
        for offset in range(edge_depth):
            alpha = int(62 * (1.0 - offset / edge_depth) ** 2)
            pygame.draw.rect(
                atmosphere,
                (0, 0, 0, alpha),
                pygame.Rect(offset, offset, config.window_width - offset * 2, config.window_height - offset * 2),
                1,
            )

        surface.blit(atmosphere, (0, 0))
        self._arena_cache[key] = surface
        return surface

    def glow_surface(self, radius: int, color: Color, peak_alpha: int = 70) -> pygame.Surface:
        safe_radius = max(1, radius)
        safe_alpha = max(0, min(peak_alpha, 255))
        key = (safe_radius, color, safe_alpha)
        cached = self._glow_cache.get(key)
        if cached is not None:
            return cached

        diameter = safe_radius * 2 + 2
        surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = (safe_radius + 1, safe_radius + 1)
        step = max(1, safe_radius // 12)
        for current_radius in range(safe_radius, 0, -step):
            strength = 1.0 - current_radius / safe_radius
            alpha = round(safe_alpha * strength * strength)
            pygame.draw.circle(surface, (*color, alpha), center, current_radius)
        self._glow_cache[key] = surface
        return surface
