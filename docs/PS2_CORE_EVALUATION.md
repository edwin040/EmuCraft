# PS2 Core Evaluation

Status: evaluation only. No third-party emulator core is vendored or linked yet.

## Candidate A: ARMSX2

Repository: https://github.com/ARMSX2/ARMSX2

Why it is the leading candidate:
- It is a PCSX2-derived PS2 emulator explicitly targeting ARM64 mobile and Android.
- Its upstream project documents native ARM64 JIT/recompiler work for EE, IOP and VU, plus Adreno and Mali renderer work.
- It is closer to the performance goal than trying to compile the desktop PCSX2 build unchanged.

Constraints:
- The repository is GPL-3.0. A distributed derivative that incorporates it must comply with GPL-3.0, including corresponding source-code and license obligations.
- BIOS must be supplied by the user from a console they are entitled to use; EmuCraft must not bundle proprietary BIOS firmware.
- We must pin a reviewed upstream commit, audit its Android build instructions and dependencies, then verify that the core can be embedded behind EmuCraft's Kotlin/JNI boundary.
- Renderer, file-system access, controller mapping, save states and lifecycle integration must be validated on real Android devices.

## Candidate B: Play!

Repository: https://github.com/jpd002/Play-

Why it remains a fallback:
- The official project supports Android and has a C++ codebase.
- It uses a built-in high-level emulation BIOS, so it does not require an external PS2 BIOS file.
- Its BSD-style license permits redistribution subject to retaining notices and disclaimer.

Trade-off:
- Its high-level emulation approach and current game compatibility/performance must be benchmarked against the target game set before selection.

## Why not link desktop PCSX2 directly?

The official PCSX2 system requirements list x86-64 CPU requirements. EmuCraft targets ARM64 Android phones, so a direct desktop build is not the correct integration route. An Android/ARM64-oriented port or fork is required.

## Decision gate before integration

1. Pin candidate source to a specific commit.
2. Read all top-level and bundled third-party licenses.
3. Build the candidate's Android ARM64 target in CI.
4. Produce a minimal JNI smoke test that initializes and shuts down the core.
5. Load a legally obtained test disc image and user-provided BIOS where required.
6. Measure frame pacing, CPU/GPU load, memory and thermal behavior on Snapdragon 720G-class and Dimensity 7200-class devices.
7. Only then select and vendor the core into EmuCraft.

No compatibility or performance guarantee is made until device and per-game tests are complete.
