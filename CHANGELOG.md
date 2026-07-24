# Changelog

Notable user-facing and engineering changes are recorded here. The project follows [Semantic Versioning](https://semver.org/).

## 1.6.0 - 2026-07-24

### Added

- Continuous integration for linting, tests, branch coverage, and package builds.
- A persistent in-game warning when progress cannot be saved.
- Automated Ruff checks and a 75% branch-coverage quality floor.

### Changed

- Tall viewports now center menus and summary scenes more naturally.
- Particle rendering uses bounded temporary surfaces to reduce per-frame allocations.
- Invalid command-line configuration now reports a concise usage error.

### Fixed

- The runtime always shuts Pygame down, including after startup and save failures.
- Non-finite configuration and persistence values can no longer destabilize the game.
- Save files from newer schema versions are preserved instead of overwritten.
- Interactive save failures no longer terminate an active game.

## 1.5.0 - 2026-07-24

### Added

- Buffered-turn intent arrows, radial countdown animation, and an expanding start cue.
- Stage-reactive arena circuitry, score pulses, personal-best celebrations, and a stronger food beacon.
- A refreshed gameplay preview showcasing the enhanced arena presentation.

### Changed

- Improved countdown contrast and reduced repeated food-beacon rendering work.

## 1.4.0 - 2026-07-24

### Added

- Live HUD telemetry, a responsive control dock, click-steering feedback, and an animated objective beacon.

## 1.3.0 - 2026-07-24

### Added

- Danger effects, motion trails, floating score feedback, and cinematic stage transitions.

## 1.2.0 - 2026-07-24

### Added

- Smooth rounded snake motion, dimensional hazards, arena lighting, and stage-progress glow.

## 1.1.0 - 2026-07-24

### Added

- Redesigned scenes and HUD, richer audio, fullscreen and mute shortcuts, text scaling, onboarding, and active power-up effects.

## 1.0.0 - 2026-07-24

### Added

- Complete Snake gameplay with difficulties, bounded and wrap maps, obstacles, power-ups, stages, achievements, leaderboards, settings, persistence, mouse controls, and packaging.
