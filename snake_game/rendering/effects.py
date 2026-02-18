import math

import pygame

type Color = tuple[int, int, int]


def build_vertical_gradient_surface(width: int, height: int, top_color: Color, bottom_color: Color) -> pygame.Surface:
    surface = pygame.Surface((width, height))
    if height <= 1:
        surface.fill(top_color)
        return surface

    for y in range(height):
        ratio = y / (height - 1)
        color = (
            int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio),
            int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio),
            int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio),
        )
        pygame.draw.line(surface, color, (0, y), (width, y))
    return surface


def draw_fade_overlay(screen: pygame.Surface, alpha: int, color: Color = (0, 0, 0)) -> None:
    if alpha <= 0:
        return
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((*color, max(0, min(alpha, 255))))
    screen.blit(overlay, (0, 0))


def pulse_alpha(
    timer_seconds: float,
    min_alpha: int = 90,
    max_alpha: int = 230,
    frequency: float = 5.0,
    reduced_motion: bool = False,
) -> int:
    if reduced_motion:
        return max_alpha
    wave = (math.sin(timer_seconds * frequency) + 1.0) * 0.5
    return int(min_alpha + (max_alpha - min_alpha) * wave)

