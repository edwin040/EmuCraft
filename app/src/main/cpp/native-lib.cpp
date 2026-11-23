#include <jni.h>
#include <string>

extern "C" JNIEXPORT jstring JNICALL
Java_com_emucraft_NativeBridge_engineStatus(JNIEnv* env, jobject) {
    const std::string status =
        "Native ARM64 layer is built. No PS2 emulation core is linked yet.";
    return env->NewStringUTF(status.c_str());
}
