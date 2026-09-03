# Snake Arcade - Development Plan

## Current State (v1.6.3)
- Complete Snake gameplay with difficulties, map modes, obstacles, power-ups, stages
- Persistent settings, career progress, achievements, per-mode leaderboards
- Three themes (Neon, Sunset, Ocean) with colorblind modes
- Comprehensive graphics settings, mouse controls, fullscreen
- 143 tests, 79% branch coverage, clean linting

## Phase 1: Polish & Quality of Life (v1.7.0)

### 1.1 Custom Key Bindings
- [ ] Add key binding configuration to settings
- [ ] Support remapping WASD/Arrows, Pause, Mute, Fullscreen, Help
- [ ] Persist bindings in save file
- [ ] Apply bindings across all scenes

### 1.2 Gamepad/Controller Support
- [ ] Detect connected gamepads
- [ ] Map D-pad/left stick to movement
- [ ] Map face buttons to pause, confirm, back
- [ ] Add controller hint overlay in menus

### 1.3 Enhanced Audio
- [ ] Add background music tracks per theme
- [ ] Separate volume sliders for SFX and music
- [ ] Add audio device selection

### 1.4 Save Management
- [ ] Add "Export Save" / "Import Save" options
- [ ] Add "Reset Progress" with confirmation
- [ ] Show save file path in settings

## Phase 2: New Game Modes (v1.8.0)

### 2.1 Time Attack Mode
- [ ] Fixed time limit (60/120/300 seconds)
- [ ] Score as high as possible before time runs out
- [ ] Separate leaderboards

### 2.2 Survival Mode
- [ ] Infinite stages with increasing speed
- [ ] Obstacles spawn more aggressively
- [ ] No power-ups (or reduced)
- [ ] Separate leaderboards

### 2.3 Challenge Mode
- [ ] Pre-defined scenarios (maze layouts, speed runs, etc.)
- [ ] Daily/weekly challenges with seed
- [ ] Global leaderboards for challenges

## Phase 3: Visual & UX Enhancements (v1.9.0)

### 3.1 Replay System
- [ ] Record runs (inputs + RNG seed)
- [ ] Playback with ghost snake
- [ ] Export/share replay codes

### 3.2 Enhanced Visual Effects
- [ ] Screen shake intensity slider
- [ ] Particle density slider
- [ ] Optional scanline/CRT shader
- [ ] Snake trail effects customization

### 3.3 Accessibility
- [ ] High contrast mode improvements
- [ ] Optional slower game speeds
- [ ] Visual pause indicator
- [ ] Colorblind mode for power-up glyphs

## Phase 4: Content & Progression (v2.0.0)

### 4.1 Extended Achievements
- [ ] Add 10+ new achievements
- [ ] Achievement categories (Speed, Survival, Collection, Mastery)
- [ ] Progress tracking toward next achievement

### 4.2 Cosmetic Unlocks
- [ ] Unlockable snake skins
- [ ] Unlockable food/hazard appearances
- [ ] Unlockable arena themes
- [ ] Earned through achievements/stats

### 4.3 Statistics Dashboard
- [ ] Detailed run history
- [ ] Per-mode statistics
- [ ] Graphs/charts for progress visualization

## Phase 5: Technical Improvements (Ongoing)

### 5.1 Performance
- [ ] Profile and optimize rendering hot paths
- [ ] Reduce memory allocations in game loop
- [ ] Add benchmark mode

### 5.2 Code Quality
- [ ] Increase branch coverage to 85%+
- [ ] Add integration tests for full game flows
- [ ] Add property-based testing for logic

### 5.3 Distribution
- [ ] Windows executable via PyInstaller
- [ ] macOS app bundle
- [ ] Linux AppImage/Flatpak
- [ ] Steam integration (future)

## Immediate Next Steps (Priority Order)

1. **Custom Key Bindings** - High impact, requested feature
2. **Gamepad Support** - Accessibility, broad appeal
3. **Save Export/Import** - User data ownership
4. **Time Attack Mode** - New gameplay variety
5. **Extended Achievements** - Retention, goals

## Notes

- Each phase should maintain test coverage >= 75%
- All new features need tests before merge
- Update CHANGELOG.md with each release
- Version follows Semantic Versioning
- CI/CD must pass before any push