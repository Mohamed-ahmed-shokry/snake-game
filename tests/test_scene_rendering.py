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
from snake_game.rendering.layers import (
    PlayfieldRenderer,
    calculate_danger_level,
    interpolate_snake_positions,
)
from snake_game.scenes.base import AppContext, SessionResult, build_ui_fonts
from snake_game.scenes.game_over_scene import GameOverScene
from snake_game.scenes.menu_scene import MenuScene
from snake_game.scenes.play_scene import PlayScene, direction_for_pointer
from snake_game.scenes.progress_scene import ProgressScene
from snake_game.scenes.settings_scene import SettingsScene
from snake_game.systems.powerups import PowerUpType
from snake_game.types import Direction, GameStatus, MapMode, SceneId
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


def test_food_beacon_animates_and_respects_reduced_motion(app_context: AppContext) -> None:
    renderer = PlayfieldRenderer(
        config=app_context.config,
        theme=resolve_theme(app_context.config.graphics.theme_id),
        assets=RenderAssets(),
    )
    first = pygame.Surface((800, 600), pygame.SRCALPHA)
    second = pygame.Surface((800, 600), pygame.SRCALPHA)
    renderer._draw_food(first, 0.0, (10, 10))
    renderer._draw_food(second, 0.45, (10, 10))
    assert pygame.image.tobytes(first, "RGBA") != pygame.image.tobytes(second, "RGBA")

    app_context.config.graphics.reduced_motion = True
    still_first = pygame.Surface((800, 600), pygame.SRCALPHA)
    still_second = pygame.Surface((800, 600), pygame.SRCALPHA)
    renderer._draw_food(still_first, 0.0, (10, 10))
    renderer._draw_food(still_second, 0.45, (10, 10))
    assert pygame.image.tobytes(still_first, "RGBA") == pygame.image.tobytes(still_second, "RGBA")


def test_obstacle_facets_render_differently_by_cell(app_context: AppContext) -> None:
    renderer = PlayfieldRenderer(
        config=app_context.config,
        theme=resolve_theme(app_context.config.graphics.theme_id),
        assets=RenderAssets(),
    )
    first = pygame.Surface((40, 40), pygame.SRCALPHA)
    second = pygame.Surface((40, 40), pygame.SRCALPHA)

    renderer._draw_obstacle(first, (0, 0))
    renderer._draw_obstacle(second, (1, 0))

    first_cell = pygame.image.tobytes(first.subsurface(pygame.Rect(0, 0, 20, 20)), "RGBA")
    second_cell = pygame.image.tobytes(second.subsurface(pygame.Rect(20, 0, 20, 20)), "RGBA")
    assert first_cell != second_cell


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


def test_hud_telemetry_changes_with_speed_and_danger(app_context: AppContext) -> None:
    scene = PlayScene(app_context)
    renderer = PlayfieldRenderer(
        config=app_context.config,
        theme=resolve_theme(app_context.config.graphics.theme_id),
        assets=RenderAssets(),
    )
    normal = pygame.Surface((800, 600), pygame.SRCALPHA)
    danger = pygame.Surface((800, 600), pygame.SRCALPHA)

    scene.state.obstacles.clear()
    renderer._draw_hud(normal, scene.state, app_context.small_font, 24, 1, [])

    head_x, head_y = scene.state.snake[0]
    scene.state.obstacles = {(head_x + 1, head_y)}
    scene.state.steps_per_second = 12.5
    renderer._draw_hud(danger, scene.state, app_context.small_font, 24, 1, [])

    assert pygame.image.tobytes(normal, "RGBA") != pygame.image.tobytes(danger, "RGBA")
    assert danger.get_bounding_rect().height >= 70


def test_arena_border_distinguishes_bounded_and_wrap_modes(app_context: AppContext) -> None:
    renderer = PlayfieldRenderer(
        config=app_context.config,
        theme=resolve_theme(app_context.config.graphics.theme_id),
        assets=RenderAssets(),
    )
    play_scene = PlayScene(app_context)

    bounded = pygame.Surface((800, 600))
    renderer.render(
        screen=bounded,
        state=play_scene.state,
        hud_font=app_context.title_font,
        small_font=app_context.small_font,
        countdown_remaining=0.0,
        best_score=0,
        stage=1,
        powerup_position=None,
        powerup_type=None,
        active_effect_labels=[],
        animation_seconds=0.5,
    )
    play_scene.state.map_mode = MapMode.WRAP
    wrapped = pygame.Surface((800, 600))
    renderer.render(
        screen=wrapped,
        state=play_scene.state,
        hud_font=app_context.title_font,
        small_font=app_context.small_font,
        countdown_remaining=0.0,
        best_score=0,
        stage=1,
        powerup_position=None,
        powerup_type=None,
        active_effect_labels=[],
        animation_seconds=0.5,
    )

    assert pygame.image.tobytes(bounded.subsurface(pygame.Rect(0, 0, 20, 600)), "RGB") != pygame.image.tobytes(
        wrapped.subsurface(pygame.Rect(0, 0, 20, 600)),
        "RGB",
    )


