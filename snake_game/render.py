import pygame

from snake_game.config import GameConfig
from snake_game.rendering.assets import RenderAssets
from snake_game.rendering.layers import PlayfieldRenderer
from snake_game.state import GameState
from snake_game.types import Point
from snake_game.ui.theme import resolve_theme

_SHARED_ASSETS = RenderAssets()
_PLAYFIELD_RENDERERS: dict[tuple[int, int, int, str, bool], PlayfieldRenderer] = {}


def draw_centered_text(
    screen: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    center: tuple[int, int],
) -> None:
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=center)
    screen.blit(surface, rect)


def draw_menu_list(
    screen: pygame.Surface,
    lines: list[str],
    selected_index: int,
    top_y: int,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    selected_color: tuple[int, int, int],
    center_x: int,
) -> None:
    for index, line in enumerate(lines):
        text = f"> {line}" if index == selected_index else line
        text_color = selected_color if index == selected_index else color
        draw_centered_text(screen, text, font, text_color, (center_x, top_y + index * 38))


def _playfield_renderer(config: GameConfig) -> PlayfieldRenderer:
    theme = resolve_theme(config.graphics.theme_id)
    key = (
        config.window_width,
        config.window_height,
        config.cell_size,
        theme.theme_id.value,
        config.graphics.show_grid,
    )
    renderer = _PLAYFIELD_RENDERERS.get(key)
    if renderer is None:
        renderer = PlayfieldRenderer(config=config, theme=theme, assets=_SHARED_ASSETS)
        _PLAYFIELD_RENDERERS[key] = renderer
    return renderer


def draw_playfield(
    screen: pygame.Surface,
    state: GameState,
    config: GameConfig,
    hud_font: pygame.font.Font,
    small_font: pygame.font.Font,
    countdown_remaining: float,
    best_score: int,
    stage: int,
    powerup_position: Point | None,
    active_effect_labels: list[str],
) -> None:
    renderer = _playfield_renderer(config)
    renderer.render(
        screen=screen,
        state=state,
        hud_font=hud_font,
        small_font=small_font,
        countdown_remaining=countdown_remaining,
        best_score=best_score,
        stage=stage,
        powerup_position=powerup_position,
        active_effect_labels=active_effect_labels,
    )

