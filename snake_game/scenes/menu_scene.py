import pygame

from snake_game.persistence import leaderboard_key
from snake_game.render import draw_centered_text, draw_menu_list
from snake_game.scenes.base import AppContext, Scene
from snake_game.types import SceneId


class MenuScene(Scene):
    scene_id = SceneId.MENU

    def __init__(self, ctx: AppContext) -> None:
        super().__init__(ctx)
        self.options = ["Start Game", "Settings", "Quit"]
        self.selected_index = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (self.selected_index - 1) % len(self.options)
            self.ctx.audio.play("move")
            return

        if event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(self.options)
            self.ctx.audio.play("move")
            return

        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.ctx.audio.play("confirm")
            selected_option = self.options[self.selected_index]
            if selected_option == "Start Game":
                self.next_scene = SceneId.PLAY
            elif selected_option == "Settings":
                self.next_scene = SceneId.SETTINGS
            else:
                self.quit_requested = True
            return

        if event.key == pygame.K_ESCAPE:
            self.quit_requested = True

    def update(self, delta_seconds: float) -> None:
        _ = delta_seconds

    def render(self, screen: pygame.Surface) -> None:
        settings = self.ctx.persistent_data.settings
        active_key = leaderboard_key(settings)
        leaderboard = self.ctx.persistent_data.leaderboard.get(active_key, [])

        screen.fill(self.ctx.config.background_color)
        draw_centered_text(
            screen,
            "Snake V2",
            self.ctx.title_font,
            self.ctx.config.accent_color,
            (self.ctx.config.window_width // 2, 110),
        )
        draw_menu_list(
            screen=screen,
            lines=self.options,
            selected_index=self.selected_index,
            top_y=210,
            font=self.ctx.body_font,
            color=self.ctx.config.text_color,
            selected_color=self.ctx.config.selected_text_color,
            center_x=self.ctx.config.window_width // 2,
        )

        settings_line = (
            f"{settings.difficulty.label} | {settings.map_mode.label} | "
            f"Obstacles {'On' if settings.obstacles_enabled else 'Off'}"
        )
        draw_centered_text(
            screen,
            settings_line,
            self.ctx.small_font,
            self.ctx.config.text_color,
            (self.ctx.config.window_width // 2, 390),
        )
        best_score = leaderboard[0] if leaderboard else 0
        draw_centered_text(
            screen,
            f"Best Score (Current Setup): {best_score}",
            self.ctx.small_font,
            self.ctx.config.text_color,
            (self.ctx.config.window_width // 2, 420),
        )
        draw_centered_text(
            screen,
            "Enter: Select   Up/Down: Navigate",
            self.ctx.small_font,
            self.ctx.config.text_color,
            (self.ctx.config.window_width // 2, 470),
        )

