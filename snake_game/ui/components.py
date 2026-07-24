import pygame

from snake_game.rendering.effects import build_vertical_gradient_surface
from snake_game.ui.layout import option_row_rects

type Color = tuple[int, int, int]

_SCENE_BACKGROUND_CACHE: dict[tuple[int, int, Color, Color, Color, Color], pygame.Surface] = {}


def draw_scene_background(
    screen: pygame.Surface,
    top_color: Color,
    bottom_color: Color,
    grid_color: Color,
    accent_color: Color,
) -> None:
    width, height = screen.get_size()
    key = (width, height, top_color, bottom_color, grid_color, accent_color)
    background = _SCENE_BACKGROUND_CACHE.get(key)
    if background is None:
        background = build_vertical_gradient_surface(width, height, top_color, bottom_color)
        decoration = pygame.Surface((width, height), pygame.SRCALPHA)

        spacing = max(48, min(width, height) // 8)
        for x in range(-height, width + height, spacing):
            pygame.draw.line(decoration, (*grid_color, 38), (x, 0), (x - height, height), 1)
        for radius, alpha in ((160, 18), (110, 24), (64, 30)):
            pygame.draw.circle(
                decoration,
                (*accent_color, alpha),
                (width - 34, 36),
                radius,
                max(1, radius // 18),
            )
        pygame.draw.circle(
            decoration,
            (*accent_color, 16),
            (40, height - 10),
            max(90, min(width, height) // 3),
        )
        background.blit(decoration, (0, 0))
        _SCENE_BACKGROUND_CACHE[key] = background
    screen.blit(background, (0, 0))

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
    offset_y: int = 0,
) -> None:
    draw_text_center(screen, title, title_font, title_color, (width // 2, 92 + offset_y))
    draw_text_center(screen, subtitle, body_font, text_color, (width // 2, 132 + offset_y))
    rule_width = min(220, max(80, width // 3))
    rule_y = 151 + offset_y
    pygame.draw.line(
        screen,
        title_color,
        (width // 2 - rule_width // 2, rule_y),
        (width // 2 + rule_width // 2, rule_y),
        2,
    )
    pygame.draw.circle(screen, title_color, (width // 2, rule_y), 4)


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
) -> list[pygame.Rect]:
    row_rects = option_row_rects(
        screen.get_width(),
        start_y,
        len(options),
        row_gap,
        row_width,
        row_height,
    )
    for index, option in enumerate(options):
        row_rect = row_rects[index]
        if index == selected_index:
            shadow = row_rect.move(0, 3)
            draw_panel(
                screen=screen,
                rect=shadow,
                fill=(0, 0, 0),
                border=(0, 0, 0),
                alpha=65,
                radius=10,
            )
            draw_panel(
                screen=screen,
                rect=row_rect,
                fill=(255, 255, 255),
                border=selected_text_color,
                alpha=35,
                radius=10,
            )
            marker = pygame.Rect(row_rect.left + 8, row_rect.top + 7, 4, max(6, row_rect.height - 14))
            pygame.draw.rect(screen, selected_text_color, marker, border_radius=2)
        else:
            draw_panel(
                screen=screen,
                rect=row_rect,
                fill=(8, 12, 18),
                border=tuple(max(18, channel // 5) for channel in text_color),
                alpha=75,
                radius=10,
            )
        draw_text_center(
            screen,
            option,
            font,
            selected_text_color if index == selected_index else text_color,
            (center_x, row_rect.centery),
        )
    return row_rects


def draw_hint_footer(
    screen: pygame.Surface,
    text: str,
    width: int,
    y: int,
    font: pygame.font.Font,
    color: Color,
) -> None:
    surface = font.render(text, True, color)
    padding_x = 16
    panel_rect = surface.get_rect(center=(width // 2, y)).inflate(padding_x * 2, 12)
    draw_panel(
        screen=screen,
        rect=panel_rect,
        fill=(8, 12, 18),
        border=tuple(max(18, channel // 5) for channel in color),
        alpha=92,
        radius=max(8, panel_rect.height // 2),
    )
    screen.blit(surface, surface.get_rect(center=(width // 2, y)))


def draw_save_warning(
    screen: pygame.Surface,
    message: str,
    font: pygame.font.Font,
) -> pygame.Rect:
    text_surface = font.render(message.upper(), True, (255, 242, 238))
    panel_rect = text_surface.get_rect(
        midbottom=(screen.get_width() // 2, screen.get_height() - 12)
    ).inflate(58, 18)
    shadow_rect = panel_rect.move(0, 3)
    draw_panel(
        screen=screen,
        rect=shadow_rect,
        fill=(0, 0, 0),
        border=(0, 0, 0),
        alpha=105,
        radius=12,
    )
    draw_panel(
        screen=screen,
        rect=panel_rect,
        fill=(62, 14, 20),
        border=(255, 102, 94),
        alpha=238,
        radius=12,
    )
    icon_center = (panel_rect.left + 17, panel_rect.centery)
    pygame.draw.circle(screen, (255, 196, 86), icon_center, 8)
    pygame.draw.line(
        screen,
        (62, 14, 20),
        (icon_center[0], icon_center[1] - 4),
        (icon_center[0], icon_center[1] + 1),
        2,
    )
    pygame.draw.circle(screen, (62, 14, 20), (icon_center[0], icon_center[1] + 4), 1)
    text_center = (panel_rect.centerx + 6, panel_rect.centery)
    screen.blit(text_surface, text_surface.get_rect(center=text_center))
    return panel_rect
