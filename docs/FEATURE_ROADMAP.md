# EmuCraft Development Roadmap

This document is the implementation contract for the next development stages. A feature is not considered complete merely because a setting or screen exists; it must be connected to the emulator core and tested.

## 1. Appearance

Required selectable combinations:
- Anime Dark
- Anime Light
- Donghua Dark
- Donghua Light

The selected character style and color mode must persist after app restart. Appearance preferences must not alter emulator performance settings.

## 2. Emulator functionality — all required

All of the following are in scope and must be implemented, not treated as optional:
- BIOS import, validation, selection, and per-user BIOS management. BIOS files are supplied by the user and are never bundled.
- Game import, scanning, metadata/library management, duplicate handling, and supported format detection (ISO, CHD, CSO, BIN where supported by the engine).
- Launching games and reporting actionable errors for missing/invalid BIOS or unsupported images.
- Per-game settings and compatibility profiles.
- Save states, load states, and PS2 memory-card management.
- Game library management, storage permissions, and safe deletion/backup flows.

## 3. Performance profiles

Provide four simple presets, with per-game persistence and an explicit Manual mode.

### FPS Max
Prioritize frame pacing and speed. Select conservative internal resolution and graphics options, reduce expensive enhancements, and use a 30/60 FPS cap only where the game/core/device supports it. Do not promise an FPS value that the game or hardware cannot sustain.

### Graphics Max
Prioritize image quality. Raise internal resolution and supported visual enhancements within device limits. FPS may fall below 60; expose 30/60 caps only when technically supported and explain that a cap is not a performance guarantee.

### Device Performance
Automatically choose conservative settings using detected ABI, CPU/GPU renderer and capabilities, available memory, thermal/power signals where Android exposes them, and measured game performance. Re-evaluate safely when device conditions change. Never claim to identify exact chipset capabilities when Android does not expose them.

### Normal / Manual
Normal starts from balanced defaults. Manual exposes the underlying supported emulator options and leaves them under the player's control. Changing a preset must update the actual core configuration, not just the UI.

## 4. Required technical safeguards

- Keep global defaults separate from per-game overrides.
- Persist selected profile and effective values; provide a reset-to-recommended action.
- Detect unsupported options and hide/disable them rather than silently pretending they work.
- Avoid changing settings while a game is running unless the core supports safe live reconfiguration.
- Do not silently overwrite a user's Manual settings when switching games.
- Show the reason for automatic choices where practical.
- Treat thermal/performance tuning as best-effort; Android device APIs and vendor drivers vary.
- Preserve upstream ARMSX2/PCSX2 notices and GPL-3.0 source obligations.

## 5. Completion and validation gates

### Appearance
- [x] Anime/Donghua dark/light palette options are patched into the Android build.
- [ ] Verify visual rendering on device in all four combinations.
- [ ] Complete distinct Modern and Console layouts (current Console choice only changes toolbar placement; it is not a complete console-style layout).
- [ ] Replace the current simple vector mascot with polished original Anime and Donghua artwork and richer animations.

### Emulator
- [ ] BIOS management and validation.
- [ ] ISO/CHD/CSO/BIN import and scanning, based on formats actually supported by the pinned core.
- [ ] Library and per-game management.
- [ ] Game boot and actionable error handling.
- [ ] Save/load states and memory cards.
- [ ] Compatibility testing across a representative game set.

### Settings and optimization
- [ ] Inventory the upstream core's real graphics, speed, audio, and controller settings.
- [ ] Implement FPS Max preset and validate effective core values.
- [ ] Implement Graphics Max preset and validate effective core values.
- [ ] Implement Device Performance detection and safe adaptive tuning.
- [ ] Implement Normal and Manual settings with per-game persistence.
- [ ] Validate 30/60 FPS cap behavior only where supported by the core/game.

### Device validation
- [ ] ARM64 install and launch.
- [ ] Test Adreno and Mali devices.
- [ ] Test mid-range and high-end Android devices.
- [ ] Measure frame pacing, heat, battery use, crashes, and save integrity.

## 6. Current build status

The GitHub Actions run for commit `48ef3063ef4d2e1f0862ccc125d6022b180e3f37` completed successfully and uploaded the `emucraft-arm64-debug-apk` artifact. This confirms compilation and packaging only; it does not prove that BIOS boot, game emulation, or all emulator features have passed device testing.


## 7. Pinned ARMSX2 implementation inventory

Inspected against upstream revision `a2914992c8c507d4c196464dbcf773fc7b0d0def` used by CI.

### Engine settings already exposed by the pinned Android source
- CPU / speed: EE cycle rate and skip, MTVU, IOP thread, VU1 instant, VU flag hack, fast CDVD, INTC_STAT, wait-loop detection, recompiler and clamp controls.
- Frame pacing: native frame limiter, nominal speed percentage, and a separate presentation FPS cap. The latter drops display presents and does not slow emulation.
- Graphics: renderer backend, internal resolution multiplier, blending accuracy, hardware mipmaps, texture preloading, hardware download mode, filtering, FXAA, texture upscaling and other GS options.
- Persistence / native bridge: `Settings.applyTo()` maps the Kotlin settings model to `NativeApp.setSetting()` followed by `commitSettings()`. `ConfigStore` keeps global settings and sparse per-game overrides; `InGameOverlay.saveSettings()` uses the active scope.
- Device signals: `DeviceTier` already checks CPU core count, low-RAM flag and total RAM; `Thermals.kt` and `BatteryWatcher.kt` exist for best-effort thermal/power signals. GPU/renderer detection is in `GpuInfo.kt`.

### BIOS, library and save systems inherited from upstream
- BIOS: upstream contains `BiosInfo.kt`, native BIOS inspection and setup state for the selected BIOS, source folder and private BIOS copy. The user supplies the BIOS.
- Game library: upstream `MainActivityRuntime` persists multiple SAF ROM folder URIs, subfolder scan policy and deduplicates library results. `GameInfo.kt` contains library metadata, hidden-game and category handling.
- Game boot: upstream runtime and native bridge provide the VM launch path. This still needs an actual BIOS + legally obtained game image test on physical hardware.
- Save states: upstream Android runtime and in-game menu include save/load-state flows; validate persistence and restore on device.
- Memory cards: upstream includes `MemoryCardBackup.kt` and `memcard/Ps2MemoryCard.kt`; validate card creation, selection, writes, backup and restore on device.

These are inherited engine capabilities, not proof of end-to-end functionality in the EmuCraft-branded APK. The CI build does not exercise storage permissions, native BIOS validation, game boot, state restore or memory-card writes.

## 8. EmuCraft performance profile implementation

The UI patch now adds four profile choices to the upstream Performance tab:
- FPS Max: native resolution, lower-cost blending/mipmap/preload settings and selected CPU speedhacks.
- Graphics Max: 2x internal resolution, higher blending quality, full texture preloading and FXAA.
- Device Performance: uses upstream `DeviceTier.isLowEnd()`, based on Android low-RAM status, CPU core count and total RAM; applies the low-end preset or a balanced 1.5x preset.
- Normal / Manual: preserves current values and does not overwrite custom tuning.

The profiles operate on the upstream `Settings` object and use `InGameOverlay.saveSettings()`, so they feed the same native setting-commit path and respect Global/Game scope. Exact preset matching is used to display Manual when settings are custom. Thermal adaptation remains a later task; device heuristics are not a benchmark or FPS guarantee.
