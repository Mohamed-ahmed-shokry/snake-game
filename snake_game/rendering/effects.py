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

