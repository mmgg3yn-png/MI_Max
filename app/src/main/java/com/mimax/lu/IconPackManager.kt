package com.mimax.lu

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.drawable.Drawable
import android.content.res.XmlResourceParser

/** Supports installed ADW/Nova-style icon packs that expose an appfilter.xml. */
class IconPackManager(private val context: Context) {
    data class Pack(val packageName: String, val label: String)

    private val pm = context.packageManager
    private val iconCache = HashMap<Pair<String, String>, Drawable?>()

    @Suppress("DEPRECATION")
    fun installed(): List<Pack> {
        val actions = listOf(
            "org.adw.launcher.THEMES",
            "com.novalauncher.THEME",
            "com.anddoes.launcher.THEME",
            "com.teslacoilsw.launcher.THEME"
        )
        return actions.flatMap { action ->
            pm.queryIntentActivities(Intent(action), PackageManager.MATCH_ALL).mapNotNull { resolve ->
                val pkg = resolve.activityInfo?.packageName ?: return@mapNotNull null
                Pack(pkg, resolve.loadLabel(pm).toString())
            }
        }.distinctBy { it.packageName }.sortedBy { it.label.lowercase() }
    }

    @Synchronized fun iconFor(iconPackPackage: String, targetPackage: String): Drawable? {
        if (iconPackPackage.isBlank()) return null
        val key = iconPackPackage to targetPackage
        if (iconCache.containsKey(key)) return iconCache[key]
        val resolved = runCatching {
            val resources = pm.getResourcesForApplication(iconPackPackage)
            val xmlId = resources.getIdentifier("appfilter", "xml", iconPackPackage)
            if (xmlId == 0) return null
            val parser: XmlResourceParser = resources.getXml(xmlId)
            var drawableName: String? = null
            try {
                var event = parser.eventType
                while (event != XmlResourceParser.END_DOCUMENT) {
                    if (event == XmlResourceParser.START_TAG && parser.name == "item") {
                        val component = parser.getAttributeValue(null, "component").orEmpty()
                        val packageFromComponent = component.substringAfter('{', "").substringBefore('/')
                        if (packageFromComponent == targetPackage) {
                            drawableName = parser.getAttributeValue(null, "drawable")
                            break
                        }
                    }
                    event = parser.next()
                }
            } finally {
                parser.close()
            }
            val name = drawableName ?: return null
            val id = resources.getIdentifier(name, "drawable", iconPackPackage)
            if (id == 0) null else resources.getDrawable(id, context.theme)
        }.getOrNull()
        iconCache[key] = resolved
        return resolved
    }
}
