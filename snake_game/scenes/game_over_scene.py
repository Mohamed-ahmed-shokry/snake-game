import pygame

from snake_game.scenes.base import AppContext, Scene
from snake_game.types import SceneId
from snake_game.ui.components import draw_hint_footer, draw_option_rows, draw_scene_header
from snake_game.ui.theme import resolve_theme


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
        theme = resolve_theme(
            self.ctx.config.graphics.theme_id,
            self.ctx.config.graphics.colorblind_mode,
        )
        palette = theme.palette

        screen.fill(palette.background_top)
        draw_scene_header(
            screen=screen,
            width=self.ctx.config.window_width,
            title="Game Over",
            subtitle="Run Summary",
            title_font=self.ctx.title_font,
            body_font=self.ctx.small_font,
            title_color=palette.food,
            text_color=palette.text,
        )

        result = self.ctx.last_result
        score_value = result.score if result else 0
        leaderboard = result.leaderboard if result else []
        new_best = result.is_new_high_score if result else False
        stage_reached = result.stage_reached if result else 1
        food_eaten = result.food_eaten if result else 0
        run_seconds = result.run_seconds if result else 0.0

        summary_text = (
            f"Score {score_value}  |  Stage {stage_reached}  |  "
            f"Food {food_eaten}  |  Time {run_seconds:0.1f}s"
        )
        draw_hint_footer(
            screen=screen,
            text=summary_text,
            width=self.ctx.config.window_width,
            y=180,
            font=self.ctx.small_font,
            color=palette.text,
        )
        if new_best:
            draw_hint_footer(
                screen=screen,
                text="New High Score!",
                width=self.ctx.config.window_width,
                y=208,
                font=self.ctx.small_font,
                color=palette.selected_text,
            )

        draw_option_rows(
            screen=screen,
            options=self.options,
            selected_index=self.selected_index,
            center_x=self.ctx.config.window_width // 2,
            start_y=280,
            row_gap=42,
            font=self.ctx.body_font,
            text_color=palette.text,
            selected_text_color=palette.selected_text,
            row_width=460,
            row_height=34,
        )

        draw_hint_footer(
            screen=screen,
            text="Top Scores (Current Setup): " + ", ".join(str(value) for value in leaderboard[:5]),
            width=self.ctx.config.window_width,
            y=430,
            font=self.ctx.small_font,
            color=palette.accent,
        )
        draw_hint_footer(
            screen=screen,
            text="Enter: Select   Esc: Main Menu",
            width=self.ctx.config.window_width,
            y=470,
            font=self.ctx.small_font,
            color=palette.text,
        )

