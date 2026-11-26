package com.mimax.lu

import android.content.Context
import android.net.Uri
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

/** Exports a minimal Android Studio project that implements the Mi_Max extension APK contract. */
class ExtensionTemplateExporter(private val context: Context) {
    private val files = linkedMapOf(
        "MiMaxExtension/settings.gradle.kts" to """
            pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
            dependencyResolutionManagement { repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS); repositories { google(); mavenCentral() } }
            rootProject.name = "MiMaxExtension"
            include(":app")
        """.trimIndent(),
        "MiMaxExtension/build.gradle.kts" to """
            plugins {
                id("com.android.application") version "8.7.3" apply false
                id("org.jetbrains.kotlin.android") version "2.0.21" apply false
            }
        """.trimIndent(),
        "MiMaxExtension/app/build.gradle.kts" to """
            plugins {
                id("com.android.application")
                id("org.jetbrains.kotlin.android")
            }
            android {
                namespace = "com.example.mimaxextension"
                compileSdk = 35
                defaultConfig {
                    applicationId = "com.example.mimaxextension"
                    minSdk = 33
                    targetSdk = 35
                    versionCode = 1
                    versionName = "1.0"
                }
            }
        """.trimIndent(),
        "MiMaxExtension/app/src/main/AndroidManifest.xml" to """
            <manifest xmlns:android="http://schemas.android.com/apk/res/android">
                <application android:label="Mi_Max Sample Extension" android:theme="@android:style/Theme.Material.Light.NoActionBar">
                    <activity android:name=".ExtensionToolActivity" android:exported="true">
                        <intent-filter>
                            <action android:name="com.mimax.lu.action.EXTENSION_TOOL" />
                            <category android:name="android.intent.category.DEFAULT" />
                        </intent-filter>
                        <meta-data android:name="com.mimax.lu.extension" android:value="true" />
                        <meta-data android:name="com.mimax.lu.minLauncherVersion" android:value="1" />
                    </activity>
                </application>
            </manifest>
        """.trimIndent(),
        "MiMaxExtension/app/src/main/java/com/example/mimaxextension/ExtensionToolActivity.kt" to """
            package com.example.mimaxextension

            import android.app.Activity
            import android.os.Bundle
            import android.widget.TextView

            class ExtensionToolActivity : Activity() {
                override fun onCreate(savedInstanceState: Bundle?) {
                    super.onCreate(savedInstanceState)
                    setContentView(TextView(this).apply {
                        text = "My Mi_Max extension tool"
                        textSize = 22f
                        setPadding(32, 48, 32, 32)
                    })
                }
            }
        """.trimIndent(),
        "MiMaxExtension/README.md" to """
            # Mi_Max extension starter

            Open this folder in Android Studio and build the app APK.

            The exported ExtensionToolActivity implements the contract:
            action com.mimax.lu.action.EXTENSION_TOOL
            metadata com.mimax.lu.extension=true
            metadata com.mimax.lu.minLauncherVersion=1

            Give the extension a unique applicationId and signing key before distribution.
            Request only permissions the extension genuinely needs.
            Install the resulting APK on the same device as Mi_Max Launcher, then refresh Extension Manager.
        """.trimIndent()
    )

    fun export(uri: Uri): Result<Unit> = runCatching {
        val output = context.contentResolver.openOutputStream(uri) ?: error("Cannot open ZIP destination")
        ZipOutputStream(output.buffered()).use { zip ->
            files.forEach { (path, source) ->
                zip.putNextEntry(ZipEntry(path))
                zip.write(source.toByteArray(Charsets.UTF_8))
                zip.closeEntry()
            }
        }
    }
}
