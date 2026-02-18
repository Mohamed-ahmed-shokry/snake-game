import pygame

from snake_game.persistence import save_persistent_data
from snake_game.render import draw_centered_text, draw_menu_list
from snake_game.scenes.base import AppContext, Scene
from snake_game.types import Difficulty, MapMode, SceneId


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
        return [
            f"Difficulty: {settings.difficulty.label}",
            f"Map Mode: {settings.map_mode.label}",
            f"Obstacles: {'On' if settings.obstacles_enabled else 'Off'}",
            f"Sound: {'Muted' if settings.muted else 'On'}",
            "Back",
        ]

    def _persist(self) -> None:
        save_persistent_data(self.ctx.persistent_data, self.ctx.data_path)

    def _change_value(self, step: int) -> None:
        settings = self.ctx.persistent_data.settings

        if self.selected_index == 0:
            settings.difficulty = _cycle_difficulty(settings.difficulty, step)
        elif self.selected_index == 1:
            settings.map_mode = _cycle_map_mode(settings.map_mode, step)
        elif self.selected_index == 2:
            settings.obstacles_enabled = not settings.obstacles_enabled
        elif self.selected_index == 3:
            settings.muted = not settings.muted
            self.ctx.audio.set_muted(settings.muted)
        else:
            self.next_scene = SceneId.MENU
            self.ctx.audio.play("confirm")
            return

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
        screen.fill(self.ctx.config.background_color)
        draw_centered_text(
            screen,
            "Settings",
            self.ctx.title_font,
            self.ctx.config.accent_color,
            (self.ctx.config.window_width // 2, 110),
        )
        draw_menu_list(
            screen=screen,
            lines=rows,
            selected_index=self.selected_index,
            top_y=220,
            font=self.ctx.body_font,
            color=self.ctx.config.text_color,
            selected_color=self.ctx.config.selected_text_color,
            center_x=self.ctx.config.window_width // 2,
        )
        draw_centered_text(
            screen,
            "Left/Right or Enter to change   Esc to return",
            self.ctx.small_font,
            self.ctx.config.text_color,
            (self.ctx.config.window_width // 2, 470),
        )
