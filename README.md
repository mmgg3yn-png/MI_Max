# Mi_Max Launcher

Native Android launcher project built with Kotlin, Jetpack Compose and a small Rust JNI module.

- Application: Mi_Max Launcher
- Package: `com.mimax.lu`
- Minimum Android: 13 (API 33)
- Architectures: ARMv7 (32-bit) and ARM64
- UI: Kotlin + Jetpack Compose
- Native module: Rust (JNI)
- Build: GitHub Actions

## Existing implemented modules

- Home screen and app drawer with installed-app discovery and app launching.
- Home pages, folders, gesture bindings and configurable grid.
- Wallpaper, font, icon shape and compatible icon-pack selection.
- Android AppWidget host/controller and widget picker.
- Theme pack import/export foundation and local theme presets.
- Launcher backup and restore.
- External APK extension discovery, permissions visibility, dependency checks, failure logs and a separate recovery screen.
- Mi_Max AI connection settings and optional AI chat UI.
- Developer/about screen.

## Me Island

A first working Me Island timer-overlay foundation has been added:
- Separate foreground service, independent of the launcher Activity.
- Android overlay permission flow.
- Live countdown capsule above other apps.
- Compact/expanded tap interaction.
- Animated appearance/disappearance and blur-behind where supported.
- Timer activity can continue while another app is in the foreground.

This is an initial timer implementation, not the completed feature set. Media sessions, calls, downloads, notification listener integration, multiple simultaneous activities, the LTIN/HIS/ColorOS visual engines, OnePlus extension, and the full `.mt1` theme package format still require implementation and device testing.

## Remaining full-product work

The complete product specification includes advanced folder/icon layouts, per-app label hiding, real widget stacks and custom widgets, theme studio, dynamic island visual engines and extension API, secure extension signing/sandboxing, extension marketplace/update delivery, profile/focus/child modes, Spotlight search, performance diagnostics, and robust backup/recovery. These must be implemented and tested as functional modules; the current repository must not be described as having them until they exist.

## Android limitations

Me Island needs the user's explicit **Display over other apps** permission to remain visible above other applications. Android may restrict foreground services or overlays according to device policy and battery management. Some system-only features (privileged Recents/SystemUI control and silent lock-screen control) cannot be provided by a normal third-party launcher.

## Build

GitHub Actions workflow: `.github/workflows/android.yml`.
Download the APK from the workflow's `Mi_Max_Launcher-debug` artifact after a successful run.

## License and upstream components

Do not copy proprietary Xiaomi, Apple, OPPO or OnePlus code, assets, signing keys or private system resources. Implement compatible original behavior and retain all applicable upstream license notices.
