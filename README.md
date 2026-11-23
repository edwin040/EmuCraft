# EmuCraft

EmuCraft is an Android-first PS2 emulator project. The Android application now uses the existing **ARMSX2 Android application and PCSX2-derived emulation core as its foundation**, rather than maintaining a separate placeholder shell.

## Current implementation direction

- Upstream base: [ARMSX2](https://github.com/ARMSX2/ARMSX2)
- Pinned upstream revision: `a2914992c8c507d4c196464dbcf773fc7b0d0def`
- Android application and native ARM64 emulation core are built from that pinned source.
- CI overrides the Android application ID to `com.emucraft.ps2` and launcher label to `EmuCraft`.
- ABI target: `arm64-v8a`
- Minimum Android version from the upstream base: Android 8.0 (API 26).
- BIOS and game images must be supplied by the user; EmuCraft will not bundle copyrighted firmware or commercial game images.

The initial CI build uses the upstream GitHub flavor. It is a first integrated EmuCraft-branded build, not yet a fully rebranded product. Some internal screens, About text, assets, and upstream identifiers may still display ARMSX2 and will be reviewed and customized in subsequent milestones.

## Device targets

The intended compatibility targets are:
- Baseline testing: Snapdragon 720G-class devices.
- Additional targets: Snapdragon 778G / 7-series and MediaTek Dimensity 7200-class or better.
- Both Adreno and Mali GPUs are in scope, subject to renderer and driver compatibility.

These are testing targets, not a guarantee that every PS2 title will run at full speed. Actual performance must be measured on physical devices and per game.

## Build

GitHub Actions builds the pinned upstream Android project using:
- JDK 17
- Android SDK API 36 for the current CI runner
- Android NDK 29.0.14206865
- CMake 3.31.6
- ARM64-v8a

The upstream revision declares API 37; the CI workflow currently adapts compile/target SDK to API 36 and uses compatible AndroidX dependency versions because API 37 is not available in the runner's configured SDK repository. These CI-only adaptations are applied to the checkout and do not rewrite the upstream repository.

To build locally, first clone the pinned ARMSX2 source with its submodules, then follow its Android build documentation. The EmuCraft workflow in `.github/workflows/android-build.yml` is the current reproducible build recipe.

## Licensing and source

The integrated emulator base is licensed under **GNU GPL version 3**. See [COPYING.GPLv3](COPYING.GPLv3) and the upstream source repository. Changes and distribution of binaries must comply with GPL-3.0, including providing the corresponding source and preserving applicable notices and third-party license terms.

- Upstream source: https://github.com/ARMSX2/ARMSX2
- Pinned source commit: https://github.com/ARMSX2/ARMSX2/commit/a2914992c8c507d4c196464dbcf773fc7b0d0def
- This repository contains the EmuCraft build configuration and project-specific modifications. The pinned upstream source is checked out by CI at build time.

## Next milestones

1. Verify the integrated APK installs and launches on real ARM64 Android devices.
2. Replace remaining upstream branding and review the full user-facing flow as EmuCraft.
3. Verify BIOS selection, game library scanning, and game boot with legally supplied files.
4. Test Vulkan/OpenGL renderer selection, audio, touch controls, and external controllers.
5. Run compatibility and performance tests on Snapdragon and MediaTek devices.
6. Review all upstream and third-party licenses before public distribution.

**Build success alone does not prove that a game boots correctly.** Real-device testing with a user-provided BIOS and game image is still required.
