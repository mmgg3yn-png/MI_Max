# Mi_Max Launcher extension contract

Extensions are separate Android APKs. They can be installed and updated independently of the launcher APK.

## Required activity contract

Declare one exported Activity with:

- Intent action: `com.mimax.lu.action.EXTENSION_TOOL`
- Category: `android.intent.category.DEFAULT`
- Activity metadata `com.mimax.lu.extension` set to `true`
- Optional activity metadata `com.mimax.lu.minLauncherVersion` (integer; current host contract version is 1)
- Optional activity metadata `com.mimax.lu.requiredPackages` (comma-separated Android package names that must be installed)

Example:

```xml
<activity
    android:name=".ExtensionToolActivity"
    android:exported="true">
    <intent-filter>
        <action android:name="com.mimax.lu.action.EXTENSION_TOOL" />
        <category android:name="android.intent.category.DEFAULT" />
    </intent-filter>
    <meta-data
        android:name="com.mimax.lu.extension"
        android:value="true" />
    <meta-data
        android:name="com.mimax.lu.minLauncherVersion"
        android:value="1" />
</activity>
```

## Expected behaviour

- Give the extension its own package name and version.
- Keep the tool UI inside the extension Activity.
- Request only Android permissions the tool truly needs. Android owns the permission prompt and the user can manage them in App info.
- Handle missing permissions and unsupported devices without crashing.
- The launcher discovers the extension through the activity intent filter, lets the user enable/disable it, and opens it on demand.
- Updating the extension means installing a newer APK with the same package name and signing key. The launcher APK does not need to be rebuilt.

## Current limits

This contract launches independent extension APK activities. It does not grant extensions permission to modify launcher internals, replace SystemUI, or execute arbitrary code inside the launcher process. The host checks the minimum launcher contract version and optional required package names. The current recovery action disables registered extensions; automatic package rollback and a remote extension marketplace are not implemented.
