# Mi_Max Launcher — Complete Acceptance Specification

The product base is the pinned Apache-2.0 OpenLauncher source. Preserve upstream notices and attribution. This checklist is the acceptance contract: no feature is complete from a mockup, placeholder, inactive switch, or documentation alone.

## A. OpenLauncher foundation and compatibility
- [x] Select and pin the real OpenLauncher upstream source.
- [ ] Retain and regression-test upstream paged desktop, dock, drag/drop, folders/groups, app drawer, app search, app hiding, icon packs, widget hosting, settings and backup.
- [ ] Rebrand all user-facing names and developer information to Mi_Max Launcher / محمد السعيد علي / mmgg3yn@gmail.com / @Mi_Max12.
- [ ] Build one APK containing ARMv7 (armeabi-v7a) and ARM64 (arm64-v8a).
- [ ] Support non-Xiaomi Android devices, including Android 14 Go and low-memory ARM32 devices; measure memory and startup cost.
- [ ] Verify install, HOME role, upgrade, data migration and uninstall behavior.

## B. Home screen and app drawer
- [ ] Multiple editable home pages, page hide/show/reorder, per-page wallpaper, live page preview and page transitions.
- [ ] Real drag-and-drop placement, grid dimensions, icon size/spacing, desktop layout lock, dock rows/columns and customization.
- [ ] Standard folders, large folders, nested folders, folder styles, folder sorting and app stacks.
- [ ] App drawer categories, sorting, search, recent/frequent apps, shortcuts and configurable layout.
- [ ] Super/large icons and adaptive icon shape/size controls.
- [ ] Long-press app menus and per-app actions.
- [ ] Home-only label hiding, drawer label controls, folder label hiding, per-app label hiding, label size/color and custom launcher display names without renaming Android packages.
- [ ] iOS-like App Library, hidden pages, icon tinting, optional glass effects and Smart Stack.
- [ ] ColorOS-like large folders, icon/text sizing, drawer settings and transitions.
- [ ] Desktop/tablet/foldable responsive layouts and optional desktop mode.

## C. Widgets
- [ ] Real Android AppWidgetHost lifecycle: provider discovery, bind permission, configuration activity, add/remove, resize, move, persist and restore.
- [ ] Multiple widget pages, widget stacks, Smart Stack rotation and user-controlled stack order.
- [ ] Widget appearance controls where the provider/API permits them.
- [ ] Built-in clock/date, weather, battery, calendar, media, photos, notes and shortcuts widgets only where they have real data providers and working refresh behavior.
- [ ] Custom widget SDK and safe widget packaging; no fake sample data presented as live data.

## D. Theme center and personalization
- [ ] Theme import/export/install/uninstall and validated theme manifest.
- [ ] Icon packs, per-app icon overrides, icon shape, icon tint, icon size, fonts, wallpapers and per-page wallpapers.
- [ ] Theme editor with preview, rollback and persistent settings.
- [ ] Liquid Glass appearance, translucency, blur, reflections, edge lighting and graceful low-performance fallback.
- [ ] Local palette and scheduled theme switching.
- [ ] Theme store/catalog with version, compatibility, dependencies, update and uninstall support.

## E. Gestures, search and system integration
- [ ] Configurable swipe-up drawer, swipe-down search, double-tap lock (only when Android grants a valid mechanism), two-finger gestures, pinch/unpinch and custom gesture-to-action mapping.
- [ ] Haptic feedback and home action mapping.
- [ ] Spotlight-style search across apps, shortcuts, launcher settings, recent/frequent items and optional contacts (permission-gated).
- [ ] Notification dots/badges only through supported Android APIs and explicit user access.
- [ ] Accessibility mode, keyboard navigation and reduced-motion support.

## F. Me Island — independent live activity overlay
- [ ] Separate foreground overlay service that can remain visible over other apps after the user grants Display over other apps.
- [ ] Correct positioning around display cutout/camera; configurable dimensions, corner geometry, spacing and safe-area behavior.
- [ ] Compact/expanded interactions, tap/long-press, swipe collapse/expand, horizontal activity switching and detail view.
- [ ] Activity queue, priority, multiple concurrent activities, stable updates without flicker and automatic completion/expiry.
- [ ] Real timer/stopwatch, media session, call state where Android exposes it, charging/battery, downloads when observable, and supported recording/navigation integrations.
- [ ] Notification listener integration only after explicit Notification Access; private-content mode and user-controlled categories.
- [ ] Three genuinely different visual/interaction engines: LTIN (iPhone-inspired), HIS (HyperOS-inspired), ColorOS (Oppo-inspired); each changes layout geometry, behavior and animations, not merely color.
- [ ] Glass/blur, morph/spring transitions, reflections and performance fallback.
- [ ] Theme editor with live preview, reset, position/dimensions, animation speed and per-activity controls.
- [ ] .mt1 import/export with validated declarative assets/layout/animation manifests; no arbitrary executable code.
- [ ] OnePlus-style Me Island extension sample that actually changes geometry, layout, activity cards and interaction.
- [ ] Overlay/service recovery, permission explanations, battery-optimization guidance and safe shutdown.

## G. Extension platform and developer tools
- [ ] Install/remove extensions independently of base APK updates.
- [ ] In-app extension catalog/store, extension updates, versioning, rollback and compatibility checks.
- [ ] Signed extension packages, integrity checks, explicit per-extension permissions, dependency resolution and API versioning.
- [ ] Restricted declarative extension API; do not load untrusted native code or arbitrary executable scripts into the launcher process.
- [ ] Automatic disable on repeated failure, last-known-good recovery, per-extension logs and crash isolation.
- [ ] Separate maintenance/recovery mode able to disable/remove broken extensions without loading the normal launcher UI.
- [ ] Developer tools/templates, validation, preview, packaging and diagnostic logs.
- [ ] Extensions can replace approved visual engines/components/animations, not only recolor them.

## H. Privacy, profiles and productivity
- [ ] Hide apps, exclude them from search, protect hidden-app settings and use supported app-lock mechanisms without claiming privileged security.
- [ ] Guest/child profiles, Focus mode, multiple local profiles and per-profile layouts.
- [ ] Hide notification content in launcher surfaces; permission-gated contact access.
- [ ] Backup protection, local device sync where supported and scheduled theme/profile changes.
- [ ] Mi_Max AI assistant integration with real provider/model selection, request streaming, error handling, secure key storage and explicit network controls.

## I. Backup, recovery, diagnostics and quality
- [ ] Backup/restore pages, app placements, folders, dock, widget IDs/configuration, themes, icon overrides, gestures and settings.
- [ ] Versioned backup format, validation, migration, partial restore and rollback on corrupt data.
- [ ] Progressive icon loading, bounded caches, memory optimization, performance/quality mode, blur/animation disable controls.
- [ ] Diagnostics, crash logs, corrupted-settings recovery, extension-specific logs and exportable support report.
- [ ] Unit/instrumentation tests for storage, layout, extension manifests, permissions and recovery.
- [ ] Build verification, APK ABI verification, install smoke tests and device testing on ARM32 and ARM64.

## J. Platform and security constraints
- A normal third-party launcher cannot replace privileged SystemUI, Android Recents, the system lock screen, notification shade, or force changes inside other apps.
- Overlay visibility requires explicit user permission; Android/OEM background limits can affect persistent live activities.
- Contacts, notification access, widgets, media sessions and call state must use supported APIs and explicit permissions.
- Extension packages are untrusted input. Theme/extension manifests must be validated and must not execute arbitrary code.
- Never claim a feature is implemented until its behavior exists and tests or device checks confirm it.
