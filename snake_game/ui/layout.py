import pygame

BASE_SCENE_HEIGHT = 600


def scene_vertical_offset(screen_height: int) -> int:
    return max(0, (screen_height - BASE_SCENE_HEIGHT) // 2)


def centered_rect(screen_width: int, top: int, width: int, height: int) -> pygame.Rect:
    left = (screen_width - width) // 2
    return pygame.Rect(left, top, width, height)


def vertical_positions(start_y: int, count: int, gap: int) -> list[int]:
    return [start_y + index * gap for index in range(count)]


def option_row_rects(
    screen_width: int,
    start_y: int,
    count: int,
    gap: int,
    row_width: int,
    row_height: int,
) -> list[pygame.Rect]:
    safe_width = min(row_width, max(40, screen_width - 32))
    return [
        centered_rect(screen_width, y - row_height // 2, safe_width, row_height)
        for y in vertical_positions(start_y, count, gap)
    ]


def option_index_at(
    position: tuple[int, int],
    screen_width: int,
    start_y: int,
    count: int,
    gap: int,
    row_width: int,
    row_height: int,
) -> int | None:
    for index, rect in enumerate(
        option_row_rects(screen_width, start_y, count, gap, row_width, row_height)
    ):
        if rect.collidepoint(position):
            return index
    return None
