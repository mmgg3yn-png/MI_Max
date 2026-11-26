# Mi_Max Launcher

Native Android launcher project.

- Application: Mi_Max Launcher
- Package: `com.mimax.lu`
- Minimum Android: 13 (API 33)
- Architectures: ARMv7 (32-bit) and ARM64
- Android UI and platform integration: Kotlin + Jetpack Compose
- Native performance module: Rust (JNI-ready)
- Build: GitHub Actions

## Project status

This repository starts the real Android launcher foundation. It includes a launcher activity, installed-app discovery/launching, a native settings screen, an About/Developer page, configurable AI connection settings, and a Rust native module built for both Android ABIs.

Advanced Xiaomi-inspired features (widget stacks, folder stacks, theme marketplace, icon packs, gesture engine, animation presets, and theme import/export) are planned as separate working modules. Android restrictions are respected: a third-party launcher cannot replace privileged SystemUI/Recents internals or silently control other apps.

## Build

GitHub Actions builds a debug APK on pushes to `main`. Download the `Mi_Max_Launcher-debug` artifact from the workflow run.

## License and upstream components

Do not copy proprietary Xiaomi system apps, resources, or signing assets. Any reused upstream code must retain its license and notices. The project can implement compatible original functionality without redistributing proprietary components.
