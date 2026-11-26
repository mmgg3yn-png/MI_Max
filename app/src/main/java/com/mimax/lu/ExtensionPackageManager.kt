package com.mimax.lu

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager

/**
 * External APK extension contract.
 * An extension APK publishes an exported Activity with the action
 * com.mimax.lu.action.EXTENSION_TOOL and metadata com.mimax.lu.extension=true.
 */
class ExtensionPackageManager(private val context: Context) {
    companion object {
        const val ACTION_EXTENSION_TOOL = "com.mimax.lu.action.EXTENSION_TOOL"
        const val META_EXTENSION = "com.mimax.lu.extension"
        const val META_MIN_LAUNCHER_VERSION = "com.mimax.lu.minLauncherVersion"
        const val MIME_APK = "application/vnd.android.package-archive"
    }

    data class InstalledExtension(
        val packageName: String,
        val label: String,
        val versionName: String,
        val versionCode: Int,
        val minLauncherVersion: Int,
        val activity: ComponentName,
        val enabled: Boolean,
        val lastError: String?,
        val requestedPermissions: List<String>,
        val deniedPermissions: List<String>,
        val missingDependencies: List<String>
    )

    private val registry = ExtensionRegistry(context)
    private val packageManager = context.packageManager

    @Suppress("DEPRECATION")
    fun discover(): List<InstalledExtension> {
        val query = Intent(ACTION_EXTENSION_TOOL)
        val resolves = packageManager.queryIntentActivities(query, PackageManager.GET_META_DATA)
        return resolves.mapNotNull { resolve ->
            val activityInfo = resolve.activityInfo ?: return@mapNotNull null
            val meta = activityInfo.metaData ?: return@mapNotNull null
            if (!meta.getBoolean(META_EXTENSION, false)) return@mapNotNull null
            val packageInfo = runCatching {
                packageManager.getPackageInfo(activityInfo.packageName, PackageManager.GET_PERMISSIONS)
            }.getOrNull() ?: return@mapNotNull null
            val versionCode = packageInfo.longVersionCode.coerceAtMost(Int.MAX_VALUE.toLong()).toInt()
            val minVersion = meta.getInt(META_MIN_LAUNCHER_VERSION, 1)
            val requiredPackages = meta.getString("com.mimax.lu.requiredPackages").orEmpty()
                .split(",").map { it.trim() }.filter { it.isNotBlank() }
            val missingDependencies = requiredPackages.filter { required ->
                runCatching { packageManager.getPackageInfo(required, 0) }.isFailure
            }
            val label = resolve.loadLabel(packageManager).toString()
            val previous = registry.all().firstOrNull { it.id == activityInfo.packageName }
            val entry = ExtensionRegistry.Extension(
                id = activityInfo.packageName,
                name = label,
                version = versionCode,
                minLauncherVersion = minVersion,
                enabled = previous?.enabled ?: true,
                lastError = previous?.lastError
            )
            if (previous == null || previous.version != versionCode) registry.register(entry)
            val requested = packageInfo.requestedPermissions?.toList().orEmpty()
            val denied = requested.filter { packageManager.checkPermission(it, activityInfo.packageName) != PackageManager.PERMISSION_GRANTED }
            InstalledExtension(
                packageName = activityInfo.packageName,
                label = label,
                versionName = packageInfo.versionName ?: versionCode.toString(),
                versionCode = versionCode,
                minLauncherVersion = minVersion,
                activity = ComponentName(activityInfo.packageName, activityInfo.name),
                enabled = entry.enabled && minVersion <= 1 && missingDependencies.isEmpty(),
                lastError = entry.lastError,
                requestedPermissions = requested,
                deniedPermissions = denied,
                missingDependencies = missingDependencies
            )
        }.distinctBy { it.packageName }
    }

    fun setEnabled(packageName: String, enabled: Boolean) {
        registry.setEnabled(packageName, enabled)
    }

    fun disableAll() {
        registry.all().forEach { registry.setEnabled(it.id, false) }
    }

    fun launch(extension: InstalledExtension): Result<Unit> = runCatching {
        require(extension.enabled) { "Extension is disabled or incompatible" }
        val intent = Intent(ACTION_EXTENSION_TOOL).setComponent(extension.activity)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
    }.onFailure {
        registry.recordFailure(extension.packageName, it.message ?: it.javaClass.simpleName)
    }

    fun errorLog(packageName: String): List<String> = registry.errorLog(packageName)

    fun registryEntries() = registry.all()
}
