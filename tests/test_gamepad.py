import random
from pathlib import Path

import pygame
import pytest

from snake_game.config import GameConfig, GamepadSettings, UserSettings
from snake_game.events import EventBus
from snake_game.persistence import PersistentData
from snake_game.scenes.base import AppContext, build_ui_fonts
from snake_game.scenes.game_over_scene import GameOverScene
from snake_game.scenes.menu_scene import MenuScene
from snake_game.scenes.play_scene import PlayScene
from snake_game.scenes.progress_scene import ProgressScene
from snake_game.scenes.settings_scene import SettingsScene
from snake_game.types import GameStatus, SceneId


class SilentAudio:
    def play(self, event_name: str) -> None:
        _ = event_name

    def set_muted(self, muted: bool) -> None:
        _ = muted


def _make_context(tmp_path: Path, enable_gamepad: bool = False) -> AppContext:
    pygame.font.init()
    config = GameConfig()
    if enable_gamepad:
        persistent_data = PersistentData(
            settings=UserSettings(
                gamepad_settings=GamepadSettings(
                    enabled=True,
                    dead_zone=0.3,
                    button_move_up=11,
                    button_move_down=12,
                    button_move_left=13,
                    button_move_right=14,
                    button_pause=7,
                    button_mute=6,
                    button_confirm=0,
                    button_menu_back=1,
                    button_help=3,
                )
            )
        )
    else:
        persistent_data = PersistentData(
            settings=UserSettings(gamepad_settings=GamepadSettings(enabled=False))
        )
    config.graphics = persistent_data.graphics
    return AppContext(
        config=config,
        data_path=tmp_path / "save.json",
        persistent_data=persistent_data,
        audio=SilentAudio(),  # type: ignore[arg-type]
        event_bus=EventBus(),
        rng=random.Random(42),
        title_font=build_ui_fonts(config)[0],
        body_font=build_ui_fonts(config)[1],
        small_font=build_ui_fonts(config)[2],
    )


@pytest.fixture
def app_context(tmp_path: Path) -> AppContext:
    return _make_context(tmp_path, enable_gamepad=False)


@pytest.fixture
def app_context_with_gamepad(tmp_path: Path) -> AppContext:
    return _make_context(tmp_path, enable_gamepad=True)


def test_menu_scene_gamepad_navigation(app_context_with_gamepad: AppContext) -> None:
    scene = MenuScene(app_context_with_gamepad)
    assert scene.selected_index == 0

    # Test D-pad down
    event = pygame.event.Event(pygame.JOYHATMOTION, value=(0, 1))
    scene.handle_gamepad_event(event)
    assert scene.selected_index == 1

    # Test D-pad up
    event = pygame.event.Event(pygame.JOYHATMOTION, value=(0, -1))
    scene.handle_gamepad_event(event)
    assert scene.selected_index == 0

    # Test confirm button
    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=0)
    scene.handle_gamepad_event(event)
    assert scene.next_scene == SceneId.PLAY


def test_menu_scene_gamepad_disabled(app_context: AppContext) -> None:
    scene = MenuScene(app_context)
    assert scene.selected_index == 0

    # Gamepad is disabled by default
    event = pygame.event.Event(pygame.JOYHATMOTION, value=(0, 1))
    scene.handle_gamepad_event(event)
    assert scene.selected_index == 0  # Should not change


def test_settings_scene_gamepad_navigation(app_context_with_gamepad: AppContext) -> None:
    scene = SettingsScene(app_context_with_gamepad)
    assert scene.selected_index == 0

    # Test D-pad down
    event = pygame.event.Event(pygame.JOYHATMOTION, value=(0, 1))
    scene.handle_gamepad_event(event)
    assert scene.selected_index == 1

    # Test D-pad up
    event = pygame.event.Event(pygame.JOYHATMOTION, value=(0, -1))
    scene.handle_gamepad_event(event)
    assert scene.selected_index == 0

    # Test D-pad right (change value)
    event = pygame.event.Event(pygame.JOYHATMOTION, value=(1, 0))
    scene.handle_gamepad_event(event)
    # Should have changed the first setting (Theme)

    # Test confirm button
    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=0)
    scene.handle_gamepad_event(event)
    # Should have changed the value

    # Test back button
    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=1)
    scene.handle_gamepad_event(event)
    assert scene.next_scene == SceneId.MENU


