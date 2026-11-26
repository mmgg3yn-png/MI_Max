# Mi_Max Launcher — Feature Acceptance Checklist

This file preserves the complete requested scope. A feature is marked implemented only when its real Android behavior exists; a visual placeholder is not counted as implementation.

## Current alpha implementation
- [x] Native Android launcher project, package `com.mimax.lu`, Android 13+.
- [x] Debug build targets ARM32 (`armeabi-v7a`) and ARM64 (`arm64-v8a`).
- [x] Launcher HOME intent and app launch intent.
- [x] Installed-app listing, app drawer screen, and name search.
- [x] Home screen with a basic app grid, multi-page horizontal navigation, and folder creation from long-press selection.
- [x] Independent hide-label controls for Home and App Library.
- [x] Persistent hide/unhide installed apps from Home and App Library.
- [x] Persistent settings for theme selection, grid columns, glass opacity, and blur preference value.
- [x] Built-in visual theme presets.
- [x] Developer/About screen and local account placeholder.
- [x] Mi_Max AI endpoint/model/key settings fields (configuration UI only).
- [x] Rust native library build step and Kotlin JNI bridge; JNI symbol has been aligned.
- [x] GitHub Actions workflow for Android debug APK + Rust ABI builds.

## Requested features — still to implement
- [ ] Real draggable home-screen icons, pages, dock, folders, folder stacks, and app stacks.
- [ ] Real Android widgets through AppWidgetHost: add, configure, resize, reorder, stack, and persist widgets.
- [ ] Full theme engine: install/import/export themes, icon packs, fonts, wallpapers, per-element styling, and theme editor.
- [ ] Theme and extension store with package metadata, compatibility checks, updates, and uninstall.
- [ ] Extension SDK/API, local extension installation, per-extension permissions, dependency checks, logs, crash isolation, automatic disable, and last-known-good recovery.
- [ ] Safe maintenance/recovery screen that can disable or remove a broken extension without loading the normal launcher UI.
- [ ] Gesture editor, transition/launch animations, icon shapes/sizes, adaptive layouts, and accessibility options.
- [ ] Hide apps, app categories, app shortcuts, notification dots where Android grants access, and advanced search.
- [ ] Backup/restore of launcher layout, settings, theme, folders, and widget configuration.
- [ ] Real Mi_Max AI integration with request handling, streaming, error handling, and model selection; fields alone do not count.
- [x] Me Island foreground overlay foundation with timer, tap expansion, swipe expansion/collapse, cutout-aware top positioning, animated appearance/disappearance, and device-supported blur.
- [x] Three selectable Me Island visual presets: LTIN, HIS, and ColorOS; visual geometry and animation parameters differ by preset.
- [x] Declarative `.mt1` theme import from a ZIP containing `manifest.json` or a compatible JSON manifest; code execution is not allowed in theme packs.
- [ ] Me Island media sessions, calls, downloads, notification listener integration, simultaneous activity carousel, and OnePlus extension.
- [ ] Recent-apps-like launcher page (not replacement of privileged Android Recents).
- [ ] Localization, RTL polish, tablet/foldable layouts, performance and memory testing.
- [ ] Release signing, versioning, tests, and verified APK artifact.

## Platform limits
A normal third-party launcher cannot replace privileged SystemUI, the system lock screen, notification shade, or Android's system Recents implementation. It cannot force animations inside other apps. Background blur depends on Android version and device support; translucent fallback must remain available. Widget hosting requires Android's widget binding/configuration flow and user approval.

## Build verification
Do not mark a build successful until GitHub Actions reports a successful run and the APK artifact is present and downloadable.
