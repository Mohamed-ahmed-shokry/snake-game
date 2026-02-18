import pytest

from snake_game.config import GameConfig, GraphicsSettings
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


def test_game_config_rejects_invalid_ui_scale() -> None:
    config = GameConfig(graphics=GraphicsSettings(ui_scale=0.0))
    with pytest.raises(ValueError):
        config.validate()
