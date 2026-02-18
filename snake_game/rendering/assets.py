from dataclasses import dataclass, field

import pygame

from snake_game.config import GameConfig
from snake_game.rendering.effects import build_vertical_gradient_surface

type Color = tuple[int, int, int]


@dataclass(slots=True)
class RenderAssets:
    _grid_cache: dict[tuple[int, int, int, Color], pygame.Surface] = field(default_factory=dict)
    _gradient_cache: dict[tuple[int, int, Color, Color], pygame.Surface] = field(default_factory=dict)

    def grid_surface(self, config: GameConfig, grid_color: Color) -> pygame.Surface:
        key = (config.window_width, config.window_height, config.cell_size, grid_color)
        cached = self._grid_cache.get(key)
        if cached is not None:
            return cached

        surface = pygame.Surface((config.window_width, config.window_height), pygame.SRCALPHA)
        for x in range(0, config.window_width, config.cell_size):
            pygame.draw.line(surface, grid_color, (x, 0), (x, config.window_height), 1)
        for y in range(0, config.window_height, config.cell_size):
            pygame.draw.line(surface, grid_color, (0, y), (config.window_width, y), 1)
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

