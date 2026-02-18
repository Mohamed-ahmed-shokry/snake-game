import pygame

from snake_game.logic import advance_simulation, create_initial_state, queue_direction_change
from snake_game.persistence import leaderboard_key, record_score, save_persistent_data
from snake_game.render import draw_centered_text, draw_playfield
from snake_game.scenes.base import AppContext, Scene, SessionResult
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

        leaderboard = record_score(
            self.ctx.persistent_data,
            self.ctx.persistent_data.settings,
            self.state.score,
            self.ctx.config.leaderboard_limit,
        )
        save_persistent_data(self.ctx.persistent_data, self.ctx.data_path)
        self.ctx.last_result = SessionResult(
            score=self.state.score,
            leaderboard_key=leaderboard_key(self.ctx.persistent_data.settings),
            leaderboard=leaderboard,
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

        advance_simulation(self.state, self.ctx.config, delta_seconds, self.ctx.rng)
        if self.state.status == GameStatus.GAME_OVER:
            self._record_and_transition()

    def render(self, screen: pygame.Surface) -> None:
        draw_playfield(
            screen=screen,
            state=self.state,
            config=self.ctx.config,
            hud_font=self.ctx.title_font,
            small_font=self.ctx.small_font,
            countdown_remaining=self.countdown_remaining,
        )
        if self.countdown_remaining <= 0:
            draw_centered_text(
                screen,
                "P/Space: Pause   Esc: Menu",
                self.ctx.small_font,
                self.ctx.config.text_color,
                (self.ctx.config.window_width // 2, self.ctx.config.window_height - 24),
            )

