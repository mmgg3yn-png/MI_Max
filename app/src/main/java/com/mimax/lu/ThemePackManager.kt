package com.mimax.lu

import android.content.Context
import android.net.Uri
import org.json.JSONObject

/** Imports portable JSON theme packs; assets remain user-provided files/URIs. */
class ThemePackManager(private val context: Context) {
    data class ThemePack(
        val id: String,
        val name: String,
        val backgroundStart: Long,
        val backgroundEnd: Long,
        val accent: Long,
        val iconShape: String
    )

    fun import(uri: Uri): Result<ThemePack> = runCatching {
        val json = context.contentResolver.openInputStream(uri)?.bufferedReader()?.use { it.readText() }
            ?: error("Cannot read theme pack")
        val o = JSONObject(json)
        require(o.optString("format") == "mimax-theme") { "Not a Mi_Max theme pack" }
        val pack = ThemePack(
            id = o.getString("id"),
            name = o.getString("name").take(48),
            backgroundStart = o.getLong("backgroundStart"),
            backgroundEnd = o.getLong("backgroundEnd"),
            accent = o.getLong("accent"),
            iconShape = o.optString("iconShape", "rounded").also {
                require(it in setOf("rounded", "circle", "squircle", "square"))
            }
        )
        require(pack.id.matches(Regex("[A-Za-z0-9_.-]{1,64}"))) { "Invalid theme ID" }
        require(pack.name.isNotBlank()) { "Theme name is empty" }
        val prefs = context.getSharedPreferences("theme_packs_v1", Context.MODE_PRIVATE)
        prefs.edit().putString(pack.id, o.toString()).apply()
        pack
    }

    fun installed(): List<ThemePack> {
        val prefs = context.getSharedPreferences("theme_packs_v1", Context.MODE_PRIVATE)
        return prefs.all.values.mapNotNull { raw ->
            runCatching {
                val o = JSONObject(raw as String)
                ThemePack(o.getString("id"), o.getString("name"), o.getLong("backgroundStart"),
                    o.getLong("backgroundEnd"), o.getLong("accent"), o.optString("iconShape", "rounded"))
            }.getOrNull()
        }
    }
}
