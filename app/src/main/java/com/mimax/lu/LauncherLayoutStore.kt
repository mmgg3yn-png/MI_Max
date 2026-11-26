package com.mimax.lu

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/**
 * Persistent, versioned launcher layout model.
 * Stores app shortcuts and folders without depending on a vendor launcher.
 */
class LauncherLayoutStore(context: Context) {
    private val prefs = context.getSharedPreferences("launcher_layout_v1", Context.MODE_PRIVATE)

    data class Entry(
        val id: String,
        val packageName: String,
        val label: String,
        val kind: String = "app",
        val folderId: String? = null,
        val page: Int = 0,
        val position: Int = 0
    )

    data class Folder(val id: String, val title: String, val page: Int, val position: Int)

    @Synchronized fun entries(): List<Entry> = runCatching {
        val array = JSONArray(prefs.getString("entries", "[]"))
        (0 until array.length()).map { i ->
            val o = array.getJSONObject(i)
            Entry(o.getString("id"), o.getString("packageName"), o.optString("label"),
                o.optString("kind", "app"), o.optString("folderId").ifBlank { null },
                o.optInt("page"), o.optInt("position"))
        }
    }.getOrDefault(emptyList())

    @Synchronized fun folders(): List<Folder> = runCatching {
        val array = JSONArray(prefs.getString("folders", "[]"))
        (0 until array.length()).map { i ->
            val o = array.getJSONObject(i)
            Folder(o.getString("id"), o.optString("title", "Folder"), o.optInt("page"), o.optInt("position"))
        }
    }.getOrDefault(emptyList())

    @Synchronized fun saveEntries(items: List<Entry>) {
        val array = JSONArray()
        items.forEach { item ->
            array.put(JSONObject().put("id", item.id).put("packageName", item.packageName)
                .put("label", item.label).put("kind", item.kind).put("folderId", item.folderId)
                .put("page", item.page).put("position", item.position))
        }
        prefs.edit().putString("entries", array.toString()).apply()
    }

    @Synchronized fun saveFolders(items: List<Folder>) {
        val array = JSONArray()
        items.forEach { item ->
            array.put(JSONObject().put("id", item.id).put("title", item.title)
                .put("page", item.page).put("position", item.position))
        }
        prefs.edit().putString("folders", array.toString()).apply()
    }

    fun pageCount(): Int = prefs.getInt("page_count", 1).coerceAtLeast(1)
    fun setPageCount(count: Int) { prefs.edit().putInt("page_count", count.coerceIn(1, 20)).apply() }
}
