import pygame

from snake_game.ui.layout import centered_rect, vertical_positions

type Color = tuple[int, int, int]


def draw_text_center(
    screen: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: Color,
    center: tuple[int, int],
) -> None:
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=center)
    screen.blit(surface, rect)


def draw_panel(
    screen: pygame.Surface,
    rect: pygame.Rect,
    fill: Color,
    border: Color,
    alpha: int = 170,
    radius: int = 14,
) -> None:
    overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(overlay, (*fill, alpha), pygame.Rect(0, 0, rect.width, rect.height), border_radius=radius)
    pygame.draw.rect(overlay, border, pygame.Rect(0, 0, rect.width, rect.height), width=2, border_radius=radius)
    screen.blit(overlay, rect.topleft)


def draw_scene_header(
    screen: pygame.Surface,
    width: int,
    title: str,
    subtitle: str,
    title_font: pygame.font.Font,
    body_font: pygame.font.Font,
    title_color: Color,
    text_color: Color,
) -> None:
    draw_text_center(screen, title, title_font, title_color, (width // 2, 92))
    draw_text_center(screen, subtitle, body_font, text_color, (width // 2, 132))


def draw_option_rows(
    screen: pygame.Surface,
    options: list[str],
    selected_index: int,
    center_x: int,
    start_y: int,
    row_gap: int,
    font: pygame.font.Font,
    text_color: Color,
    selected_text_color: Color,
    row_width: int = 520,
    row_height: int = 34,
) -> None:
    y_positions = vertical_positions(start_y, len(options), row_gap)
    for index, option in enumerate(options):
        row_rect = centered_rect(screen.get_width(), y_positions[index] - row_height // 2, row_width, row_height)
        if index == selected_index:
            draw_panel(
                screen=screen,
                rect=row_rect,
                fill=(255, 255, 255),
                border=selected_text_color,
                alpha=35,
                radius=10,
            )
        draw_text_center(
            screen,
            f"> {option}" if index == selected_index else option,
            font,
            selected_text_color if index == selected_index else text_color,
            (center_x, y_positions[index]),
        )


def draw_hint_footer(
    screen: pygame.Surface,
    text: str,
    width: int,
    y: int,
    font: pygame.font.Font,
    color: Color,
) -> None:
    draw_text_center(screen, text, font, color, (width // 2, y))

