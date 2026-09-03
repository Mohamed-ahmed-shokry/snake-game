import pygame

from snake_game.persistence import best_score_for_settings
from snake_game.scenes.base import AppContext, Scene
from snake_game.systems.achievements import ACHIEVEMENTS
from snake_game.types import SceneId
from snake_game.ui.components import (
    draw_hint_footer,
    draw_option_rows,
    draw_scene_background,
    draw_scene_header,
)
from snake_game.ui.layout import option_index_at, scene_vertical_offset
from snake_game.ui.theme import resolve_theme


class MenuScene(Scene):
    scene_id = SceneId.MENU
    option_start_y = 220
    option_gap = 42
    option_width = 520
    option_height = 34

    def __init__(self, ctx: AppContext) -> None:
        super().__init__(ctx)
        self.options = ["Start Game", "Progress", "Settings", "Quit"]
        self.selected_index = 0

    def _layout_offset(self) -> int:
        return scene_vertical_offset(self.ctx.config.window_height)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            hovered = option_index_at(
                event.pos,
                self.ctx.config.window_width,
                self.option_start_y + self._layout_offset(),
                len(self.options),
                self.option_gap,
                self.option_width,
                self.option_height,
            )
            if hovered is not None and hovered != self.selected_index:
                self.selected_index = hovered
                self.ctx.audio.play("move")
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked = option_index_at(
                event.pos,
                self.ctx.config.window_width,
                self.option_start_y + self._layout_offset(),
                len(self.options),
                self.option_gap,
                self.option_width,
                self.option_height,
            )
            if clicked is not None:
                self.selected_index = clicked
                self._activate_selected()
            return

        if event.type != pygame.KEYDOWN:
            return

        key_bindings = self.ctx.persistent_data.settings.key_bindings
        if event.key in (key_bindings.move_up, key_bindings.move_up_alt):
            self.selected_index = (self.selected_index - 1) % len(self.options)
            self.ctx.audio.play("move")
            return

        if event.key in (key_bindings.move_down, key_bindings.move_down_alt):
            self.selected_index = (self.selected_index + 1) % len(self.options)
            self.ctx.audio.play("move")
            return

        if event.key in (key_bindings.confirm, key_bindings.confirm_alt):
            self._activate_selected()
            return

        if event.key == key_bindings.menu_back:
            self.quit_requested = True

    def handle_gamepad_event(self, event: pygame.event.Event) -> None:
        gamepad_settings = self.ctx.persistent_data.settings.gamepad_settings
        if not gamepad_settings.enabled:
            return

        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == gamepad_settings.button_confirm:
                self._activate_selected()
            elif event.button == gamepad_settings.button_menu_back:
                self.quit_requested = True
        elif event.type == pygame.JOYHATMOTION:
            hat_x, hat_y = event.value
            if hat_y == -1:  # Up
                self.selected_index = (self.selected_index - 1) % len(self.options)
                self.ctx.audio.play("move")
            elif hat_y == 1:  # Down
                self.selected_index = (self.selected_index + 1) % len(self.options)
                self.ctx.audio.play("move")

    def _activate_selected(self) -> None:
        self.ctx.audio.play("confirm")
        selected_option = self.options[self.selected_index]
        if selected_option == "Start Game":
            self.next_scene = SceneId.PLAY
        elif selected_option == "Progress":
            self.next_scene = SceneId.PROGRESS
        elif selected_option == "Settings":
            self.next_scene = SceneId.SETTINGS
        else:
            self.quit_requested = True

    def update(self, delta_seconds: float) -> None:
        _ = delta_seconds

    def render(self, screen: pygame.Surface) -> None:
        settings = self.ctx.persistent_data.settings
        key_bindings = settings.key_bindings
        theme = resolve_theme(
            self.ctx.config.graphics.theme_id,
            self.ctx.config.graphics.colorblind_mode,
        )
        palette = theme.palette
        offset_y = self._layout_offset()

        draw_scene_background(
            screen,
            palette.background_top,
            palette.background_bottom,
            palette.grid,
            palette.accent,
        )
        draw_scene_header(
            screen,
            width=self.ctx.config.window_width,
            title="Snake Arcade",
            subtitle="Classic Rules. Modern Runs.",
            title_font=self.ctx.title_font,
            body_font=self.ctx.small_font,
            title_color=palette.accent,
            text_color=palette.text,
            offset_y=offset_y,
        )
        draw_option_rows(
            screen=screen,
            options=self.options,
            selected_index=self.selected_index,
            center_x=self.ctx.config.window_width // 2,
            start_y=self.option_start_y + offset_y,
            row_gap=self.option_gap,
            font=self.ctx.body_font,
            text_color=palette.text,
            selected_text_color=palette.selected_text,
            row_width=self.option_width,
            row_height=self.option_height,
        )

        settings_line = (
            f"{settings.difficulty.label} | {settings.map_mode.label} | "
            f"Obstacles {'On' if settings.obstacles_enabled else 'Off'} | Theme {self.ctx.config.graphics.theme_id.value.capitalize()}"
        )
        draw_hint_footer(
            screen=screen,
            text=settings_line,
            width=self.ctx.config.window_width,
            y=390 + offset_y,
            font=self.ctx.small_font,
            color=palette.text,
        )
        best_score = best_score_for_settings(self.ctx.persistent_data, settings)
        draw_hint_footer(
            screen=screen,
            text=(
                f"Best {best_score}  |  Runs {self.ctx.persistent_data.stats.total_runs}  |  "
                f"Achievements {len(self.ctx.persistent_data.achievements)}/{len(ACHIEVEMENTS)}"
            ),
            width=self.ctx.config.window_width,
            y=420 + offset_y,
            font=self.ctx.small_font,
            color=palette.text,
        )
        confirm_name = pygame.key.name(key_bindings.confirm).upper()
        up_name = pygame.key.name(key_bindings.move_up).upper()
        down_name = pygame.key.name(key_bindings.move_down).upper()
        hint_text = f"{confirm_name} / Click: Select   {up_name}/{down_name} / Mouse: Navigate"
        try:
            if pygame.joystick.get_count() > 0:
                hint_text += "   Pad: D-pad + A Select"
        except pygame.error:
            pass
        draw_hint_footer(
            screen=screen,
            text=hint_text,
            width=self.ctx.config.window_width,
            y=475 + offset_y,
            font=self.ctx.small_font,
            color=palette.text,
        )
