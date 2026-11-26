package com.mimax.lu

object NativeBridge {
    private val loaded: Boolean = try {
        System.loadLibrary("mimax_engine")
        true
    } catch (_: UnsatisfiedLinkError) {
        false
    }

    fun engineVersion(): String =
        if (loaded) nativeEngineVersion() else "Rust engine not packaged in this local build"

    @JvmStatic private external fun nativeEngineVersion(): String
}
