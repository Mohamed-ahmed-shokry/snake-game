import pygame


def centered_rect(screen_width: int, top: int, width: int, height: int) -> pygame.Rect:
    left = (screen_width - width) // 2
    return pygame.Rect(left, top, width, height)


def vertical_positions(start_y: int, count: int, gap: int) -> list[int]:
    return [start_y + index * gap for index in range(count)]

