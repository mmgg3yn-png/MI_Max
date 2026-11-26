# Mi_Max Launcher extension packages

The current OpenLauncher build supports two safe, declarative package types. Neither type runs downloaded code inside the launcher.

## Me Island theme packs (.mt1)

A theme pack is a JSON manifest that changes the actual Me Island presentation: engine, layout geometry, animation, dimensions, blur, corner radius, colours and activity-card layout.

Example:

    {
      "format": "mimax-island-theme",
      "id": "oneplus_split",
      "name": "OnePlus Split",
      "style": "custom",
      "layout": "split",
      "animation": "spring",
      "background": 4010806080,
      "accent": 4293529600,
      "blur": 34,
      "cornerDp": 20,
      "widthDp": 224,
      "compactHeightDp": 40,
      "expandedHeightDp": 124,
      "animationMs": 360
    }

Supported engine IDs are ltin, his, coloros and custom. Supported layouts are pill, wide_card, split and fluid. Supported animations are spring, morph and fade_slide.

Import/export is available from Settings → Mi_Max Me Island. The local theme store includes built-in packs and can refresh the online catalogue at extensions/store/catalog.json. The catalogue lists HTTPS raw-content URLs and SHA-256 digests; the launcher checks the digest before installing or updating a theme. Updates are stored in app-private preferences and do not require a new launcher APK. The theme manager preserves a previous version for rollback.

## Declarative launcher extension archives (.zip)

A ZIP archive contains a root manifest.json and optional static assets. The manifest fields are:

- id: 3–80 characters using letters, numbers, underscore, dot or hyphen.
- name and version: display name and version.
- minApi: minimum Android API level.
- permissions: a list of declared capability names for host-side review.

The installer checks archive paths, limits archives to 128 entries and 4 MB uncompressed, checks the manifest and minimum API, and preserves the last-known-good package during replacement. Packages are data/assets only; they cannot run Java, native code or arbitrary scripts in the launcher process.

Open Settings → Mi_Max Extensions to import, inspect or roll back packages. The separate Mi_Max Recovery activity can clear broken visual packs or extension storage without opening the normal launcher workspace.

## Security and platform boundaries

Downloaded manifests are untrusted input and are parsed with strict size and field validation. SHA-256 detects catalogue/file mismatches; HTTPS protects transport. A theme pack can only select the documented visual properties. It cannot replace Android SystemUI, the lock screen, Recents, notification shade, or other applications.
