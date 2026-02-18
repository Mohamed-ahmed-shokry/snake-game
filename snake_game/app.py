import random
from pathlib import Path

import pygame

from snake_game.audio import AudioManager
from snake_game.config import GameConfig
from snake_game.persistence import load_persistent_data, save_persistent_data
from snake_game.scenes.base import AppContext, Scene
from snake_game.scenes.game_over_scene import GameOverScene
from snake_game.scenes.menu_scene import MenuScene
from snake_game.scenes.play_scene import PlayScene
from snake_game.scenes.settings_scene import SettingsScene
from snake_game.types import SceneId


def _build_scene(scene_id: SceneId, ctx: AppContext) -> Scene:
    if scene_id == SceneId.MENU:
        return MenuScene(ctx)
    if scene_id == SceneId.SETTINGS:
        return SettingsScene(ctx)
    if scene_id == SceneId.PLAY:
        return PlayScene(ctx)
    if scene_id == SceneId.GAME_OVER:
        return GameOverScene(ctx)
    raise ValueError(f"Unsupported scene id: {scene_id}")


def run() -> None:
    pygame.init()

    config = GameConfig()
    config.validate()

    screen = pygame.display.set_mode((config.window_width, config.window_height))
    pygame.display.set_caption("Snake V2")
    clock = pygame.time.Clock()

    title_font = pygame.font.Font(None, 76)
    body_font = pygame.font.Font(None, 42)
    small_font = pygame.font.Font(None, 28)

    data_path = Path(config.data_file)
    persistent_data = load_persistent_data(data_path)
    audio = AudioManager(muted=persistent_data.settings.muted)

    ctx = AppContext(
        config=config,
        data_path=data_path,
        persistent_data=persistent_data,
        audio=audio,
        rng=random.Random(),
        title_font=title_font,
        body_font=body_font,
        small_font=small_font,
    )

    scene: Scene = _build_scene(SceneId.MENU, ctx)
    running = True

    while running:
        delta_seconds = clock.tick(config.render_fps) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            scene.handle_event(event)

        if not running:
            break

        next_scene = scene.consume_next_scene()
        if next_scene is not None:
            scene = _build_scene(next_scene, ctx)

        if scene.quit_requested:
            break

        scene.update(delta_seconds)
        if scene.quit_requested:
            break

        post_update_scene = scene.consume_next_scene()
        if post_update_scene is not None:
            scene = _build_scene(post_update_scene, ctx)

        scene.render(screen)
        pygame.display.flip()

    save_persistent_data(ctx.persistent_data, data_path)
    pygame.quit()
