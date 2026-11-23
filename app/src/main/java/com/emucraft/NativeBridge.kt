package com.emucraft

/** JNI boundary reserved for the future Android-compatible PS2 core. */
object NativeBridge {
    init { System.loadLibrary("emucraft_native") }
    external fun engineStatus(): String
}
