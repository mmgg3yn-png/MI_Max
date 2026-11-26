# Mi_Max Launcher

Mi_Max Launcher is being rebuilt on the real **OpenLauncher** Android codebase, not as a separate launcher imitation.

## Upstream foundation

- Upstream: https://github.com/linsmod/openlauncher-2026
- Pinned upstream commit: `683e11199c67024132287757a55665f56fc6fff6`
- License: Apache-2.0 (upstream notices and attribution must remain)
- Existing native launcher features retained: paged desktop, dock, drag-and-drop, app hiding, search, icon packs, Android widgets, launcher settings and backup support.
- Mi_Max identity: developer محمد السعيد علي — mmgg3yn@gmail.com — Telegram @Mi_Max12.

## Build policy

The build workflow now checks out the pinned upstream source and applies Mi_Max integration patches to that source. It is manual-only while feature integration is in progress, so an incomplete upstream-only APK is not presented as the finished Mi_Max product.

A release candidate may be built only after the acceptance checklist in `FEATURES.md` is implemented, compiled, and verified. The universal package must include both `armeabi-v7a` and `arm64-v8a`.

## Product scope

The complete requested specification is tracked in `FEATURES.md`. A feature is not complete merely because a settings switch or visual mockup exists: it must have a working Android implementation, persistence, permission handling, error recovery where relevant, and build/device validation.

## Android platform limits

A normal third-party launcher cannot replace privileged SystemUI, Android Recents, the lock screen, or force changes inside other apps. Overlay-based Me Island functions require explicit user permission and are subject to Android background-service restrictions. Features that depend on APIs or permissions will be clearly disclosed and must fail safely when unavailable.
