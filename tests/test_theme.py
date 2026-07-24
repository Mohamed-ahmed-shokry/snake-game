import pytest

from snake_game.config import (
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    GameConfig,
    GraphicsSettings,
)
from snake_game.types import ThemeId
from snake_game.ui.theme import resolve_theme


def test_resolve_theme_by_enum() -> None:
    theme = resolve_theme(ThemeId.SUNSET)
    assert theme.theme_id == ThemeId.SUNSET


def test_resolve_theme_falls_back_for_unknown_value() -> None:
    theme = resolve_theme("not-a-theme")
    assert theme.theme_id == ThemeId.NEON


def test_resolve_theme_applies_colorblind_mode_variant() -> None:
    normal = resolve_theme(ThemeId.NEON, colorblind_mode="off")
    adjusted = resolve_theme(ThemeId.NEON, colorblind_mode="deuteranopia")
    assert adjusted.palette.snake_head != normal.palette.snake_head


@pytest.mark.parametrize("ui_scale", [0.0, float("nan"), float("inf")])
def test_game_config_rejects_invalid_ui_scale(ui_scale: float) -> None:
    with pytest.raises(ValueError, match="ui_scale"):
        GameConfig(graphics=GraphicsSettings(ui_scale=ui_scale)).validate()


@pytest.mark.parametrize("countdown_seconds", [-1.0, float("nan"), float("inf")])
def test_game_config_rejects_invalid_countdown(countdown_seconds: float) -> None:
    with pytest.raises(ValueError, match="countdown_seconds"):
        GameConfig(countdown_seconds=countdown_seconds).validate()


def test_game_config_rejects_non_positive_dimensions() -> None:
    for config in [
        GameConfig(window_width=0),
        GameConfig(window_height=0),
        GameConfig(cell_size=0),
    ]:
        with pytest.raises(ValueError):
            config.validate()


def test_game_config_rejects_viewports_too_small_for_the_ui() -> None:
    with pytest.raises(ValueError, match="window_width"):
        GameConfig(window_width=MIN_WINDOW_WIDTH - 20).validate()
    with pytest.raises(ValueError, match="window_height"):
        GameConfig(window_height=MIN_WINDOW_HEIGHT - 20).validate()


def test_game_config_rejects_invalid_render_fps() -> None:
    config = GameConfig(render_fps=0)
    with pytest.raises(ValueError):
        config.validate()


def test_game_config_rejects_invalid_colorblind_mode() -> None:
    config = GameConfig(graphics=GraphicsSettings(colorblind_mode="invalid"))
    with pytest.raises(ValueError):
        config.validate()