def test_danger_level_tracks_obstacles_and_bounded_walls(app_context: AppContext) -> None:
    state = PlayScene(app_context).state
    head_x, head_y = state.snake[0]
    state.snake = [
        (head_x, head_y),
        (head_x - 1, head_y),
        (head_x - 2, head_y),
        (head_x - 3, head_y),
    ]
    assert calculate_danger_level(state, app_context.config) == 0.0

    state.obstacles = {(head_x + 1, head_y)}

    assert calculate_danger_level(state, app_context.config) == 1.0

    state.obstacles.clear()
    state.snake = [(0, head_y)]
    state.map_mode = MapMode.BOUNDED
    assert calculate_danger_level(state, app_context.config) == 1.0

    state.map_mode = MapMode.WRAP
    assert calculate_danger_level(state, app_context.config) == 0.0


def test_arena_energy_animates_unless_reduced_motion(app_context: AppContext) -> None:
    renderer = PlayfieldRenderer(
        config=app_context.config,
        theme=resolve_theme(app_context.config.graphics.theme_id),
        assets=RenderAssets(),
    )
    state = PlayScene(app_context).state
    state.obstacles.clear()
    state.snake = [(10, 10)]

    first = pygame.Surface((800, 600), pygame.SRCALPHA)
    second = pygame.Surface((800, 600), pygame.SRCALPHA)
    renderer._draw_arena_energy(first, state, 3, 0.0, 1.0)
    renderer._draw_arena_energy(second, state, 3, 2.0, 1.0)
    assert pygame.image.tobytes(first, "RGBA") != pygame.image.tobytes(second, "RGBA")

    app_context.config.graphics.reduced_motion = True
    still_first = pygame.Surface((800, 600), pygame.SRCALPHA)
    still_second = pygame.Surface((800, 600), pygame.SRCALPHA)
    renderer._draw_arena_energy(still_first, state, 3, 0.0, 1.0)
    renderer._draw_arena_energy(still_second, state, 3, 2.0, 1.0)
    assert pygame.image.tobytes(still_first, "RGBA") == pygame.image.tobytes(still_second, "RGBA")


def test_floating_score_rises_fades_and_expires(app_context: AppContext) -> None:
    scene = PlayScene(app_context)
    scene._spawn_floating_score(8, 12, 4)
    original_y = scene.floating_scores[0].y

    scene._update_floating_scores(0.2)
    assert scene.floating_scores[0].y < original_y

    screen = pygame.Surface((800, 600))
    before = pygame.image.tobytes(screen, "RGB")
    scene._draw_floating_scores(screen)
    assert pygame.image.tobytes(screen, "RGB") != before

    scene._update_floating_scores(1.0)
    assert scene.floating_scores == []


def test_reduced_motion_keeps_floating_score_stationary(app_context: AppContext) -> None:
    app_context.config.graphics.reduced_motion = True
    scene = PlayScene(app_context)
    scene._spawn_floating_score(8, 12, 2)
    original_y = scene.floating_scores[0].y

    scene._update_floating_scores(0.2)

    assert scene.floating_scores[0].y == original_y


def test_control_dock_renders_grouped_key_hints(app_context: AppContext) -> None:
    scene = PlayScene(app_context)
    screen = pygame.Surface((800, 600), pygame.SRCALPHA)

    dock = scene._draw_control_dock(screen)

    assert dock.bottom == 590
    assert dock.width < 800
    assert screen.get_at(dock.center).a > 0
    assert screen.get_bounding_rect().contains(dock)


def test_movement_trail_particles_fade_without_gravity(app_context: AppContext) -> None:
    scene = PlayScene(app_context)
    scene._spawn_movement_trail(10, 10)

    assert len(scene.particles) == 2
    assert all(particle.gravity == 0 for particle in scene.particles)
    initial_life = scene.particles[0].life
    initial_vy = scene.particles[0].vy

    scene._update_particles(0.05)

    assert scene.particles[0].life < initial_life
    assert scene.particles[0].vy == initial_vy


def test_stage_banner_has_cinematic_layers_and_fades(app_context: AppContext) -> None:
    renderer = PlayfieldRenderer(
        config=app_context.config,
        theme=resolve_theme(app_context.config.graphics.theme_id),
        assets=RenderAssets(),
    )
    opening = pygame.Surface((800, 600), pygame.SRCALPHA)
    fading = pygame.Surface((800, 600), pygame.SRCALPHA)

    renderer._draw_stage_banner(
        opening,
        "Stage 4",
        app_context.title_font,
        app_context.small_font,
        210,
    )
    renderer._draw_stage_banner(
        fading,
        "Stage 4",
        app_context.title_font,
        app_context.small_font,
        80,
    )

    assert opening.get_bounding_rect().width == 800
    assert pygame.image.tobytes(opening, "RGBA") != pygame.image.tobytes(fading, "RGBA")
    assert opening.get_at((400, 300)).a > 0


