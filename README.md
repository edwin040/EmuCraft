# EmuCraft

Android-first, PS2-focused emulator application project.

## Target devices
- Android 8.0 (API 26) and newer
- ARM64-v8a
- Baseline test target: Snapdragon 720G-class devices
- Additional targets: Snapdragon 778G / 7-series and MediaTek Dimensity 7200-class or better

These are device targets, not a guarantee that every PS2 title will run at full speed.

## Current milestone: Android foundation
- Native Android application shell
- ARM64 Android NDK / CMake integration
- Storage Access Framework game-file picker
- GitHub Actions debug APK workflow

**This is an application scaffold, not a functioning PS2 emulator.** No PS2 emulation core is integrated yet. Selecting an ISO does not start a game.

## Planned architecture
- Kotlin Android application and lifecycle
- C++20 native layer via Android NDK
- PS2 core integration after Android-port feasibility, license and distribution review
- Vulkan renderer with capability-based OpenGL ES fallback
- Low-latency audio, controller input, memory cards and save states

## BIOS and game files
The project will not bundle copyrighted PS2 BIOS firmware or commercial game images. Users must provide files they are legally entitled to use. BIOS configuration will be implemented in a later milestone.

## Build
Requirements: JDK 17, Android SDK platform 35, NDK 27.2.12479018, CMake 3.22.1 and Gradle 8.9.

```bash
gradle assembleDebug
```

APK output: `app/build/outputs/apk/debug/app-debug.apk`.

## Licensing
Third-party emulator components and their licenses must be reviewed and documented before distribution.
