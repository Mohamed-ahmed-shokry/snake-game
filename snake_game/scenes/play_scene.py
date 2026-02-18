from dataclasses import dataclass

import pygame

from snake_game.events import GameEvent, GameEventType
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
from snake_game.ui.components import draw_panel
from snake_game.ui.theme import resolve_theme

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


@dataclass(slots=True)
class FxParticle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    size: int
    color: tuple[int, int, int]


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

        self.stage_banner_text: str | None = None
        self.stage_banner_timer: float = 0.0
        self.flash_timer: float = 0.0
        self.shake_timer: float = 0.0

        self.food_eaten_count = 0
        self.run_seconds = 0.0

        self.onboarding_visible = not ctx.persistent_data.onboarding_seen
        self.particles: list[FxParticle] = []

    def _spawn_burst(self, cell_x: int, cell_y: int, color: tuple[int, int, int], count: int = 8) -> None:
        if not self.ctx.config.graphics.particles_enabled:
            return
        if self.ctx.config.graphics.reduced_motion:
            return

        center_x = cell_x * self.ctx.config.cell_size + self.ctx.config.cell_size / 2
        center_y = cell_y * self.ctx.config.cell_size + self.ctx.config.cell_size / 2
        for _ in range(count):
            self.particles.append(
                FxParticle(
                    x=center_x,
                    y=center_y,
                    vx=self.ctx.rng.uniform(-80, 80),
                    vy=self.ctx.rng.uniform(-80, 80),
                    life=self.ctx.rng.uniform(0.20, 0.45),
                    size=self.ctx.rng.randint(2, 4),
                    color=color,
                )
            )

    def _update_particles(self, delta_seconds: float) -> None:
        if not self.particles:
            return
        alive: list[FxParticle] = []
        for particle in self.particles:
            particle.life -= delta_seconds
            if particle.life <= 0:
                continue
            particle.x += particle.vx * delta_seconds
            particle.y += particle.vy * delta_seconds
            particle.vy += 240 * delta_seconds
            alive.append(particle)
        self.particles = alive

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
            stage_reached=self.progression.current_stage,
            food_eaten=self.food_eaten_count,
            run_seconds=self.run_seconds,
        )
        self.score_recorded = True
        self.ctx.audio.play("death")
        self.next_scene = SceneId.GAME_OVER

    def _dismiss_onboarding(self) -> None:
        self.onboarding_visible = False
        if not self.ctx.persistent_data.onboarding_seen:
            self.ctx.persistent_data.onboarding_seen = True
            save_persistent_data(self.ctx.persistent_data, self.ctx.data_path)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if self.onboarding_visible:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_h):
                self._dismiss_onboarding()
                self.ctx.audio.play("confirm")
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

    def update(self, delta_seconds: float) -> None:
        self._update_particles(delta_seconds)

        if self.stage_banner_timer > 0:
            self.stage_banner_timer = max(0.0, self.stage_banner_timer - delta_seconds)
            if self.stage_banner_timer == 0:
                self.stage_banner_text = None
        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - delta_seconds)
        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - delta_seconds)

        if self.ctx.config.graphics.reduced_motion:
            self.stage_banner_text = None
            self.stage_banner_timer = 0.0
            self.flash_timer = 0.0
            self.shake_timer = 0.0
            self.particles.clear()

        if self.onboarding_visible:
            return

        if self.state.status == GameStatus.PAUSED:
            return

        if self.countdown_remaining > 0:
            self.countdown_remaining = max(0.0, self.countdown_remaining - delta_seconds)
            return

        self.run_seconds += delta_seconds
        self.powerups.update(delta_seconds)
        advance_simulation(
            self.state,
            self.ctx.config,
            delta_seconds,
            self.ctx.rng,
            score_multiplier=self.powerups.score_multiplier(),
            speed_multiplier=self.powerups.speed_multiplier(),
            phase_active=self.powerups.phase_active(),
            emit=self.ctx.event_bus.emit,
        )
        self.hazards.update()
        self.progression.update_from_score(self.state.score, emit=self.ctx.event_bus.emit)

        events = self.ctx.event_bus.drain()
        for event in events:
            if event.type == GameEventType.FOOD_EATEN:
                self.ctx.audio.play("eat")
                self.food_eaten_count += 1
                head_x = int(event.payload.get("head_x", self.state.snake[0][0]))
                head_y = int(event.payload.get("head_y", self.state.snake[0][1]))
                self._spawn_burst(head_x, head_y, (245, 165, 95), count=10)

                occupied_cells = set(self.state.snake) | set(self.state.obstacles) | {self.state.food}
                self.powerups.maybe_spawn(
                    rng=self.ctx.rng,
                    occupied_cells=occupied_cells,
                    grid_width=self.ctx.config.grid_width,
                    grid_height=self.ctx.config.grid_height,
                )
            elif event.type == GameEventType.STEP_ADVANCED:
                head_x = int(event.payload.get("head_x", self.state.snake[0][0]))
                head_y = int(event.payload.get("head_y", self.state.snake[0][1]))
                collected = self.powerups.collect_at((head_x, head_y))
                if collected is not None:
                    self.ctx.event_bus.emit(
                        GameEvent(
                            type=GameEventType.POWERUP_COLLECTED,
                            payload={
                                "powerup": collected.type.value,
                                "duration_seconds": round(collected.remaining_seconds, 1),
                            },
                        )
                    )
            elif event.type == GameEventType.STAGE_ADVANCED:
                self.ctx.audio.play("confirm")
                self.stage_banner_text = f"Stage {self.progression.current_stage}"
                self.stage_banner_timer = 1.2
                self.flash_timer = max(self.flash_timer, 0.12)
            elif event.type == GameEventType.PLAYER_DIED:
                reason = str(event.payload.get("reason", ""))
                if self.powerups.absorb_fatal_collision(reason):
                    self.state.status = GameStatus.RUNNING
                    self.ctx.audio.play("confirm")
                    self.flash_timer = max(self.flash_timer, 0.18)
                    self.shake_timer = max(self.shake_timer, 0.12)

        for event in self.ctx.event_bus.drain():
            if event.type == GameEventType.POWERUP_COLLECTED:
                self.ctx.audio.play("confirm")
                self.flash_timer = max(self.flash_timer, 0.16)
                self.shake_timer = max(self.shake_timer, 0.08)
                head = self.state.snake[0]
                self._spawn_burst(head[0], head[1], (120, 210, 255), count=14)

        if self.state.status == GameStatus.GAME_OVER:
            self._record_and_transition()

    def _camera_offset(self) -> tuple[int, int]:
        if self.ctx.config.graphics.reduced_motion:
            return (0, 0)
        if not self.ctx.config.graphics.screen_shake_enabled:
            return (0, 0)
        if self.shake_timer <= 0:
            return (0, 0)
        intensity = 4 if self.shake_timer > 0.06 else 2
        return (
            self.ctx.rng.randint(-intensity, intensity),
            self.ctx.rng.randint(-intensity, intensity),
        )

    def render(self, screen: pygame.Surface) -> None:
        best_score_now = max(self.best_score_at_start, self.state.score)
        spawned_powerup_position = self.powerups.spawned.position if self.powerups.spawned is not None else None
        theme = resolve_theme(
            self.ctx.config.graphics.theme_id,
            self.ctx.config.graphics.colorblind_mode,
        )

        particle_primitives = [
            (particle.x, particle.y, particle.size, particle.color) for particle in self.particles
        ]
        stage_banner_alpha = int(210 * min(1.0, self.stage_banner_timer / 1.2))
        flash_alpha = int(150 * min(1.0, self.flash_timer / 0.18))

        draw_playfield(
            screen=screen,
            state=self.state,
            config=self.ctx.config,
            hud_font=self.ctx.title_font,
            small_font=self.ctx.small_font,
            countdown_remaining=self.countdown_remaining,
            best_score=best_score_now,
            stage=self.progression.current_stage,
            powerup_position=spawned_powerup_position,
            active_effect_labels=self.powerups.active_effect_labels(),
            stage_banner_text=self.stage_banner_text,
            stage_banner_alpha=stage_banner_alpha,
            flash_alpha=flash_alpha,
            camera_offset=self._camera_offset(),
            particles=particle_primitives,
        )
        if self.countdown_remaining <= 0 and not self.onboarding_visible:
            draw_centered_text(
                screen,
                "P/Space: Pause   Esc: Menu",
                self.ctx.small_font,
                theme.palette.text,
                (self.ctx.config.window_width // 2, self.ctx.config.window_height - 24),
            )

        if self.onboarding_visible:
            panel = pygame.Rect(
                self.ctx.config.window_width // 2 - 275,
                self.ctx.config.window_height // 2 - 110,
                550,
                220,
            )
            draw_panel(
                screen=screen,
                rect=panel,
                fill=(18, 24, 32),
                border=theme.palette.accent,
                alpha=220,
                radius=16,
            )
            draw_centered_text(
                screen,
                "Quick Controls",
                self.ctx.body_font,
                theme.palette.accent,
                (self.ctx.config.window_width // 2, panel.top + 34),
            )
            draw_centered_text(
                screen,
                "Move: Arrow Keys / WASD    Pause: P or Space",
                self.ctx.small_font,
                theme.palette.text,
                (self.ctx.config.window_width // 2, panel.top + 84),
            )
            draw_centered_text(
                screen,
                "Goal: Eat food, survive hazards, use power-ups.",
                self.ctx.small_font,
                theme.palette.text,
                (self.ctx.config.window_width // 2, panel.top + 116),
            )
            draw_centered_text(
                screen,
                "Press Enter to Start",
                self.ctx.small_font,
                theme.palette.selected_text,
                (self.ctx.config.window_width // 2, panel.top + 162),
            )

