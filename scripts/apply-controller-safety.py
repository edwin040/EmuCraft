#!/usr/bin/env python3
"""Prevent controller BACK aliases from exiting Android/EmuCraft during gameplay."""
from pathlib import Path

runtime = Path(
    "upstream/ARMSX2/platforms/android/app/src/main/java/com/armsx2/runtime/MainActivityRuntime.kt"
)
if not runtime.is_file():
    raise SystemExit(f"Expected upstream runtime source not found: {runtime}")

text = runtime.read_text()

old_back = """        if (kc == KeyEvent.KEYCODE_BACK) {
            // If the user bound BACK to a hotkey (e.g. Menu), that binding WINS — do
"""
new_back = """        val isPhysicalControllerKey = event.isFromSource(InputDevice.SOURCE_GAMEPAD) ||
            event.isFromSource(InputDevice.SOURCE_JOYSTICK)
        if (kc == KeyEvent.KEYCODE_BACK && !isPhysicalControllerKey) {
            // Physical controller BACK aliases must never invoke Android-style exit.
            // They continue to the gameplay mapping path below; if unmapped, they are
            // consumed at the final gameplay boundary rather than escaping to Android.
            // If the user bound BACK to a hotkey (e.g. Menu), that binding WINS — do
"""
if text.count(old_back) != 1:
    raise SystemExit(f"Expected one BACK hold block, found {text.count(old_back)}")
text = text.replace(old_back, new_back, 1)

old_tail = """        if (dispatchGameplayKey(event)) return true
        return super.dispatchKeyEvent(event)
"""
new_tail = """        if (dispatchGameplayKey(event)) return true
        // Some USB pads expose a face button as Android KEYCODE_BACK. Never let that
        // physical gamepad event fall through to Activity/system navigation while a
        // PS2 game is running. Properly mapped keys were already forwarded above.
        if (kc == KeyEvent.KEYCODE_BACK && isPhysicalControllerKey &&
            eState.value == EmuState.RUNNING
        ) {
            return true
        }
        return super.dispatchKeyEvent(event)
"""
if text.count(old_tail) != 1:
    raise SystemExit(f"Expected one dispatch tail, found {text.count(old_tail)}")
text = text.replace(old_tail, new_tail, 1)

runtime.write_text(text)
print("Controller safety patch applied.")
