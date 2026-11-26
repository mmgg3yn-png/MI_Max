package com.mimax.lu

import android.content.Context
import android.net.Uri
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.util.zip.ZipInputStream

/**
 * Me Island visual packs (.mt1).
 *
 * A .mt1 is a ZIP archive containing manifest.json. The manifest is declarative:
 * it can configure colors, geometry and animation only; it cannot execute code.
 */
class MeIslandThemeManager(private val context: Context) {
    data class Theme(
        val id: String,
        val name: String,
        val style: String,
        val layout: String,
        val animation: String,
        val background: Long,
        val accent: Long,
        val blur: Int,
        val cornerDp: Int,
        val widthDp: Int,
        val compactHeightDp: Int,
        val expandedHeightDp: Int,
        val animationMs: Int
    )

    companion object {
        const val PREFS = "me_island_themes_v1"
        const val SELECTED = "selected_theme"
        const val BLUR = "blur_enabled"

        val builtIns = listOf(
            Theme("ltin", "LTIN", "ltin", "pill", "spring", 0xFF050505, 0xFFFFFFFF, 18, 28, 178, 34, 104, 260),
            Theme("his", "HIS", "his", "wide_card", "morph", 0xEE10151D, 0xFFB8D9FF, 28, 24, 196, 38, 116, 340),
            Theme("coloros", "ColorOS", "coloros", "fluid", "spring", 0xCC263442, 0xFFBDEBFF, 32, 22, 190, 38, 112, 300)
        )
    }

    private val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    fun all(): List<Theme> {
        val imported = prefs.all.values.mapNotNull { raw ->
            runCatching { fromJson(JSONObject(raw as String)) }.getOrNull()
        }
        return builtIns + imported.filter { p -> builtIns.none { it.id == p.id } }
    }

    fun selectedId(): String = prefs.getString(SELECTED, "his") ?: "his"

    fun select(id: String) {
        require(all().any { it.id == id }) { "Unknown Me Island theme" }
        prefs.edit().putString(SELECTED, id).apply()
    }

    fun current(): Theme = all().firstOrNull { it.id == selectedId() } ?: builtIns[1]

    fun setBlurEnabled(enabled: Boolean) {
        prefs.edit().putBoolean(BLUR, enabled).apply()
    }

    fun blurEnabled(): Boolean = prefs.getBoolean(BLUR, true)

    fun import(uri: Uri): Result<Theme> = runCatching {
        val bytes = context.contentResolver.openInputStream(uri)?.use { input ->
            val out = ByteArrayOutputStream()
            val buffer = ByteArray(8192)
            var total = 0
            while (true) {
                val count = input.read(buffer)
                if (count < 0) break
                total += count
                require(total <= 2 * 1024 * 1024) { "Theme package exceeds 2 MB" }
                out.write(buffer, 0, count)
            }
            out.toByteArray()
        } ?: error("Cannot read theme file")

        val jsonText = if (bytes.size >= 4 && bytes[0] == 0x50.toByte() && bytes[1] == 0x4B.toByte()) {
            var manifest: String? = null
            ZipInputStream(bytes.inputStream()).use { zip ->
                while (true) {
                    val entry = zip.nextEntry ?: break
                    require(!entry.name.startsWith("/") && !entry.name.contains("..")) { "Unsafe theme entry" }
                    if (entry.name == "manifest.json") {
                        val out = ByteArrayOutputStream()
                        val buffer = ByteArray(4096)
                        var total = 0
                        while (true) {
                            val count = zip.read(buffer)
                            if (count < 0) break
                            total += count
                            require(total <= 128 * 1024) { "Theme manifest is too large" }
                            out.write(buffer, 0, count)
                        }
                        manifest = out.toString(Charsets.UTF_8.name())
                        break
                    }
                }
            }
            manifest ?: error("The .mt1 archive has no manifest.json")
        } else {
            bytes.toString(Charsets.UTF_8)
        }

        val root = JSONObject(jsonText)
        require(root.optString("format") in setOf("mimax-island-theme", "mt1")) { "Unsupported .mt1 format" }
        val theme = fromJson(root)
        require(theme.id.matches(Regex("[A-Za-z0-9_.-]{1,48}"))) { "Invalid theme ID" }
        require(theme.name.isNotBlank()) { "Theme name is empty" }
        require(theme.style in setOf("ltin", "his", "coloros", "custom")) { "Unsupported visual engine" }
        prefs.edit().putString("pack_${theme.id}", root.toString()).apply()
        theme
    }

    private fun fromJson(o: JSONObject): Theme {
        val theme = o.optJSONObject("theme") ?: o
        return Theme(
            id = theme.getString("id"),
            name = theme.getString("name").take(48),
            style = theme.optString("style", "custom"),
            layout = theme.optString("layout", "wide_card").also { require(it in setOf("pill", "wide_card", "split", "fluid")) },
            animation = theme.optString("animation", "spring").also { require(it in setOf("spring", "morph", "fade_slide")) },
            background = theme.optLong("background", 0xEE10151D),
            accent = theme.optLong("accent", 0xFFB8D9FF),
            blur = theme.optInt("blur", 24).coerceIn(0, 80),
            cornerDp = theme.optInt("cornerDp", 26).coerceIn(8, 48),
            widthDp = theme.optInt("widthDp", 190).coerceIn(120, 300),
            compactHeightDp = theme.optInt("compactHeightDp", 38).coerceIn(24, 70),
            expandedHeightDp = theme.optInt("expandedHeightDp", 112).coerceIn(60, 220),
            animationMs = theme.optInt("animationMs", 300).coerceIn(100, 900)
        )
    }
}
