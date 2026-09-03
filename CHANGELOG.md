# Changelog

Notable user-facing and engineering changes are recorded here. The project follows [Semantic Versioning](https://semver.org/).

## 1.7.0 - 2026-09-03

### Added

- Customizable key bindings for all game actions (movement, pause, mute, fullscreen, help, menu navigation, confirm)
- Key bindings persist in save file and apply across all scenes
- Dynamic key hints in menus and game-over screens reflect current bindings

### Changed

- Updated all scenes (Menu, Settings, Progress, Game Over, Play) to use configurable key bindings
- Global shortcuts (Mute, Fullscreen) now respect custom bindings
- Settings scene navigation uses custom key bindings

## 1.6.3 - 2026-08-01

### Changed

- Continuous integration now verifies the lockfile, distribution metadata, and the installed wheel in addition to tests, linting, formatting, and builds.

### Fixed

- A Shield save now stops the remaining catch-up steps in that frame, preventing a second immediate collision during a momentary frame hitch.
- Programmatic configuration rejects non-integer, non-finite, and malformed values before Pygame or gameplay can encounter them.

## 1.6.2 - 2026-07-31

### Fixed

- Power-ups collected during a multi-step frame now affect the very next simulation step, so effects such as Double Score are never delayed by a momentary frame hitch.

### Changed

- Added regression coverage for the `python -m snake_game` package launcher.

## 1.6.1 - 2026-07-29

### Added

- Continuous integration now verifies Ruff formatting alongside lint and tests.
- Regression coverage for invalid UTF-8, excessively nested, oversized, and directory save paths.

### Changed

- Applied consistent Ruff formatting across the Python source and tests.

### Fixed

- Unreadable or pathological saves now fall back to defaults instead of crashing startup.
- Directory save targets are never renamed as corrupt files and are rejected during configuration.
- Save files larger than 1 MiB are preserved as corrupt backups without being loaded into memory.

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
