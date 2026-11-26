package com.mimax.lu

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/**
 * Metadata registry for installable launcher extensions.
 * This deliberately does not execute downloaded code: extensions require a signed,
 * permission-scoped runtime/API before activation can be considered safe.
 */
class ExtensionRegistry(context: Context) {
    data class Extension(
        val id: String,
        val name: String,
        val version: Int,
        val minLauncherVersion: Int,
        val enabled: Boolean,
        val lastError: String?
    )

    private val prefs = context.getSharedPreferences("extension_registry_v1", Context.MODE_PRIVATE)

    fun all(): List<Extension> = runCatching {
        val a = JSONArray(prefs.getString("items", "[]"))
        (0 until a.length()).map { i ->
            val o = a.getJSONObject(i)
            Extension(o.getString("id"), o.optString("name"), o.optInt("version"),
                o.optInt("minLauncherVersion"), o.optBoolean("enabled"),
                o.optString("lastError").ifBlank { null })
        }
    }.getOrDefault(emptyList())

    fun register(extension: Extension) {
        val items = all().filterNot { it.id == extension.id } + extension
        persist(items)
    }

    fun setEnabled(id: String, enabled: Boolean) =
        persist(all().map { if (it.id == id) it.copy(enabled = enabled, lastError = null) else it })

    fun recordFailure(id: String, error: String) {
        val key = "errors_$id"
        val log = runCatching { JSONArray(prefs.getString(key, "[]")) }.getOrDefault(JSONArray())
        log.put("${System.currentTimeMillis()}: ${error.take(1200)}")
        while (log.length() > 20) log.remove(0)
        prefs.edit().putString(key, log.toString()).apply()
        persist(all().map { if (it.id == id) it.copy(enabled = false, lastError = error.take(1200)) else it })
    }

    fun errorLog(id: String): List<String> = runCatching {
        val log = JSONArray(prefs.getString("errors_$id", "[]"))
        (0 until log.length()).map { log.optString(it) }
    }.getOrDefault(emptyList())

    fun compatible(extension: Extension, launcherVersion: Int = 1): Boolean =
        extension.version > 0 && extension.minLauncherVersion <= launcherVersion

    private fun persist(items: List<Extension>) {
        val a = JSONArray()
        items.forEach { e ->
            a.put(JSONObject().put("id", e.id).put("name", e.name).put("version", e.version)
                .put("minLauncherVersion", e.minLauncherVersion).put("enabled", e.enabled)
                .put("lastError", e.lastError))
        }
        prefs.edit().putString("items", a.toString()).apply()
    }
}
