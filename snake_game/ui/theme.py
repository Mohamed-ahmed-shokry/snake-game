from dataclasses import dataclass

from snake_game.types import ThemeId

type Color = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class ThemePalette:
    background_top: Color
    background_bottom: Color
    grid: Color
    snake_head: Color
    snake_body: Color
    obstacle: Color
    food: Color
    powerup: Color
    text: Color
    accent: Color
    selected_text: Color


@dataclass(frozen=True, slots=True)
class UiTheme:
    theme_id: ThemeId
    palette: ThemePalette


THEMES: dict[ThemeId, UiTheme] = {
    ThemeId.NEON: UiTheme(
        theme_id=ThemeId.NEON,
        palette=ThemePalette(
            background_top=(16, 18, 22),
            background_bottom=(25, 29, 38),
            grid=(30, 34, 42),
            snake_head=(106, 219, 130),
            snake_body=(55, 179, 92),
            obstacle=(113, 123, 143),
            food=(233, 88, 81),
            powerup=(247, 198, 85),
            text=(236, 239, 244),
            accent=(93, 198, 240),
            selected_text=(255, 215, 86),
        ),
    ),
    ThemeId.SUNSET: UiTheme(
        theme_id=ThemeId.SUNSET,
        palette=ThemePalette(
            background_top=(30, 20, 24),
            background_bottom=(51, 29, 40),
            grid=(72, 43, 56),
            snake_head=(255, 178, 86),
            snake_body=(245, 135, 86),
            obstacle=(125, 90, 112),
            food=(239, 71, 111),
            powerup=(255, 209, 102),
            text=(247, 244, 240),
            accent=(255, 159, 28),
            selected_text=(255, 230, 109),
        ),
    ),
    ThemeId.OCEAN: UiTheme(
        theme_id=ThemeId.OCEAN,
        palette=ThemePalette(
            background_top=(12, 27, 36),
            background_bottom=(16, 43, 56),
            grid=(29, 67, 84),
            snake_head=(124, 221, 196),
            snake_body=(56, 167, 169),
            obstacle=(94, 125, 143),
            food=(255, 107, 107),
            powerup=(255, 221, 89),
            text=(231, 245, 255),
            accent=(111, 255, 233),
            selected_text=(255, 236, 179),
        ),
    ),
}


def _with_palette(theme: UiTheme, palette: ThemePalette) -> UiTheme:
    return UiTheme(theme_id=theme.theme_id, palette=palette)


def _apply_colorblind_mode(theme: UiTheme, colorblind_mode: str) -> UiTheme:
    mode = colorblind_mode.strip().lower()
    palette = theme.palette
    if mode in {"", "off", "none"}:
        return theme

    if mode == "deuteranopia":
        return _with_palette(
            theme,
            ThemePalette(
                background_top=palette.background_top,
                background_bottom=palette.background_bottom,
                grid=palette.grid,
                snake_head=(114, 184, 255),
                snake_body=(86, 154, 232),
                obstacle=palette.obstacle,
                food=(255, 173, 82),
                powerup=palette.powerup,
                text=palette.text,
                accent=palette.accent,
                selected_text=palette.selected_text,
            ),
        )

    if mode == "tritanopia":
        return _with_palette(
            theme,
            ThemePalette(
                background_top=palette.background_top,
                background_bottom=palette.background_bottom,
                grid=(72, 72, 72),
                snake_head=(112, 220, 142),
                snake_body=(72, 182, 112),
                obstacle=(136, 136, 136),
                food=(255, 112, 112),
                powerup=(255, 208, 92),
                text=palette.text,
                accent=(255, 184, 76),
                selected_text=palette.selected_text,
            ),
        )

    if mode == "high_contrast":
        return _with_palette(
            theme,
            ThemePalette(
                background_top=(10, 10, 10),
                background_bottom=(18, 18, 18),
                grid=(60, 60, 60),
                snake_head=(0, 255, 128),
                snake_body=(0, 210, 110),
                obstacle=(170, 170, 170),
                food=(255, 80, 80),
                powerup=(255, 220, 50),
                text=(255, 255, 255),
                accent=(80, 220, 255),
                selected_text=(255, 245, 120),
            ),
        )

    return theme


def resolve_theme(theme_id: ThemeId | str, colorblind_mode: str = "off") -> UiTheme:
    if isinstance(theme_id, ThemeId):
        base = THEMES[theme_id]
        return _apply_colorblind_mode(base, colorblind_mode)
    try:
        parsed = ThemeId(str(theme_id))
    except ValueError:
        parsed = ThemeId.NEON
    base = THEMES[parsed]
    return _apply_colorblind_mode(base, colorblind_mode)
