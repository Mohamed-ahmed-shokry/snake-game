import pygame

from snake_game.config import COLORBLIND_MODES, normalize_colorblind_mode
from snake_game.scenes.base import UI_SCALE_OPTIONS, AppContext, Scene
from snake_game.types import Difficulty, MapMode, SceneId, ThemeId
from snake_game.ui.components import (
    draw_hint_footer,
    draw_option_rows,
    draw_scene_background,
    draw_scene_header,
)
from snake_game.ui.layout import option_index_at, scene_vertical_offset
from snake_game.ui.theme import resolve_theme


def _cycle_theme(current: ThemeId, step: int) -> ThemeId:
    values = list(ThemeId)
    index = values.index(current)
    return values[(index + step) % len(values)]


def _cycle_color_mode(current: str, step: int) -> str:
    normalized = normalize_colorblind_mode(current)
    index = COLORBLIND_MODES.index(normalized)
    return COLORBLIND_MODES[(index + step) % len(COLORBLIND_MODES)]


def _cycle_ui_scale(current: float, step: int) -> float:
    nearest_index = min(range(len(UI_SCALE_OPTIONS)), key=lambda index: abs(UI_SCALE_OPTIONS[index] - current))
    return UI_SCALE_OPTIONS[(nearest_index + step) % len(UI_SCALE_OPTIONS)]


def _cycle_difficulty(current: Difficulty, step: int) -> Difficulty:
    values = list(Difficulty)
    index = values.index(current)
    return values[(index + step) % len(values)]


def _cycle_map_mode(current: MapMode, step: int) -> MapMode:
    values = list(MapMode)
    index = values.index(current)
    return values[(index + step) % len(values)]


