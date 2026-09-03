import random
from importlib.resources import as_file, files
from pathlib import Path

import pygame

from snake_game.audio import AudioManager
from snake_game.config import GameConfig
from snake_game.events import EventBus
from snake_game.persistence import load_persistent_data
from snake_game.rendering.effects import draw_fade_overlay
from snake_game.scenes.base import AppContext, Scene, build_ui_fonts
from snake_game.scenes.game_over_scene import GameOverScene
from snake_game.scenes.menu_scene import MenuScene
from snake_game.scenes.play_scene import PlayScene
from snake_game.scenes.progress_scene import ProgressScene
from snake_game.scenes.settings_scene import SettingsScene
from snake_game.types import SceneId
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


def _toggle_mute(ctx: AppContext) -> None:
    settings = ctx.persistent_data.settings
    settings.muted = not settings.muted
    ctx.audio.set_muted(settings.muted)
    ctx.persist()
    if not settings.muted:
        ctx.audio.play("confirm")


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

        while running:
            delta_seconds = clock.tick(config.render_fps) / 1000.0

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
