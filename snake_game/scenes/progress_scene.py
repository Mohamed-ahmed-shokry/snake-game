from __future__ import annotations

import pygame

from snake_game.persistence import PersistentData, best_score_for_settings
from snake_game.scenes.base import AppContext, Scene
from snake_game.systems.achievements import ACHIEVEMENTS
from snake_game.types import SceneId
from snake_game.ui.components import (
    draw_hint_footer,
    draw_panel,
    draw_scene_background,
    draw_scene_header,
    draw_text_center,
)
from snake_game.ui.theme import resolve_theme


def progress_summary_lines(data: PersistentData) -> list[str]:
    current_best = best_score_for_settings(data, data.settings)
    return [
        f"Runs Completed: {data.stats.total_runs}",
        f"Total Score: {data.stats.total_score}",
        f"Global Best: {data.stats.best_score_global}",
        f"Current Setup Best: {current_best}",
    ]


class ProgressScene(Scene):
    scene_id = SceneId.PROGRESS

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.ctx.audio.play("confirm")
            self.next_scene = SceneId.MENU
            return
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
            self.ctx.audio.play("confirm")
            self.next_scene = SceneId.MENU

    def update(self, delta_seconds: float) -> None:
        _ = delta_seconds

    def render(self, screen: pygame.Surface) -> None:
        theme = resolve_theme(
            self.ctx.config.graphics.theme_id,
            self.ctx.config.graphics.colorblind_mode,
        )
        palette = theme.palette
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
            title="Progress",
            subtitle="Career Stats and Achievements",
            title_font=self.ctx.title_font,
            body_font=self.ctx.small_font,
            title_color=palette.accent,
            text_color=palette.text,
        )

        stats_panel = pygame.Rect(self.ctx.config.window_width // 2 - 280, 160, 560, 104)
        draw_panel(
            screen=screen,
            rect=stats_panel,
            fill=(20, 20, 20),
            border=palette.grid,
            alpha=145,
            radius=14,
        )
        summary_lines = progress_summary_lines(self.ctx.persistent_data)
        for index, line in enumerate(summary_lines):
            column = index % 2
            row = index // 2
            draw_text_center(
                screen,
                line,
                self.ctx.small_font,
                palette.text,
                (self.ctx.config.window_width // 2 - 135 + column * 270, 190 + row * 42),
            )

        unlocked = set(self.ctx.persistent_data.achievements)
        draw_text_center(
            screen,
            f"Achievements {len(unlocked)}/{len(ACHIEVEMENTS)}",
            self.ctx.body_font,
            palette.selected_text,
            (self.ctx.config.window_width // 2, 300),
        )
        for index, achievement in enumerate(ACHIEVEMENTS):
            is_unlocked = achievement.id in unlocked
            status = "UNLOCKED" if is_unlocked else "LOCKED"
            color = palette.powerup if is_unlocked else palette.text
            draw_text_center(
                screen,
                f"{status}  |  {achievement.label} - {achievement.description}",
                self.ctx.small_font,
                color,
                (self.ctx.config.window_width // 2, 346 + index * 34),
            )

        draw_hint_footer(
            screen=screen,
            text="Enter, Esc, or Click: Main Menu",
            width=self.ctx.config.window_width,
            y=548,
            font=self.ctx.small_font,
            color=palette.accent,
        )