def test_countdown_completion_triggers_go_cue(app_context: AppContext) -> None:
    scene = PlayScene(app_context)
    scene.onboarding_visible = False
    scene.countdown_remaining = 0.1

    scene.update(0.2)

    assert scene.countdown_remaining == 0
    assert scene.go_cue_timer == 0.55

    screen = pygame.Surface((800, 600), pygame.SRCALPHA)
    scene.render(screen)
    assert screen.get_at((400, 300)).a > 0

    scene.update(0.6)
    assert scene.go_cue_timer == 0


def test_cached_glow_is_brightest_near_center() -> None:
    assets = RenderAssets()
    glow = assets.glow_surface(30, (90, 200, 240), peak_alpha=80)

    assert glow.get_at((31, 31)).a > glow.get_at((5, 31)).a
    assert assets.glow_surface(30, (90, 200, 240), peak_alpha=80) is glow


def test_active_powerup_changes_head_visual_effect(app_context: AppContext) -> None:
    play_scene = PlayScene(app_context)
    renderer = PlayfieldRenderer(
        config=app_context.config,
        theme=resolve_theme(app_context.config.graphics.theme_id),
        assets=RenderAssets(),
    )

    def render_head(active_types: set[PowerUpType]) -> bytes:
        screen = pygame.Surface((app_context.config.window_width, app_context.config.window_height))
        renderer.render(
            screen=screen,
            state=play_scene.state,
            hud_font=app_context.title_font,
            small_font=app_context.small_font,
            countdown_remaining=0.0,
            best_score=0,
            stage=1,
            powerup_position=None,
            powerup_type=None,
            active_effect_labels=[],
            active_powerup_types=active_types,
            animation_seconds=0.5,
        )
        head_x, head_y = play_scene.state.snake[0]
        sample = pygame.Rect(
            head_x * app_context.config.cell_size - 8,
            head_y * app_context.config.cell_size - 8,
            app_context.config.cell_size + 16,
            app_context.config.cell_size + 16,
        )
        return pygame.image.tobytes(screen.subsurface(sample), "RGB")

    assert render_head(set()) != render_head({PowerUpType.SHIELD})


def test_queued_turns_render_as_direction_intent(app_context: AppContext) -> None:
    scene = PlayScene(app_context)
    renderer = PlayfieldRenderer(
        config=app_context.config,
        theme=resolve_theme(app_context.config.graphics.theme_id),
        assets=RenderAssets(),
    )
    without_queue = pygame.Surface((800, 600), pygame.SRCALPHA)
    with_queue = pygame.Surface((800, 600), pygame.SRCALPHA)

    renderer._draw_turn_intent(without_queue, scene.state, 0.4)
    scene.state.direction_queue = [Direction.UP, Direction.LEFT]
    renderer._draw_turn_intent(with_queue, scene.state, 0.4)

    assert without_queue.get_bounding_rect().width == 0
    assert with_queue.get_bounding_rect().width > 0


def test_snake_positions_interpolate_between_simulation_steps(app_context: AppContext) -> None:
    scene = PlayScene(app_context)
    scene.state.previous_snake = [(10, 10), (9, 10), (8, 10)]
    scene.state.snake = [(11, 10), (10, 10), (9, 10)]

    assert interpolate_snake_positions(scene.state, 0.5) == [
        (10.5, 10.0),
        (9.5, 10.0),
        (8.5, 10.0),
    ]


def test_snake_interpolation_snaps_across_wrap_boundary(app_context: AppContext) -> None:
    scene = PlayScene(app_context)
    scene.state.previous_snake = [(39, 10), (38, 10), (37, 10)]
    scene.state.snake = [(0, 10), (39, 10), (38, 10)]

    positions = interpolate_snake_positions(scene.state, 0.5)

    assert positions[0] == (0.0, 10.0)


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


def test_pointer_click_shows_feedback_then_expires(app_context: AppContext) -> None:
    scene = PlayScene(app_context)
    scene.onboarding_visible = False
    click_position = (640, 300)

    scene.handle_event(
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            pos=click_position,
            button=1,
        )
    )

    assert scene.pointer_feedback_position == click_position
    assert scene.pointer_feedback_timer == 0.45

    screen = pygame.Surface((800, 600), pygame.SRCALPHA)
    scene._draw_pointer_feedback(screen)
    assert screen.get_at(click_position).a > 0

    scene.update(0.5)
    assert scene.pointer_feedback_position is None


def test_focus_loss_auto_pauses_active_game(app_context: AppContext) -> None:
    scene = PlayScene(app_context)
    scene.onboarding_visible = False

    scene.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))

    assert scene.state.status == GameStatus.PAUSED
    assert scene.toast_text == "AUTO-PAUSED"
