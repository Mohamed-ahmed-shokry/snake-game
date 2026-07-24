from __future__ import annotations

import random
from pathlib import Path

import pygame
import pytest

from snake_game.app import _create_display, _load_window_icon, _toggle_mute
from snake_game.config import GameConfig
from snake_game.events import EventBus
from snake_game.persistence import PersistentData
from snake_game.rendering.assets import RenderAssets
from snake_game.rendering.layers import PlayfieldRenderer
from snake_game.scenes.base import AppContext, SessionResult, build_ui_fonts
from snake_game.scenes.game_over_scene import GameOverScene
from snake_game.scenes.menu_scene import MenuScene
from snake_game.scenes.play_scene import PlayScene, direction_for_pointer
from snake_game.scenes.progress_scene import ProgressScene
from snake_game.scenes.settings_scene import SettingsScene
from snake_game.systems.powerups import PowerUpType
from snake_game.types import Direction, GameStatus, SceneId
from snake_game.ui.theme import resolve_theme


class SilentAudio:
    def play(self, event_name: str) -> None:
        _ = event_name

    def set_muted(self, muted: bool) -> None:
        _ = muted


@pytest.fixture
def app_context(tmp_path: Path) -> AppContext:
    pygame.font.init()
    config = GameConfig()
    persistent_data = PersistentData()
    config.graphics = persistent_data.graphics
    return AppContext(
        config=config,
        data_path=tmp_path / "save.json",
        persistent_data=persistent_data,
        audio=SilentAudio(),  # type: ignore[arg-type]
        event_bus=EventBus(),
        rng=random.Random(7),
        title_font=pygame.font.Font(None, 76),
        body_font=pygame.font.Font(None, 42),
        small_font=pygame.font.Font(None, 28),
    )


def test_every_scene_renders_at_default_viewport(app_context: AppContext) -> None:
    app_context.last_result = SessionResult(
        score=30,
        leaderboard_key="normal|bounded|clear",
        leaderboard=[30, 20, 10],
        is_new_high_score=True,
        stage_reached=3,
        food_eaten=10,
        run_seconds=65.0,
        new_achievements=["first_run", "score_25"],
    )
    screen = pygame.Surface((app_context.config.window_width, app_context.config.window_height))
    scenes = [
        MenuScene(app_context),
        ProgressScene(app_context),
        SettingsScene(app_context),
        PlayScene(app_context),
        GameOverScene(app_context),
    ]

    for scene in scenes:
        screen.fill((0, 0, 0))
        scene.render(screen)
        assert screen.get_at((0, 0))[:3] != (0, 0, 0)


def test_packaged_window_icon_loads_at_requested_size() -> None:
    icon = _load_window_icon(size=48)

    assert icon is not None
    assert icon.get_size() == (48, 48)


def test_display_helper_sets_expected_window_size(app_context: AppContext) -> None:
    screen = _create_display(app_context.config)

    assert screen.get_size() == (800, 600)
    assert pygame.display.get_caption()[0] == "Snake Arcade"


def test_global_mute_shortcut_persists_setting(app_context: AppContext) -> None:
    _toggle_mute(app_context)

    assert app_context.persistent_data.settings.muted is True
    assert app_context.data_path.exists()


def test_powerup_types_have_distinct_visual_glyphs(app_context: AppContext) -> None:
    play_scene = PlayScene(app_context)
    renderer = PlayfieldRenderer(
        config=app_context.config,
        theme=resolve_theme(app_context.config.graphics.theme_id),
        assets=RenderAssets(),
    )
    images: list[bytes] = []

    for powerup_type in PowerUpType:
        screen = pygame.Surface((app_context.config.window_width, app_context.config.window_height))
        renderer.render(
            screen=screen,
            state=play_scene.state,
            hud_font=app_context.title_font,
            small_font=app_context.small_font,
            countdown_remaining=0.0,
            best_score=0,
            stage=1,
            powerup_position=(1, 1),
            powerup_type=powerup_type,
            active_effect_labels=[],
        )
        images.append(pygame.image.tobytes(screen.subsurface(pygame.Rect(20, 20, 20, 20)), "RGB"))

    assert len(set(images)) == len(PowerUpType)


def test_hud_renders_multiple_active_effects_without_error(app_context: AppContext) -> None:
    play_scene = PlayScene(app_context)
    renderer = PlayfieldRenderer(
        config=app_context.config,
        theme=resolve_theme(app_context.config.graphics.theme_id),
        assets=RenderAssets(),
    )
    screen = pygame.Surface((app_context.config.window_width, app_context.config.window_height))

    renderer.render(
        screen=screen,
        state=play_scene.state,
        hud_font=app_context.title_font,
        small_font=app_context.small_font,
        countdown_remaining=0.0,
        best_score=24,
        stage=3,
        powerup_position=None,
        powerup_type=None,
        active_effect_labels=["Shield 8.0s", "Double 5.2s", "Phase 3.1s"],
        camera_offset=(3, -2),
    )

    assert screen.get_at((0, app_context.config.window_height - 1))[:3] != (0, 0, 0)


def test_menu_supports_mouse_hover_and_click(app_context: AppContext) -> None:
    scene = MenuScene(app_context)
    scene.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(400, 262)))
    assert scene.selected_index == 1

    scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(400, 262), button=1))
    assert scene.next_scene == SceneId.PROGRESS


def test_settings_supports_forward_and_reverse_mouse_changes(app_context: AppContext) -> None:
    scene = SettingsScene(app_context)
    original_theme = app_context.persistent_data.graphics.theme_id

    scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(400, 178), button=1))
    assert app_context.persistent_data.graphics.theme_id != original_theme

    scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(400, 178), button=3))
    assert app_context.persistent_data.graphics.theme_id == original_theme


def test_text_size_setting_refreshes_fonts_and_wraps_options(app_context: AppContext) -> None:
    scene = SettingsScene(app_context)
    original_height = app_context.small_font.get_height()
    scene.selected_index = 2

    scene._change_value(1)

    assert app_context.persistent_data.graphics.ui_scale == 1.1
    assert app_context.small_font.get_height() > original_height
    scene._change_value(1)
    assert app_context.persistent_data.graphics.ui_scale == 0.85


def test_build_ui_fonts_clamps_untrusted_saved_scale() -> None:
    config = GameConfig()
    config.graphics.ui_scale = 99.0

    _, _, small_font = build_ui_fonts(config)

    assert small_font.get_height() == pygame.font.Font(None, round(28 * 1.1)).get_height()


def test_pointer_direction_uses_dominant_axis_and_dead_zone() -> None:
    assert direction_for_pointer((150, 100), (100, 100)) == Direction.RIGHT
    assert direction_for_pointer((70, 100), (100, 100)) == Direction.LEFT
    assert direction_for_pointer((100, 140), (100, 100)) == Direction.DOWN
    assert direction_for_pointer((100, 60), (100, 100)) == Direction.UP
    assert direction_for_pointer((102, 103), (100, 100)) is None


def test_focus_loss_auto_pauses_active_game(app_context: AppContext) -> None:
    scene = PlayScene(app_context)
    scene.onboarding_visible = False

    scene.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))

    assert scene.state.status == GameStatus.PAUSED
    assert scene.toast_text == "AUTO-PAUSED"
