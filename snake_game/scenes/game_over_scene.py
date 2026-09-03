import pygame

from snake_game.scenes.base import AppContext, Scene
from snake_game.systems.achievements import achievement_label
from snake_game.types import SceneId
from snake_game.ui.components import (
    draw_hint_footer,
    draw_option_rows,
    draw_scene_background,
    draw_scene_header,
)
from snake_game.ui.layout import option_index_at, scene_vertical_offset
from snake_game.ui.theme import resolve_theme


def format_run_time(seconds: float) -> str:
    safe_seconds = max(0, int(seconds))
    minutes, remaining_seconds = divmod(safe_seconds, 60)
    return f"{minutes}:{remaining_seconds:02d}"


def top_scores_text(leaderboard: list[int]) -> str:
    if not leaderboard:
        return "Top Scores (Current Setup): None yet"
    return "Top Scores (Current Setup): " + ", ".join(str(value) for value in leaderboard[:5])


def achievement_unlock_lines(achievement_ids: list[str]) -> list[str]:
    labels = [achievement_label(achievement_id) for achievement_id in achievement_ids]
    return [
        f"Unlocked: {', '.join(labels[index : index + 2])}" for index in range(0, len(labels), 2)
    ]


def end_reason_text(reason: str) -> str:
    labels = {
        "wall": "Hit the arena wall",
        "obstacle": "Hit a stage hazard",
        "self_collision": "Ran into your own trail",
        "board_full": "Board cleared - perfect run!",
        "collision": "Run complete",
    }
    return labels.get(reason, "Run complete")


class GameOverScene(Scene):
    scene_id = SceneId.GAME_OVER
    option_start_y = 318
    option_gap = 42
    option_width = 460
    option_height = 34

    def __init__(self, ctx: AppContext) -> None:
        super().__init__(ctx)
        self.selected_index = 0
        self.options = ["Play Again", "Main Menu", "Quit"]

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
            self.next_scene = SceneId.MENU

    def _activate_selected(self) -> None:
        self.ctx.audio.play("confirm")
        selected = self.options[self.selected_index]
        if selected == "Play Again":
            self.next_scene = SceneId.PLAY
        elif selected == "Main Menu":
            self.next_scene = SceneId.MENU
        else:
            self.quit_requested = True

    def update(self, delta_seconds: float) -> None:
        _ = delta_seconds

    def render(self, screen: pygame.Surface) -> None:
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
            palette.food,
        )
        draw_scene_header(
            screen=screen,
            width=self.ctx.config.window_width,
            title="Game Over",
            subtitle="Run Summary",
            title_font=self.ctx.title_font,
            body_font=self.ctx.small_font,
            title_color=palette.food,
            text_color=palette.text,
            offset_y=offset_y,
        )

        result = self.ctx.last_result
        score_value = result.score if result else 0
        leaderboard = result.leaderboard if result else []
        new_best = result.is_new_high_score if result else False
        stage_reached = result.stage_reached if result else 1
        food_eaten = result.food_eaten if result else 0
        run_seconds = result.run_seconds if result else 0.0
        new_achievements = result.new_achievements if result else []
        end_reason = result.end_reason if result else "collision"

        summary_text = (
            f"Score {score_value}  |  Stage {stage_reached}  |  "
            f"Food {food_eaten}  |  Time {format_run_time(run_seconds)}"
        )
        draw_hint_footer(
            screen=screen,
            text=summary_text,
            width=self.ctx.config.window_width,
            y=180 + offset_y,
            font=self.ctx.small_font,
            color=palette.text,
        )
        draw_hint_footer(
            screen=screen,
            text=end_reason_text(end_reason),
            width=self.ctx.config.window_width,
            y=210 + offset_y,
            font=self.ctx.small_font,
            color=palette.food if end_reason != "board_full" else palette.powerup,
        )
        if new_best:
            draw_hint_footer(
                screen=screen,
                text="New High Score!",
                width=self.ctx.config.window_width,
                y=238 + offset_y,
                font=self.ctx.small_font,
                color=palette.selected_text,
            )

        for index, line in enumerate(achievement_unlock_lines(new_achievements)[:2]):
            draw_hint_footer(
                screen=screen,
                text=line,
                width=self.ctx.config.window_width,
                y=264 + index * 22 + offset_y,
                font=self.ctx.small_font,
                color=palette.powerup,
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

        draw_hint_footer(
            screen=screen,
            text=top_scores_text(leaderboard),
            width=self.ctx.config.window_width,
            y=468 + offset_y,
            font=self.ctx.small_font,
            color=palette.accent,
        )
        draw_hint_footer(
            screen=screen,
            text=f"{pygame.key.name(self.ctx.persistent_data.settings.key_bindings.confirm).upper()} / Click: Select   "
            f"{pygame.key.name(self.ctx.persistent_data.settings.key_bindings.menu_back).upper()}: Main Menu",
            width=self.ctx.config.window_width,
            y=508 + offset_y,
            font=self.ctx.small_font,
            color=palette.text,
        )
