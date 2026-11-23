# EmuCraft

Android-first, PS2-focused emulator application project.

## Target devices
- Android 8.0 (API 26) and newer
- ARM64-v8a
- Baseline test target: Snapdragon 720G-class devices
- Additional targets: Snapdragon 778G / 7-series and MediaTek Dimensity 7200-class or better

These are device targets, not a guarantee that every PS2 title will run at full speed.

## Current milestone: Android foundation + private file staging
- Native Android application shell
- ARM64 Android NDK / CMake integration
- JNI bridge loaded by the Android application
- Storage Access Framework game and BIOS selection
- Supported preliminary game extensions: ISO, CHD, CSO and BIN
- Supported preliminary BIOS extensions: BIN, ROM and BIOS
- Selected files are copied as streams into app-private storage (no full-file RAM buffering)
- SHA-256 digest is calculated during import
- Temporary files are finalized only after a successful, non-empty copy
- Private file paths and original SAF URI references are persisted across app restarts
- GitHub Actions debug APK workflow

**This is not yet a functioning PS2 emulator.** The current app can stage user-selected files and expose their private filesystem paths to future native integration. It does not parse disc images, validate BIOS contents, boot games, or emulate PS2 hardware.

## PS2 core evaluation

ARMSX2 is the leading integration candidate because its upstream repository contains a dedicated Android application and an ARM64 PCSX2-derived core. The upstream Android guide documents an Android Gradle build (:app:assembleGithubDebug), and its Android CMake entry point wires the shared PCSX2 core into an Android JNI library.

However, the upstream Android CMake entry point currently contains an explicit warning that its wiring has **not yet been compiled against a real Android NDK**. Its Android toolchain also differs materially from this app (upstream currently specifies Gradle 9.4.1, AGP 9.2.1, compile SDK 37, NDK 29 and CMake 3.31.6; this project uses Gradle 8.9, AGP 8.7.3, SDK 35, NDK 27.2.12479018 and CMake 3.22.1). Therefore, copying its native build files or changing tool versions blindly would be unsafe.

Evaluation snapshot:
- Upstream: https://github.com/ARMSX2/ARMSX2
- Branch inspected: master
- Commit inspected: a2914992c8c507d4c196464dbcf773fc7b0d0def
- License: GPL-3.0; distribution must preserve the license and satisfy corresponding-source obligations if this core is incorporated.
- Decision: candidate accepted for a controlled Android build experiment, not yet vendored or linked into EmuCraft.

Integration gate before shipping the core:
1. Pin and fetch a reviewed upstream commit, including all required submodules and third-party sources.
2. Build the upstream Android native target in a separate CI job with its documented toolchain.
3. Verify the resulting ARM64 libraries and 16 KB page-size compatibility.
4. Add a narrow JNI adapter and smoke-test core initialization/shutdown before wiring game boot.
5. Review GPL-3.0 and all bundled third-party licenses before distribution.

## Planned architecture
- Kotlin Android application and lifecycle
- C++ native layer via Android NDK
- PS2 core integration after Android-port feasibility, license and distribution review
- Vulkan renderer with capability-based OpenGL ES fallback
- Low-latency audio, controller input, memory cards and save states

## BIOS and game files
The project will not bundle copyrighted PS2 BIOS firmware or commercial game images. Users must provide files they are legally entitled to use. Extension checks are only preliminary selection checks; actual disc format and BIOS validation must be implemented by the emulation core.

Imported files live in the app's private storage under files/emucraft/imports. They are removed if the app's private data is cleared or the app is uninstalled. A future library-management feature should provide explicit removal and re-import controls.

## Build
Requirements: JDK 17, Android SDK platform 35, NDK 27.2.12479018, CMake 3.22.1 and Gradle 8.9.

    gradle assembleDebug

APK output: app/build/outputs/apk/debug/app-debug.apk.

## Licensing
Third-party emulator components and their licenses must be reviewed and documented before distribution.