class SettingsScene(Scene):
    scene_id = SceneId.SETTINGS
    option_start_y = 174
    option_gap = 27
    option_width = 560
    option_height = 25

    def __init__(self, ctx: AppContext) -> None:
        super().__init__(ctx)
        self.selected_index = 0

    def _layout_offset(self) -> int:
        return scene_vertical_offset(self.ctx.config.window_height)

    def _rows(self) -> list[str]:
        settings = self.ctx.persistent_data.settings
        graphics = self.ctx.persistent_data.graphics
        return [
            f"Theme: {graphics.theme_id.value.capitalize()}",
            f"Color Mode: {graphics.colorblind_mode.replace('_', ' ').title()}",
            f"Text Size: {round(graphics.ui_scale * 100)}%",
            f"Show Grid: {'On' if graphics.show_grid else 'Off'}",
            f"Particles: {'On' if graphics.particles_enabled else 'Off'}",
            f"Reduced Motion: {'On' if graphics.reduced_motion else 'Off'}",
            f"Screen Shake: {'On' if graphics.screen_shake_enabled else 'Off'}",
            f"Difficulty: {settings.difficulty.label}",
            f"Map Mode: {settings.map_mode.label}",
            f"Obstacles: {'On' if settings.obstacles_enabled else 'Off'}",
            f"Sound: {'Muted' if settings.muted else 'On'}",
            "Back",
        ]

    def _description_for(self, index: int) -> str:
        descriptions = [
            "Visual palette style for the entire game.",
            "Accessibility palette adjustment for color perception.",
            "Adjust text size across every screen.",
            "Show or hide board grid lines.",
            "Enable pickup and food burst particles.",
            "Disables most animation intensity and transitions.",
            "Applies small camera shake on key events.",
            "Changes base speed and score pace.",
            "Bounded walls or wrap-around movement.",
            "Adds hazards at the start and as each stage advances.",
            "Toggle all gameplay/menu sound effects.",
            "Return to main menu.",
        ]
        if 0 <= index < len(descriptions):
            return descriptions[index]
        return ""

    def _persist(self) -> None:
        self.ctx.persist()

    def _change_value(self, step: int) -> None:
        settings = self.ctx.persistent_data.settings
        graphics = self.ctx.persistent_data.graphics

        if self.selected_index == 0:
            graphics.theme_id = _cycle_theme(graphics.theme_id, step)
        elif self.selected_index == 1:
            graphics.colorblind_mode = _cycle_color_mode(graphics.colorblind_mode, step)
        elif self.selected_index == 2:
            graphics.ui_scale = _cycle_ui_scale(graphics.ui_scale, step)
            self.ctx.refresh_fonts()
        elif self.selected_index == 3:
            graphics.show_grid = not graphics.show_grid
        elif self.selected_index == 4:
            graphics.particles_enabled = not graphics.particles_enabled
        elif self.selected_index == 5:
            graphics.reduced_motion = not graphics.reduced_motion
            if graphics.reduced_motion:
                graphics.screen_shake_enabled = False
        elif self.selected_index == 6:
            if not graphics.reduced_motion:
                graphics.screen_shake_enabled = not graphics.screen_shake_enabled
        elif self.selected_index == 7:
            settings.difficulty = _cycle_difficulty(settings.difficulty, step)
        elif self.selected_index == 8:
            settings.map_mode = _cycle_map_mode(settings.map_mode, step)
        elif self.selected_index == 9:
            settings.obstacles_enabled = not settings.obstacles_enabled
        elif self.selected_index == 10:
            settings.muted = not settings.muted
            self.ctx.audio.set_muted(settings.muted)
        else:
            self.next_scene = SceneId.MENU
            self.ctx.audio.play("confirm")
            return

        self.ctx.config.graphics = graphics
        self.ctx.audio.play("move")
        self._persist()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            hovered = option_index_at(
                event.pos,
                self.ctx.config.window_width,
                self.option_start_y + self._layout_offset(),
                len(self._rows()),
                self.option_gap,
                self.option_width,
                self.option_height,
            )
            if hovered is not None and hovered != self.selected_index:
                self.selected_index = hovered
                self.ctx.audio.play("move")
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
            clicked = option_index_at(
                event.pos,
                self.ctx.config.window_width,
                self.option_start_y + self._layout_offset(),
                len(self._rows()),
                self.option_gap,
                self.option_width,
                self.option_height,
            )
            if clicked is not None:
                self.selected_index = clicked
                self._change_value(-1 if event.button == 3 else 1)
            return

        if event.type != pygame.KEYDOWN:
            return

        row_count = len(self._rows())
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (self.selected_index - 1) % row_count
            self.ctx.audio.play("move")
            return

        if event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % row_count
            self.ctx.audio.play("move")
            return

        if event.key in (pygame.K_LEFT, pygame.K_a):
            self._change_value(-1)
            return

        if event.key in (pygame.K_RIGHT, pygame.K_d):
            self._change_value(1)
            return

        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._change_value(1)
            return

        if event.key == pygame.K_ESCAPE:
            self.next_scene = SceneId.MENU

    def update(self, delta_seconds: float) -> None:
        _ = delta_seconds

    def render(self, screen: pygame.Surface) -> None:
        rows = self._rows()
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
            screen=screen,
            width=self.ctx.config.window_width,
            title="Settings",
            subtitle="Graphics, Accessibility, and Gameplay",
            title_font=self.ctx.title_font,
            body_font=self.ctx.small_font,
            title_color=palette.accent,
            text_color=palette.text,
            offset_y=offset_y,
        )
        draw_option_rows(
            screen=screen,
            options=rows,
            selected_index=self.selected_index,
            center_x=self.ctx.config.window_width // 2,
            start_y=self.option_start_y + offset_y,
            row_gap=self.option_gap,
            font=self.ctx.small_font,
            text_color=palette.text,
            selected_text_color=palette.selected_text,
            row_width=self.option_width,
            row_height=self.option_height,
        )
        draw_hint_footer(
            screen=screen,
            text=self._description_for(self.selected_index),
            width=self.ctx.config.window_width,
            y=510 + offset_y,
            font=self.ctx.small_font,
            color=palette.text,
        )
        draw_hint_footer(
            screen=screen,
            text="Left/Right or Click: Change   Right Click: Previous   Esc: Back",
            width=self.ctx.config.window_width,
            y=548 + offset_y,
            font=self.ctx.small_font,
            color=palette.accent,
        )
