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


def test_game_config_rejects_invalid_ui_scale() -> None:
    config = GameConfig(graphics=GraphicsSettings(ui_scale=0.0))
    with pytest.raises(ValueError):
        config.validate()