def test_settings_scene_gamepad_disabled(app_context: AppContext) -> None:
    scene = SettingsScene(app_context)
    assert scene.selected_index == 0

    event = pygame.event.Event(pygame.JOYHATMOTION, value=(0, 1))
    scene.handle_gamepad_event(event)
    assert scene.selected_index == 0  # Should not change


def test_progress_scene_gamepad_back(app_context_with_gamepad: AppContext) -> None:
    scene = ProgressScene(app_context_with_gamepad)

    # Test confirm button
    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=0)
    scene.handle_gamepad_event(event)
    assert scene.next_scene == SceneId.MENU

    # Test back button
    scene = ProgressScene(app_context_with_gamepad)
    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=1)
    scene.handle_gamepad_event(event)
    assert scene.next_scene == SceneId.MENU


def test_progress_scene_gamepad_disabled(app_context: AppContext) -> None:
    scene = ProgressScene(app_context)

    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=0)
    scene.handle_gamepad_event(event)
    assert scene.next_scene is None  # Should not change


def test_game_over_scene_gamepad_navigation(app_context_with_gamepad: AppContext) -> None:
    scene = GameOverScene(app_context_with_gamepad)
    assert scene.selected_index == 0

    # Test D-pad down
    event = pygame.event.Event(pygame.JOYHATMOTION, value=(0, 1))
    scene.handle_gamepad_event(event)
    assert scene.selected_index == 1

    # Test D-pad up
    event = pygame.event.Event(pygame.JOYHATMOTION, value=(0, -1))
    scene.handle_gamepad_event(event)
    assert scene.selected_index == 0

    # Test confirm button - Play Again
    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=0)
    scene.handle_gamepad_event(event)
    assert scene.next_scene == SceneId.PLAY


def test_game_over_scene_gamepad_disabled(app_context: AppContext) -> None:
    scene = GameOverScene(app_context)

    event = pygame.event.Event(pygame.JOYHATMOTION, value=(0, 1))
    scene.handle_gamepad_event(event)
    assert scene.selected_index == 0  # Should not change

    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=0)
    scene.handle_gamepad_event(event)
    assert scene.next_scene is None  # Should not change


def test_play_scene_gamepad_pause(app_context_with_gamepad: AppContext) -> None:
    scene = PlayScene(app_context_with_gamepad)
    assert scene.state.status == GameStatus.RUNNING

    # Test pause button
    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=7)
    scene.handle_gamepad_event(event)
    assert scene.state.status == GameStatus.PAUSED

    # Test resume
    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=7)
    scene.handle_gamepad_event(event)
    assert scene.state.status == GameStatus.RUNNING


def test_play_scene_gamepad_menu_back(app_context_with_gamepad: AppContext) -> None:
    scene = PlayScene(app_context_with_gamepad)

    # Test menu back button
    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=1)
    scene.handle_gamepad_event(event)
    assert scene.next_scene == SceneId.MENU


def test_play_scene_gamepad_help(app_context_with_gamepad: AppContext) -> None:
    # onboarding_visible defaults to True when onboarding_seen is False
    scene = PlayScene(app_context_with_gamepad)
    assert scene.onboarding_visible is True

    # Test help button toggles onboarding
    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=3)
    scene.handle_gamepad_event(event)
    assert scene.onboarding_visible is True  # Already visible, stays visible

    # Dismiss onboarding
    scene.onboarding_visible = True
    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=0)  # confirm button
    scene.handle_gamepad_event(event)
    assert scene.onboarding_visible is False


def test_play_scene_gamepad_disabled(app_context: AppContext) -> None:
    scene = PlayScene(app_context)
    assert scene.state.status == GameStatus.RUNNING

    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=7)
    scene.handle_gamepad_event(event)
    assert scene.state.status == GameStatus.RUNNING  # Should not pause

    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=1)
    scene.handle_gamepad_event(event)
    assert scene.next_scene is None  # Should not go to menu


def test_play_scene_gamepad_onboarding_dismiss(app_context_with_gamepad: AppContext) -> None:
    scene = PlayScene(app_context_with_gamepad)
    scene.onboarding_visible = True

    # Test confirm button dismisses onboarding
    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=0)
    scene.handle_gamepad_event(event)
    assert scene.onboarding_visible is False
