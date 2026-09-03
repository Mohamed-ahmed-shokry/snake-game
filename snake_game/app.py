import random
from importlib.resources import as_file, files
from pathlib import Path

import pygame

from snake_game.audio import AudioManager
from snake_game.config import GameConfig
from snake_game.events import EventBus
from snake_game.logic import queue_direction_change
from snake_game.persistence import load_persistent_data
from snake_game.rendering.effects import draw_fade_overlay
from snake_game.scenes.base import AppContext, Scene, build_ui_fonts
from snake_game.scenes.game_over_scene import GameOverScene
from snake_game.scenes.menu_scene import MenuScene
from snake_game.scenes.play_scene import PlayScene
from snake_game.scenes.progress_scene import ProgressScene
from snake_game.scenes.settings_scene import SettingsScene
from snake_game.types import Direction, SceneId
from snake_game.ui.components import draw_save_warning


def _load_window_icon(size: int = 64) -> pygame.Surface | None:
    try:
        icon_resource = files("snake_game").joinpath("assets", "snake_arcade_icon.png")
        with as_file(icon_resource) as icon_path:
            icon = pygame.image.load(str(icon_path))
        return pygame.transform.smoothscale(icon, (size, size))
    except (FileNotFoundError, OSError, pygame.error):
        return None


def _create_display(config: GameConfig, fullscreen: bool = False) -> pygame.Surface:
    flags = pygame.FULLSCREEN if fullscreen else 0
    screen = pygame.display.set_mode((config.window_width, config.window_height), flags)
    pygame.display.set_caption("Snake Arcade")
    window_icon = _load_window_icon()
    if window_icon is not None:
        pygame.display.set_icon(window_icon)
    return screen


def _init_gamepad() -> list[pygame.joystick.Joystick]:
    """Initialize joystick subsystem and return list of connected gamepads."""
    gamepads: list[pygame.joystick.Joystick] = []
    try:
        pygame.joystick.init()
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            gamepads.append(joy)
    except pygame.error:
        pass
    return gamepads


def _toggle_mute(ctx: AppContext) -> None:
    settings = ctx.persistent_data.settings
    settings.muted = not settings.muted
    ctx.audio.set_muted(settings.muted)
    ctx.persist()
    if not settings.muted:
        ctx.audio.play("confirm")


def _handle_gamepad_button_down(ctx: AppContext, button: int) -> bool:
    """Handle gamepad button press. Returns True if event was consumed."""
    gamepad_settings = ctx.persistent_data.settings.gamepad_settings
    if not gamepad_settings.enabled:
        return False

    if button == gamepad_settings.button_pause:
        # Pause is handled by the current scene
        return False
    if button == gamepad_settings.button_mute:
        _toggle_mute(ctx)
        return True
    if button == gamepad_settings.button_confirm:
        # Confirm is handled by the current scene
        return False
    if button == gamepad_settings.button_menu_back:
        # Menu back is handled by the current scene
        return False
    if button == gamepad_settings.button_help:
        # Help is handled by the current scene
        return False
    return False


def _get_gamepad_direction(ctx: AppContext) -> tuple[float, float] | None:
    """Get direction from gamepad left stick/D-pad. Returns (x, y) or None."""
    gamepad_settings = ctx.persistent_data.settings.gamepad_settings
    if not gamepad_settings.enabled:
        return None

    try:
        if pygame.joystick.get_count() == 0:
            return None
        joy = pygame.joystick.Joystick(0)
        if not joy.get_init():
            return None

        # Check D-pad first (hat)
        if joy.get_numhats() > 0:
            hat_x, hat_y = joy.get_hat(0)
            if hat_x != 0 or hat_y != 0:
                return (float(hat_x), float(-hat_y))  # D-pad Y is inverted

        # Check left stick
        if joy.get_numaxes() > 1:
            axis_x = joy.get_axis(0)
            axis_y = joy.get_axis(1)
            dead_zone = gamepad_settings.dead_zone
            if abs(axis_x) > dead_zone or abs(axis_y) > dead_zone:
                return (axis_x, axis_y)
    except pygame.error:
        pass
    return None


def _apply_gamepad_direction(
    ctx: AppContext,
    scene: Scene,
    pressed: dict[str, bool],
    axis_x: float,
    axis_y: float,
    dead_zone: float,
) -> None:
    """Queue one direction change from polled stick/D-pad axes (edge-triggered)."""
    if scene.scene_id != SceneId.PLAY or not hasattr(scene, "state"):
        return
    if abs(axis_x) > abs(axis_y):
        if axis_x > dead_zone and not pressed["right"]:
            queue_direction_change(scene.state, Direction.RIGHT)  # type: ignore[attr-defined]
            pressed["right"] = True
            pressed["left"] = False
        elif axis_x < -dead_zone and not pressed["left"]:
            queue_direction_change(scene.state, Direction.LEFT)  # type: ignore[attr-defined]
            pressed["left"] = True
            pressed["right"] = False
        elif abs(axis_x) <= dead_zone:
            pressed["left"] = False
            pressed["right"] = False
    elif abs(axis_y) > abs(axis_x):
        if axis_y < -dead_zone and not pressed["up"]:
            queue_direction_change(scene.state, Direction.UP)  # type: ignore[attr-defined]
            pressed["up"] = True
            pressed["down"] = False
        elif axis_y > dead_zone and not pressed["down"]:
            queue_direction_change(scene.state, Direction.DOWN)  # type: ignore[attr-defined]
            pressed["down"] = True
            pressed["up"] = False
        elif abs(axis_y) <= dead_zone:
            pressed["up"] = False
            pressed["down"] = False


