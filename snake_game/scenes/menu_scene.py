import pygame

from snake_game.persistence import best_score_for_settings
from snake_game.scenes.base import AppContext, Scene
from snake_game.types import SceneId
from snake_game.ui.components import draw_hint_footer, draw_option_rows, draw_scene_header
from snake_game.ui.theme import resolve_theme


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
        theme = resolve_theme(
            self.ctx.config.graphics.theme_id,
            self.ctx.config.graphics.colorblind_mode,
        )
        palette = theme.palette

        screen.fill(palette.background_top)
        draw_scene_header(
            screen,
            width=self.ctx.config.window_width,
            title="Snake V4",
            subtitle="Arcade Run",
            title_font=self.ctx.title_font,
            body_font=self.ctx.small_font,
            title_color=palette.accent,
            text_color=palette.text,
        )
        draw_option_rows(
            screen=screen,
            options=self.options,
            selected_index=self.selected_index,
            center_x=self.ctx.config.window_width // 2,
            start_y=220,
            row_gap=42,
            font=self.ctx.body_font,
            text_color=palette.text,
            selected_text_color=palette.selected_text,
        )

        settings_line = (
            f"{settings.difficulty.label} | {settings.map_mode.label} | "
            f"Obstacles {'On' if settings.obstacles_enabled else 'Off'} | Theme {self.ctx.config.graphics.theme_id.value.capitalize()}"
        )
        draw_hint_footer(
            screen=screen,
            text=settings_line,
            width=self.ctx.config.window_width,
            y=390,
            font=self.ctx.small_font,
            color=palette.text,
        )
        best_score = best_score_for_settings(self.ctx.persistent_data, settings)
        draw_hint_footer(
            screen=screen,
            text=f"Best Score (Current Setup): {best_score}",
            width=self.ctx.config.window_width,
            y=420,
            font=self.ctx.small_font,
            color=palette.text,
        )
        draw_hint_footer(
            screen=screen,
            text="Enter: Select   Up/Down: Navigate",
            width=self.ctx.config.window_width,
            y=470,
            font=self.ctx.small_font,
            color=palette.text,
        )
