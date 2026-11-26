from pathlib import Path

gradle = Path("app/build.gradle")
source = gradle.read_text()
replacements = [
    ('applicationId "com.benny.openlauncher"', 'applicationId "com.mimax.launcher"'),
    ('resValue \'string\', \'app_name\', "OpenLauncher"', 'resValue \'string\', \'app_name\', "Mi_Max Launcher"'),
    ('resValue "string", "manifest_package_id", "com.benny.openlauncher"', 'resValue "string", "manifest_package_id", "com.mimax.launcher"'),
    ('versionCode 37', 'versionCode 38'),
    ('versionName "0.6.1"', 'versionName "1.0.0-mimax.1"'),
]
for old, new in replacements:
    if old not in source:
        raise SystemExit(f"Expected Gradle marker not found: {old}")
    source = source.replace(old, new, 1)

marker = "        multiDexEnabled false"
if marker not in source:
    raise SystemExit("Could not locate defaultConfig ABI insertion point")
source = source.replace(
    marker,
    marker + '\n\n        // Single APK; compatible with ARMv7 and ARM64 devices.\n'
             + '        ndk { abiFilters "armeabi-v7a", "arm64-v8a" }',
    1,
)
gradle.write_text(source)

settings = Path("settings.gradle")
settings.write_text(settings.read_text().replace(
    'rootProject.name = "OpenLauncher"',
    'rootProject.name = "Mi_Max Launcher"',
))

strings = Path("app/src/main/res/values/strings.xml")
source = strings.read_text()
if 'name="mimax_developer_title"' not in source:
    source = source.replace(
        "</resources>",
        '    <string name="mimax_developer_title">Mi_Max Developer</string>\n'
        '    <string name="mimax_developer_summary">محمد السعيد علي&#10;Porting, adaptation and maintenance for ARM32 and ARM64 devices outside Xiaomi.&#10;mmgg3yn@gmail.com | Telegram: @Mi_Max12</string>\n'
        "</resources>",
        1,
    )
strings.write_text(source)

about = Path("app/src/main/res/xml/preferences_about.xml")
source = about.read_text()
marker = (
    '    </PreferenceCategory>\n\n'
    '    <PreferenceCategory\n'
    '        android:key="@string/pref_key__more_info__project_community"'
)
if 'mimax_developer_title' not in source:
    if marker not in source:
        raise SystemExit("Could not find project team category insertion point")
    source = source.replace(
        marker,
        '        <Preference\n'
        '            android:icon="@drawable/ic_info_black_24dp"\n'
        '            android:title="@string/mimax_developer_title"\n'
        '            android:summary="@string/mimax_developer_summary" />\n\n'
        + marker,
        1,
    )
about.write_text(source)


# The upstream About screen loads these documents through R.raw.*.
# Copy them explicitly because the upstream copy task is not wired into this Gradle version.
import shutil
raw_dir = Path("app/src/main/res/raw")
raw_dir.mkdir(parents=True, exist_ok=True)
for source_name, target_name in [
    ("LICENSE", "license.md"),
    ("CONTRIBUTORS.md", "contributors.md"),
    ("CHANGELOG.md", "changelog.md"),
]:
    source_file = Path(source_name)
    if not source_file.exists():
        raise SystemExit(f"Required upstream attribution/document file missing: {source_name}")
    shutil.copyfile(source_file, raw_dir / target_name)


# Android 12+ requires an explicit PendingIntent mutability flag.
context_utils = Path("app/src/main/java/net/gsantner/opoc/util/ContextUtils.java")
source = context_utils.read_text()
old = "PendingIntent.FLAG_CANCEL_CURRENT);"
new = "PendingIntent.FLAG_CANCEL_CURRENT | PendingIntent.FLAG_IMMUTABLE);"
if old not in source:
    raise SystemExit("Could not locate restart PendingIntent to make it Android 12+ safe")
context_utils.write_text(source.replace(old, new, 1))


# Sign the first test build with Android's local debug certificate so it can be installed.
app_gradle = Path("app/build.gradle")
source = app_gradle.read_text()
release_marker = "        release {\n            minifyEnabled false"
release_replacement = "        release {\n            signingConfig signingConfigs.debug\n            minifyEnabled false"
if release_marker not in source:
    raise SystemExit("Could not find release build type for test signing")
app_gradle.write_text(source.replace(release_marker, release_replacement, 1))

print("Mi_Max branding, developer credit, About resources, Android 12+ fix and installable test signing applied.")
