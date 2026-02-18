import pygame

from snake_game.events import GameEventType
from snake_game.logic import advance_simulation, create_initial_state, queue_direction_change
from snake_game.persistence import (
    best_score_for_settings,
    is_new_high_score,
    leaderboard_key,
    record_score,
    save_persistent_data,
    update_run_stats,
)
from snake_game.render import draw_centered_text, draw_playfield
from snake_game.scenes.base import AppContext, Scene, SessionResult
from snake_game.systems.hazards import HazardSystem
from snake_game.systems.powerups import PowerUpSystem
from snake_game.systems.progression import StageProgression
from snake_game.types import Direction, GameStatus, SceneId

KEY_TO_DIRECTION = {
    pygame.K_UP: Direction.UP,
    pygame.K_w: Direction.UP,
    pygame.K_DOWN: Direction.DOWN,
    pygame.K_s: Direction.DOWN,
    pygame.K_LEFT: Direction.LEFT,
    pygame.K_a: Direction.LEFT,
    pygame.K_RIGHT: Direction.RIGHT,
    pygame.K_d: Direction.RIGHT,
}


class PlayScene(Scene):
    scene_id = SceneId.PLAY

    def __init__(self, ctx: AppContext) -> None:
        super().__init__(ctx)
        self.state = create_initial_state(ctx.config, ctx.persistent_data.settings, ctx.rng)
        self.best_score_at_start = best_score_for_settings(ctx.persistent_data, ctx.persistent_data.settings)
        self.progression = StageProgression(points_per_stage=ctx.config.stage_points_interval)
        self.hazards = HazardSystem(enabled=False)
        self.powerups = PowerUpSystem()
        self.countdown_remaining = ctx.config.countdown_seconds
        self.score_recorded = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.next_scene = SceneId.MENU
            return

        if event.key in KEY_TO_DIRECTION:
            queue_direction_change(self.state, KEY_TO_DIRECTION[event.key])
            return

        if event.key in (pygame.K_p, pygame.K_SPACE):
            if self.state.status == GameStatus.RUNNING:
                self.state.status = GameStatus.PAUSED
            elif self.state.status == GameStatus.PAUSED:
                self.state.status = GameStatus.RUNNING
            self.ctx.audio.play("confirm")

    def _record_and_transition(self) -> None:
        if self.score_recorded:
            return

        settings = self.ctx.persistent_data.settings
        score_key = leaderboard_key(settings)
        existing_scores = list(self.ctx.persistent_data.leaderboard.get(score_key, []))

        leaderboard = record_score(
            self.ctx.persistent_data,
            settings,
            self.state.score,
            self.ctx.config.leaderboard_limit,
        )
        update_run_stats(self.ctx.persistent_data, self.state.score)
        save_persistent_data(self.ctx.persistent_data, self.ctx.data_path)
        self.ctx.last_result = SessionResult(
            score=self.state.score,
            leaderboard_key=score_key,
            leaderboard=leaderboard,
            is_new_high_score=is_new_high_score(existing_scores, self.state.score),
        )
        self.score_recorded = True
        self.ctx.audio.play("death")
        self.next_scene = SceneId.GAME_OVER

    def update(self, delta_seconds: float) -> None:
        if self.state.status == GameStatus.PAUSED:
            return

        if self.countdown_remaining > 0:
            self.countdown_remaining = max(0.0, self.countdown_remaining - delta_seconds)
            return

        advance_simulation(
            self.state,
            self.ctx.config,
            delta_seconds,
            self.ctx.rng,
            emit=self.ctx.event_bus.emit,
        )
        self.hazards.update()
        self.powerups.update(delta_seconds)
        self.progression.update_from_score(self.state.score, emit=self.ctx.event_bus.emit)

        events = self.ctx.event_bus.drain()
        for event in events:
            if event.type == GameEventType.FOOD_EATEN:
                self.ctx.audio.play("eat")
            elif event.type == GameEventType.STAGE_ADVANCED:
                self.ctx.audio.play("confirm")
        if self.state.status == GameStatus.GAME_OVER:
            self._record_and_transition()

    def render(self, screen: pygame.Surface) -> None:
        best_score_now = max(self.best_score_at_start, self.state.score)
        draw_playfield(
            screen=screen,
            state=self.state,
            config=self.ctx.config,
            hud_font=self.ctx.title_font,
            small_font=self.ctx.small_font,
            countdown_remaining=self.countdown_remaining,
            best_score=best_score_now,
            stage=self.progression.current_stage,
        )
        if self.countdown_remaining <= 0:
            draw_centered_text(
                screen,
                "P/Space: Pause   Esc: Menu",
                self.ctx.small_font,
                self.ctx.config.text_color,
                (self.ctx.config.window_width // 2, self.ctx.config.window_height - 24),
            )
