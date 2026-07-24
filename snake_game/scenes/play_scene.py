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
from snake_game.systems.achievements import unlock_run_achievements
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


def direction_for_pointer(
    position: tuple[int, int],
    head_center: tuple[int, int],
    dead_zone: int = 4,
) -> Direction | None:
    delta_x = position[0] - head_center[0]
    delta_y = position[1] - head_center[1]
    if abs(delta_x) <= dead_zone and abs(delta_y) <= dead_zone:
        return None
    if abs(delta_x) >= abs(delta_y):
        return Direction.RIGHT if delta_x > 0 else Direction.LEFT
    return Direction.DOWN if delta_y > 0 else Direction.UP


@dataclass(slots=True)
class FxParticle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: int
    color: tuple[int, int, int]
    gravity: float = 240.0


@dataclass(slots=True)
class FloatingScore:
    x: float
    y: float
    points: int
    life: float = 0.9
    max_life: float = 0.9


class PlayScene(Scene):
    scene_id = SceneId.PLAY

    def __init__(self, ctx: AppContext) -> None:
        super().__init__(ctx)
        self.state = create_initial_state(ctx.config, ctx.persistent_data.settings, ctx.rng)
        self.best_score_at_start = best_score_for_settings(ctx.persistent_data, ctx.persistent_data.settings)
        self.progression = StageProgression(points_per_stage=ctx.config.stage_points_interval)
        self.hazards = HazardSystem(enabled=ctx.persistent_data.settings.obstacles_enabled)
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
        self.floating_scores: list[FloatingScore] = []
        self.visual_time = 0.0
        self.toast_text: str | None = None
        self.toast_timer = 0.0
        self.toast_color: tuple[int, int, int] = (255, 255, 255)
        self.pointer_feedback_position: tuple[int, int] | None = None
        self.pointer_feedback_timer = 0.0
        self.end_reason = "collision"

    def _spawn_burst(self, cell_x: int, cell_y: int, color: tuple[int, int, int], count: int = 8) -> None:
        if not self.ctx.config.graphics.particles_enabled:
            return
        if self.ctx.config.graphics.reduced_motion:
            return

        center_x = cell_x * self.ctx.config.cell_size + self.ctx.config.cell_size / 2
        center_y = cell_y * self.ctx.config.cell_size + self.ctx.config.cell_size / 2
        for _ in range(count):
            life = self.ctx.rng.uniform(0.20, 0.45)
            self.particles.append(
                FxParticle(
                    x=center_x,
                    y=center_y,
                    vx=self.ctx.rng.uniform(-80, 80),
                    vy=self.ctx.rng.uniform(-80, 80),
                    life=life,
                    max_life=life,
                    size=self.ctx.rng.randint(2, 4),
                    color=color,
                )
            )

    def _spawn_movement_trail(self, cell_x: int, cell_y: int) -> None:
        if not self.ctx.config.graphics.particles_enabled:
            return
        if self.ctx.config.graphics.reduced_motion:
            return

        theme = resolve_theme(
            self.ctx.config.graphics.theme_id,
            self.ctx.config.graphics.colorblind_mode,
        )
        center_x = cell_x * self.ctx.config.cell_size + self.ctx.config.cell_size / 2
        center_y = cell_y * self.ctx.config.cell_size + self.ctx.config.cell_size / 2
        for _ in range(2):
            life = self.ctx.rng.uniform(0.18, 0.30)
            self.particles.append(
                FxParticle(
                    x=center_x + self.ctx.rng.uniform(-3, 3),
                    y=center_y + self.ctx.rng.uniform(-3, 3),
                    vx=self.ctx.rng.uniform(-8, 8),
                    vy=self.ctx.rng.uniform(-8, 8),
                    life=life,
                    max_life=life,
                    size=max(2, self.ctx.config.cell_size // 7),
                    color=theme.palette.snake_body,
                    gravity=0.0,
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
            particle.vy += particle.gravity * delta_seconds
            alive.append(particle)
        self.particles = alive

    def _spawn_floating_score(self, cell_x: int, cell_y: int, points: int) -> None:
        self.floating_scores.append(
            FloatingScore(
                x=cell_x * self.ctx.config.cell_size + self.ctx.config.cell_size / 2,
                y=max(
                    96.0,
                    cell_y * self.ctx.config.cell_size - self.ctx.config.cell_size * 0.6,
                ),
                points=points,
            )
        )

    def _update_floating_scores(self, delta_seconds: float) -> None:
        alive: list[FloatingScore] = []
        for score in self.floating_scores:
            score.life -= delta_seconds
            if score.life <= 0:
                continue
            if not self.ctx.config.graphics.reduced_motion:
                score.y -= 34 * delta_seconds
            alive.append(score)
        self.floating_scores = alive

    def _draw_floating_scores(self, screen: pygame.Surface) -> None:
        theme = resolve_theme(
            self.ctx.config.graphics.theme_id,
            self.ctx.config.graphics.colorblind_mode,
        )
        for score in self.floating_scores:
            progress = max(0.0, min(1.0, score.life / score.max_life))
            fade_in = min(1.0, (1.0 - progress) * 7.0)
            alpha = round(255 * min(progress, fade_in))
            label = f"+{score.points}"
            if score.points > self.state.score_per_food:
                label = f"2X  +{score.points}"

            shadow = self.ctx.body_font.render(label, True, (4, 8, 12))
            shadow.set_alpha(alpha)
            text = self.ctx.body_font.render(label, True, theme.palette.selected_text)
            text.set_alpha(alpha)
            center = (round(score.x), round(score.y))
            screen.blit(shadow, shadow.get_rect(center=(center[0] + 2, center[1] + 3)))
            screen.blit(text, text.get_rect(center=center))

    def _draw_control_dock(self, screen: pygame.Surface) -> pygame.Rect:
        theme = resolve_theme(
            self.ctx.config.graphics.theme_id,
            self.ctx.config.graphics.colorblind_mode,
        )
        controls = (
            ("WASD / CLICK", "MOVE"),
            ("P", "PAUSE"),
            ("H", "HELP"),
            ("ESC", "MENU"),
        )
        rendered: list[tuple[pygame.Surface, pygame.Surface, int]] = []
        for key, action in controls:
            key_surface = self.ctx.small_font.render(key, True, theme.palette.selected_text)
            action_surface = self.ctx.small_font.render(action, True, theme.palette.text)
            rendered.append(
                (
                    key_surface,
                    action_surface,
                    key_surface.get_width() + action_surface.get_width() + 24,
                )
            )

        group_gap = 22
        content_width = sum(width for _, _, width in rendered) + group_gap * (len(rendered) - 1)
        dock_width = min(self.ctx.config.window_width - 28, content_width + 42)
        dock = pygame.Rect(0, 0, dock_width, 52)
        dock.midbottom = (self.ctx.config.window_width // 2, self.ctx.config.window_height - 10)
        draw_panel(
            screen=screen,
            rect=dock,
            fill=(6, 10, 16),
            border=tuple(max(28, channel // 2) for channel in theme.palette.grid),
            alpha=226,
            radius=16,
        )

        cursor_x = dock.centerx - content_width // 2
        for index, (key_surface, action_surface, group_width) in enumerate(rendered):
            key_rect = key_surface.get_rect(midleft=(cursor_x + 8, dock.centery)).inflate(16, 8)
            draw_panel(
                screen=screen,
                rect=key_rect,
                fill=(12, 20, 28),
                border=theme.palette.accent,
                alpha=235,
                radius=7,
            )
            screen.blit(key_surface, key_surface.get_rect(center=key_rect.center))
            action_rect = action_surface.get_rect(
                midleft=(key_rect.right + 8, dock.centery)
            )
            screen.blit(action_surface, action_rect)
            cursor_x += group_width
            if index < len(rendered) - 1:
                separator_x = cursor_x + group_gap // 2
                pygame.draw.line(
                    screen,
                    tuple(max(32, channel // 2) for channel in theme.palette.grid),
                    (separator_x, dock.top + 14),
                    (separator_x, dock.bottom - 14),
                    1,
                )
                cursor_x += group_gap
        return dock

    def _draw_pointer_feedback(self, screen: pygame.Surface) -> None:
        if self.pointer_feedback_position is None or self.pointer_feedback_timer <= 0:
            return

        theme = resolve_theme(
            self.ctx.config.graphics.theme_id,
            self.ctx.config.graphics.colorblind_mode,
        )
        layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        strength = max(0.0, min(1.0, self.pointer_feedback_timer / 0.45))
        progress = 1.0 - strength
        target_x, target_y = self.pointer_feedback_position
        head_x, head_y = self.state.snake[0]
        head_center = (
            head_x * self.ctx.config.cell_size + self.ctx.config.cell_size // 2,
            head_y * self.ctx.config.cell_size + self.ctx.config.cell_size // 2,
        )

        delta_x = target_x - head_center[0]
        delta_y = target_y - head_center[1]
        distance = max(1.0, (delta_x * delta_x + delta_y * delta_y) ** 0.5)
        dot_count = min(14, max(1, int(distance // 34)))
        for index in range(1, dot_count + 1):
            fraction = index / (dot_count + 1)
            dot_center = (
                round(head_center[0] + delta_x * fraction),
                round(head_center[1] + delta_y * fraction),
            )
            pygame.draw.circle(
                layer,
                (*theme.palette.accent, round(38 * strength)),
                dot_center,
                1 + (index % 3 == 0),
            )

        radius = 18 if self.ctx.config.graphics.reduced_motion else round(14 + progress * 22)
        pygame.draw.circle(
            layer,
            (*theme.palette.accent, round(210 * strength)),
            (target_x, target_y),
            radius,
            2,
        )
        tick_gap = radius + 5
        tick_length = 7
        for start, end in (
            ((target_x - tick_gap, target_y), (target_x - tick_gap + tick_length, target_y)),
            ((target_x + tick_gap, target_y), (target_x + tick_gap - tick_length, target_y)),
            ((target_x, target_y - tick_gap), (target_x, target_y - tick_gap + tick_length)),
            ((target_x, target_y + tick_gap), (target_x, target_y + tick_gap - tick_length)),
        ):
            pygame.draw.line(
                layer,
                (*theme.palette.selected_text, round(230 * strength)),
                start,
                end,
                2,
            )
        pygame.draw.circle(
            layer,
            (*theme.palette.selected_text, round(230 * strength)),
            (target_x, target_y),
            3,
        )
        screen.blit(layer, (0, 0))

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
        new_achievements = unlock_run_achievements(
            self.ctx.persistent_data,
            score=self.state.score,
            stage_reached=self.progression.current_stage,
            food_eaten=self.food_eaten_count,
            run_seconds=self.run_seconds,
        )
        self.ctx.last_result = SessionResult(
            score=self.state.score,
            leaderboard_key=score_key,
            leaderboard=leaderboard,
            is_new_high_score=is_new_high_score(existing_scores, self.state.score),
            stage_reached=self.progression.current_stage,
            food_eaten=self.food_eaten_count,
            run_seconds=self.run_seconds,
            new_achievements=new_achievements,
            end_reason=self.end_reason,
        )
        save_persistent_data(self.ctx.persistent_data, self.ctx.data_path)
        self.score_recorded = True
        self.ctx.audio.play("death")
        self.next_scene = SceneId.GAME_OVER

    def _dismiss_onboarding(self) -> None:
        self.onboarding_visible = False
        if not self.ctx.persistent_data.onboarding_seen:
            self.ctx.persistent_data.onboarding_seen = True
            save_persistent_data(self.ctx.persistent_data, self.ctx.data_path)

    def _show_toast(self, text: str, color: tuple[int, int, int], duration: float = 1.8) -> None:
        self.toast_text = text
        self.toast_color = color
        self.toast_timer = duration

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.WINDOWFOCUSLOST:
            if self.state.status == GameStatus.RUNNING and not self.onboarding_visible:
                self.state.status = GameStatus.PAUSED
                self._show_toast("AUTO-PAUSED", (120, 210, 255))
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.onboarding_visible:
                self._dismiss_onboarding()
                self.ctx.audio.play("confirm")
                return
            self.pointer_feedback_position = event.pos
            self.pointer_feedback_timer = 0.45
            head_x, head_y = self.state.snake[0]
            head_center = (
                head_x * self.ctx.config.cell_size + self.ctx.config.cell_size // 2,
                head_y * self.ctx.config.cell_size + self.ctx.config.cell_size // 2,
            )
            next_direction = direction_for_pointer(event.pos, head_center)
            if next_direction is not None:
                queue_direction_change(self.state, next_direction)
            return

        if event.type != pygame.KEYDOWN:
            return

        if self.onboarding_visible:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_h, pygame.K_ESCAPE):
                self._dismiss_onboarding()
                self.ctx.audio.play("confirm")
            return

        if event.key == pygame.K_h:
            self.onboarding_visible = True
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
        self.visual_time += max(0.0, delta_seconds)
        self._update_particles(delta_seconds)
        self._update_floating_scores(delta_seconds)

        if self.stage_banner_timer > 0:
            self.stage_banner_timer = max(0.0, self.stage_banner_timer - delta_seconds)
            if self.stage_banner_timer == 0:
                self.stage_banner_text = None
        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - delta_seconds)
        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - delta_seconds)
        if self.toast_timer > 0:
            self.toast_timer = max(0.0, self.toast_timer - delta_seconds)
            if self.toast_timer == 0:
                self.toast_text = None
        if self.pointer_feedback_timer > 0:
            self.pointer_feedback_timer = max(0.0, self.pointer_feedback_timer - delta_seconds)
            if self.pointer_feedback_timer == 0:
                self.pointer_feedback_position = None

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
        self.progression.update_from_score(self.state.score, emit=self.ctx.event_bus.emit)

        events = self.ctx.event_bus.drain()
        for event in events:
            if event.type == GameEventType.FOOD_EATEN:
                self.ctx.audio.play("eat")
                self.food_eaten_count += 1
                head_x = int(event.payload.get("head_x", self.state.snake[0][0]))
                head_y = int(event.payload.get("head_y", self.state.snake[0][1]))
                multiplier = max(1, int(event.payload.get("score_multiplier", 1)))
                self._spawn_floating_score(
                    head_x,
                    head_y,
                    self.state.score_per_food * multiplier,
                )
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
                previous_head_x = int(event.payload.get("previous_head_x", head_x))
                previous_head_y = int(event.payload.get("previous_head_y", head_y))
                self._spawn_movement_trail(previous_head_x, previous_head_y)
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
                self.ctx.audio.play("stage")
                stage = int(event.payload.get("stage", self.progression.current_stage))
                self.stage_banner_text = f"Stage {stage}"
                self.stage_banner_timer = 1.2
                self.flash_timer = max(self.flash_timer, 0.12)
                head_x, head_y = self.state.snake[0]
                safe_cells = {
                    (head_x + offset_x, head_y + offset_y)
                    for offset_x in range(-1, 2)
                    for offset_y in range(-1, 2)
                }
                forbidden_cells = set(self.state.snake) | {self.state.food} | safe_cells
                if self.powerups.spawned is not None:
                    forbidden_cells.add(self.powerups.spawned.position)
                added_hazards = self.hazards.advance_to_stage(
                    stage=stage,
                    obstacles=self.state.obstacles,
                    forbidden_cells=forbidden_cells,
                    grid_width=self.ctx.config.grid_width,
                    grid_height=self.ctx.config.grid_height,
                    rng=self.ctx.rng,
                )
                if added_hazards:
                    self._show_toast(
                        f"STAGE {stage}  |  +{len(added_hazards)} HAZARDS",
                        resolve_theme(
                            self.ctx.config.graphics.theme_id,
                            self.ctx.config.graphics.colorblind_mode,
                        ).palette.obstacle,
                    )
            elif event.type == GameEventType.PLAYER_DIED:
                reason = str(event.payload.get("reason", ""))
                if self.powerups.absorb_fatal_collision(reason):
                    self.state.status = GameStatus.RUNNING
                    self.ctx.audio.play("shield")
                    self.flash_timer = max(self.flash_timer, 0.18)
                    self.shake_timer = max(self.shake_timer, 0.12)
                    self._show_toast("SHIELD SAVED THE RUN", (120, 210, 255), duration=2.2)
                else:
                    self.end_reason = reason or "collision"

        for event in self.ctx.event_bus.drain():
            if event.type == GameEventType.POWERUP_COLLECTED:
                self.ctx.audio.play("powerup")
                self.flash_timer = max(self.flash_timer, 0.16)
                self.shake_timer = max(self.shake_timer, 0.08)
                head = self.state.snake[0]
                self._spawn_burst(head[0], head[1], (120, 210, 255), count=14)
                powerup_name = str(event.payload.get("powerup", "powerup")).replace("_", " ").upper()
                self._show_toast(f"{powerup_name} ACTIVATED", (247, 198, 85))

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
        spawned_powerup_type = self.powerups.spawned.type if self.powerups.spawned is not None else None
        theme = resolve_theme(
            self.ctx.config.graphics.theme_id,
            self.ctx.config.graphics.colorblind_mode,
        )

        particle_primitives = [
            (
                particle.x,
                particle.y,
                particle.size,
                particle.color,
                round(210 * max(0.0, min(1.0, particle.life / particle.max_life))),
            )
            for particle in self.particles
        ]
        effective_step_rate = max(0.1, self.state.steps_per_second * self.powerups.speed_multiplier())
        if self.ctx.config.graphics.reduced_motion:
            movement_alpha = 1.0
        else:
            movement_alpha = min(1.0, 0.25 + self.state.accumulator_seconds * effective_step_rate * 0.75)
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
            powerup_type=spawned_powerup_type,
            active_effect_labels=self.powerups.active_effect_labels(),
            active_powerup_types=self.powerups.active_types(),
            animation_seconds=self.visual_time,
            movement_alpha=movement_alpha,
            stage_banner_text=self.stage_banner_text,
            stage_banner_alpha=stage_banner_alpha,
            flash_alpha=flash_alpha,
            camera_offset=self._camera_offset(),
            particles=particle_primitives,
        )
        self._draw_pointer_feedback(screen)
        self._draw_floating_scores(screen)
        if self.countdown_remaining <= 0 and not self.onboarding_visible:
            control_dock = self._draw_control_dock(screen)
        else:
            control_dock = pygame.Rect(
                0,
                self.ctx.config.window_height,
                self.ctx.config.window_width,
                0,
            )

        if self.toast_text is not None and self.toast_timer > 0:
            toast_surface = self.ctx.small_font.render(self.toast_text, True, self.toast_color)
            toast_rect = toast_surface.get_rect(
                center=(self.ctx.config.window_width // 2, control_dock.top - 25)
            ).inflate(32, 16)
            draw_panel(
                screen=screen,
                rect=toast_rect,
                fill=(8, 12, 18),
                border=self.toast_color,
                alpha=220,
                radius=toast_rect.height // 2,
            )
            screen.blit(toast_surface, toast_surface.get_rect(center=toast_rect.center))

        if self.onboarding_visible:
            panel = pygame.Rect(
                self.ctx.config.window_width // 2 - 275,
                self.ctx.config.window_height // 2 - 150,
                550,
                300,
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
                (self.ctx.config.window_width // 2, panel.top + 78),
            )
            draw_centered_text(
                screen,
                "Mouse: Click where you want the snake to turn",
                self.ctx.small_font,
                theme.palette.text,
                (self.ctx.config.window_width // 2, panel.top + 108),
            )
            draw_centered_text(
                screen,
                "Shield: saves one hit   Slow: reduces speed",
                self.ctx.small_font,
                theme.palette.powerup,
                (self.ctx.config.window_width // 2, panel.top + 150),
            )
            draw_centered_text(
                screen,
                "Double: 2x score   Phase: crosses walls and hazards",
                self.ctx.small_font,
                theme.palette.powerup,
                (self.ctx.config.window_width // 2, panel.top + 180),
            )
            draw_centered_text(
                screen,
                "M: Mute sound   F11: Fullscreen   H: Toggle this help",
                self.ctx.small_font,
                theme.palette.text,
                (self.ctx.config.window_width // 2, panel.top + 220),
            )
            draw_centered_text(
                screen,
                "Press Enter, H, Esc, or Click to Continue",
                self.ctx.small_font,
                theme.palette.selected_text,
                (self.ctx.config.window_width // 2, panel.top + 262),
            )