def _reset_gamepad_pressed() -> dict[str, bool]:
    return {"up": False, "down": False, "left": False, "right": False}


def _build_scene(scene_id: SceneId, ctx: AppContext) -> Scene:
    if scene_id == SceneId.MENU:
        return MenuScene(ctx)
    if scene_id == SceneId.PROGRESS:
        return ProgressScene(ctx)
    if scene_id == SceneId.SETTINGS:
        return SettingsScene(ctx)
    if scene_id == SceneId.PLAY:
        return PlayScene(ctx)
    if scene_id == SceneId.GAME_OVER:
        return GameOverScene(ctx)
    raise ValueError(f"Unsupported scene id: {scene_id}")


def run(config: GameConfig | None = None, seed: int | None = None) -> None:
    pygame.init()
    ctx: AppContext | None = None
    try:
        config = config or GameConfig()
        data_path = Path(config.data_file)
        persistent_data = load_persistent_data(data_path)
        config.graphics = persistent_data.graphics
        config.validate()

        # Initialize gamepad
        _init_gamepad()

        screen = _create_display(config)
        clock = pygame.time.Clock()

        title_font, body_font, small_font = build_ui_fonts(config)

        audio = AudioManager(muted=persistent_data.settings.muted)

        ctx = AppContext(
            config=config,
            data_path=data_path,
            persistent_data=persistent_data,
            audio=audio,
            event_bus=EventBus(),
            rng=random.Random(seed),
            title_font=title_font,
            body_font=body_font,
            small_font=small_font,
        )

        scene: Scene = _build_scene(SceneId.MENU, ctx)
        running = True
        fullscreen = False
        transition_alpha = 0 if config.graphics.reduced_motion else 255

        # Gamepad state tracking (edge-triggered stick/D-pad movement)
        gamepad_direction_pressed = _reset_gamepad_pressed()

        while running:
            delta_seconds = clock.tick(config.render_fps) / 1000.0

            # Handle gamepad axis input for continuous movement
            gamepad_dir = _get_gamepad_direction(ctx)
            if gamepad_dir is not None:
                axis_x, axis_y = gamepad_dir
                dead_zone = ctx.persistent_data.settings.gamepad_settings.dead_zone
                _apply_gamepad_direction(
                    ctx, scene, gamepad_direction_pressed, axis_x, axis_y, dead_zone
                )
            else:
                # Reset direction pressed state when no input
                gamepad_direction_pressed = _reset_gamepad_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if event.type == pygame.KEYDOWN:
                    key_bindings = ctx.persistent_data.settings.key_bindings
                    if event.key == key_bindings.fullscreen:
                        fullscreen = not fullscreen
                        screen = _create_display(config, fullscreen=fullscreen)
                        continue
                    if event.key == key_bindings.mute:
                        _toggle_mute(ctx)
                        continue
                if event.type == pygame.JOYBUTTONDOWN:
                    _handle_gamepad_button_down(ctx, event.button)
                    # Also pass to scene for scene-specific handling
                    scene.handle_gamepad_event(event)
                if event.type == pygame.JOYHATMOTION:
                    # D-pad handled via axis polling above, but pass to scene too
                    scene.handle_gamepad_event(event)
                if event.type == pygame.JOYAXISMOTION:
                    # Axis handled via polling above, but pass to scene too
                    scene.handle_gamepad_event(event)
                if event.type == pygame.JOYDEVICEADDED:
                    # Re-initialize gamepads
                    _init_gamepad()
                if event.type == pygame.JOYDEVICEREMOVED:
                    pass  # Gamepad removed, will be handled on next init
                scene.handle_event(event)

            if not running:
                break

            next_scene = scene.consume_next_scene()
            if next_scene is not None:
                scene = _build_scene(next_scene, ctx)
                if not config.graphics.reduced_motion:
                    transition_alpha = 180

            if scene.quit_requested:
                break

            scene.update(delta_seconds)
            if scene.quit_requested:
                break

            post_update_scene = scene.consume_next_scene()
            if post_update_scene is not None:
                scene = _build_scene(post_update_scene, ctx)
                if not config.graphics.reduced_motion:
                    transition_alpha = 180

            scene.render(screen)
            if transition_alpha > 0:
                draw_fade_overlay(screen, transition_alpha)
                transition_alpha = max(0, transition_alpha - int(420 * delta_seconds))
            if ctx.save_error_message is not None:
                draw_save_warning(screen, ctx.save_error_message, ctx.small_font)
            pygame.display.flip()
    finally:
        try:
            if ctx is not None:
                ctx.persist()
        finally:
            pygame.quit()
