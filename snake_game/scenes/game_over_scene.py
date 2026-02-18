import pygame

from snake_game.render import draw_centered_text, draw_menu_list
from snake_game.scenes.base import AppContext, Scene
from snake_game.types import SceneId


class GameOverScene(Scene):
    scene_id = SceneId.GAME_OVER

    def __init__(self, ctx: AppContext) -> None:
        super().__init__(ctx)
        self.selected_index = 0
        self.options = ["Play Again", "Main Menu", "Quit"]

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
            selected = self.options[self.selected_index]
            if selected == "Play Again":
                self.next_scene = SceneId.PLAY
            elif selected == "Main Menu":
                self.next_scene = SceneId.MENU
            else:
                self.quit_requested = True
            return

        if event.key == pygame.K_ESCAPE:
            self.next_scene = SceneId.MENU

    def update(self, delta_seconds: float) -> None:
        _ = delta_seconds

    def render(self, screen: pygame.Surface) -> None:
        screen.fill(self.ctx.config.background_color)
        draw_centered_text(
            screen,
            "Game Over",
            self.ctx.title_font,
            self.ctx.config.food_color,
            (self.ctx.config.window_width // 2, 110),
        )

        score_value = self.ctx.last_result.score if self.ctx.last_result else 0
        leaderboard = self.ctx.last_result.leaderboard if self.ctx.last_result else []

        draw_centered_text(
            screen,
            f"Score: {score_value}",
            self.ctx.body_font,
            self.ctx.config.text_color,
            (self.ctx.config.window_width // 2, 165),
        )
        draw_menu_list(
            screen=screen,
            lines=self.options,
            selected_index=self.selected_index,
            top_y=230,
            font=self.ctx.body_font,
            color=self.ctx.config.text_color,
            selected_color=self.ctx.config.selected_text_color,
            center_x=self.ctx.config.window_width // 2,
        )

        draw_centered_text(
            screen,
            "Top Scores (Current Setup)",
            self.ctx.small_font,
            self.ctx.config.accent_color,
            (self.ctx.config.window_width // 2, 365),
        )
        for index, value in enumerate(leaderboard[:5], start=1):
            draw_centered_text(
                screen,
                f"{index}. {value}",
                self.ctx.small_font,
                self.ctx.config.text_color,
                (self.ctx.config.window_width // 2, 365 + index * 24),
            )

