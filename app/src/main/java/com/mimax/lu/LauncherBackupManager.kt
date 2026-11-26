package com.mimax.lu

import android.content.Context
import android.net.Uri
import org.json.JSONObject

/** Export/restore user-facing launcher settings through Android's document picker URI. */
class LauncherBackupManager(private val context: Context) {
    private val prefs get() = context.getSharedPreferences("mimax_launcher", Context.MODE_PRIVATE)
    private val layoutPrefs get() = context.getSharedPreferences("launcher_layout_v1", Context.MODE_PRIVATE)
    private val extraPreferenceFiles = listOf("gesture_settings_v1", "extension_registry_v1", "theme_packs_v1", "widget_host_v1")

    fun exportTo(uri: Uri): Result<Unit> = runCatching {
        val root = JSONObject()
            .put("format", "mimax-launcher-backup")
            .put("version", 1)
            .put("settings", prefs.all.toJson())
            .put("layout", layoutPrefs.all.toJson())
            .put("extraPreferences", JSONObject().apply {
                extraPreferenceFiles.forEach { name ->
                    put(name, context.getSharedPreferences(name, Context.MODE_PRIVATE).all.toJson())
                }
            })
        context.contentResolver.openOutputStream(uri)?.bufferedWriter(Charsets.UTF_8)?.use {
            it.write(root.toString(2))
        } ?: error("Unable to open backup destination")
    }

    fun restoreFrom(uri: Uri): Result<Unit> = runCatching {
        val raw = context.contentResolver.openInputStream(uri)?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }
            ?: error("Unable to open backup file")
        val root = JSONObject(raw)
        require(root.optString("format") == "mimax-launcher-backup") { "Unsupported backup format" }
        require(root.optInt("version") == 1) { "Unsupported backup version" }
        restorePrefs(prefs, root.getJSONObject("settings"))
        restorePrefs(layoutPrefs, root.getJSONObject("layout"))
        root.optJSONObject("extraPreferences")?.let { extra ->
            extraPreferenceFiles.forEach { name ->
                extra.optJSONObject(name)?.let { values ->
                    restorePrefs(context.getSharedPreferences(name, Context.MODE_PRIVATE), values)
                }
            }
        }
    }

    private fun Map<String, *>.toJson(): JSONObject {
        val result = JSONObject()
        forEach { (key, value) ->
            when (value) {
                is String, is Boolean, is Int, is Long, is Float -> result.put(key, value)
                is Set<*> -> result.put(key, value.filterIsInstance<String>().toTypedArray())
            }
        }
        return result
    }

    private fun restorePrefs(target: android.content.SharedPreferences, values: JSONObject) {
        val edit = target.edit().clear()
        values.keys().forEach { key ->
            when (val value = values.get(key)) {
                is String -> edit.putString(key, value)
                is Boolean -> edit.putBoolean(key, value)
                is Int -> edit.putInt(key, value)
                is Long -> edit.putLong(key, value)
                is Double -> edit.putFloat(key, value.toFloat())
                is org.json.JSONArray -> edit.putStringSet(key,
                    (0 until value.length()).map { value.getString(it) }.toSet())
            }
        }
        edit.apply()
    }
}
