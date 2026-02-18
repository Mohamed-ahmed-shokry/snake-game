import pygame

from snake_game.persistence import save_persistent_data
from snake_game.scenes.base import AppContext, Scene
from snake_game.types import Difficulty, MapMode, SceneId, ThemeId
from snake_game.ui.components import draw_hint_footer, draw_option_rows, draw_scene_header
from snake_game.ui.theme import resolve_theme

COLORBLIND_MODES = ["off", "deuteranopia", "tritanopia", "high_contrast"]


def _cycle_theme(current: ThemeId, step: int) -> ThemeId:
    values = list(ThemeId)
    index = values.index(current)
    return values[(index + step) % len(values)]


def _cycle_color_mode(current: str, step: int) -> str:
    normalized = current.strip().lower()
    if normalized not in COLORBLIND_MODES:
        normalized = "off"
    index = COLORBLIND_MODES.index(normalized)
    return COLORBLIND_MODES[(index + step) % len(COLORBLIND_MODES)]


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

    def __init__(self, ctx: AppContext) -> None:
        super().__init__(ctx)
        self.selected_index = 0

    def _rows(self) -> list[str]:
        settings = self.ctx.persistent_data.settings
        graphics = self.ctx.persistent_data.graphics
        return [
            f"Theme: {graphics.theme_id.value.capitalize()}",
            f"Color Mode: {graphics.colorblind_mode.replace('_', ' ').title()}",
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
            "Show or hide board grid lines.",
            "Enable pickup and food burst particles.",
            "Disables most animation intensity and transitions.",
            "Applies small camera shake on key events.",
            "Changes base speed and score pace.",
            "Bounded walls or wrap-around movement.",
            "Adds static obstacle cells to the arena.",
            "Toggle all gameplay/menu sound effects.",
            "Return to main menu.",
        ]
        if 0 <= index < len(descriptions):
            return descriptions[index]
        return ""

    def _persist(self) -> None:
        save_persistent_data(self.ctx.persistent_data, self.ctx.data_path)

    def _change_value(self, step: int) -> None:
        settings = self.ctx.persistent_data.settings
        graphics = self.ctx.persistent_data.graphics

        if self.selected_index == 0:
            graphics.theme_id = _cycle_theme(graphics.theme_id, step)
        elif self.selected_index == 1:
            graphics.colorblind_mode = _cycle_color_mode(graphics.colorblind_mode, step)
        elif self.selected_index == 2:
            graphics.show_grid = not graphics.show_grid
        elif self.selected_index == 3:
            graphics.particles_enabled = not graphics.particles_enabled
        elif self.selected_index == 4:
            graphics.reduced_motion = not graphics.reduced_motion
            if graphics.reduced_motion:
                graphics.screen_shake_enabled = False
        elif self.selected_index == 5:
            if not graphics.reduced_motion:
                graphics.screen_shake_enabled = not graphics.screen_shake_enabled
        elif self.selected_index == 6:
            settings.difficulty = _cycle_difficulty(settings.difficulty, step)
        elif self.selected_index == 7:
            settings.map_mode = _cycle_map_mode(settings.map_mode, step)
        elif self.selected_index == 8:
            settings.obstacles_enabled = not settings.obstacles_enabled
        elif self.selected_index == 9:
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

        screen.fill(palette.background_top)
        draw_scene_header(
            screen=screen,
            width=self.ctx.config.window_width,
            title="Settings",
            subtitle="Graphics, Accessibility, and Gameplay",
            title_font=self.ctx.title_font,
            body_font=self.ctx.small_font,
            title_color=palette.accent,
            text_color=palette.text,
        )
        draw_option_rows(
            screen=screen,
            options=rows,
            selected_index=self.selected_index,
            center_x=self.ctx.config.window_width // 2,
            start_y=178,
            row_gap=30,
            font=self.ctx.small_font,
            text_color=palette.text,
            selected_text_color=palette.selected_text,
            row_width=560,
            row_height=28,
        )
        draw_hint_footer(
            screen=screen,
            text=self._description_for(self.selected_index),
            width=self.ctx.config.window_width,
            y=500,
            font=self.ctx.small_font,
            color=palette.text,
        )
        draw_hint_footer(
            screen=screen,
            text="Left/Right or Enter: Change   Esc: Back",
            width=self.ctx.config.window_width,
            y=532,
            font=self.ctx.small_font,
            color=palette.accent,
        )

