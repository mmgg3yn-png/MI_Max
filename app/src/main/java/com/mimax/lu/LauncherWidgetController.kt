package com.mimax.lu

import android.app.Activity
import android.appwidget.AppWidgetHost
import android.appwidget.AppWidgetManager
import android.content.Context
import android.content.Intent
import android.os.Bundle

/**
 * Owns the Android widget-host lifecycle. The launcher UI must call allocateAndBind()
 * from a user gesture and attach the returned AppWidgetHostView to its layout.
 */
class LauncherWidgetController(context: Context) {
    companion object {
        const val HOST_ID = 0x4D494D
        const val REQUEST_BIND_WIDGET = 7101
        const val REQUEST_CONFIGURE_WIDGET = 7102
    }

    private val appContext = context.applicationContext
    private val manager = AppWidgetManager.getInstance(appContext)
    private val host = AppWidgetHost(appContext, HOST_ID)

    fun startListening() = runCatching { host.startListening() }
    fun stopListening() = runCatching { host.stopListening() }

    fun allocateId(): Int = host.allocateAppWidgetId()

    fun bindIntent(widgetId: Int, provider: android.content.ComponentName): Intent? {
        val allowed = manager.bindAppWidgetIdIfAllowed(widgetId, provider)
        if (allowed) return null
        return Intent(AppWidgetManager.ACTION_APPWIDGET_BIND).apply {
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId)
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_PROVIDER, provider)
        }
    }

    fun createView(widgetId: Int): android.appwidget.AppWidgetHostView? =
        runCatching {
            val info = manager.getAppWidgetInfo(widgetId) ?: return null
            host.createView(appContext, widgetId, info).apply { setAppWidget(widgetId, info) }
        }.getOrNull()

    fun configureIntent(widgetId: Int): Intent? {
        val component = manager.getAppWidgetInfo(widgetId)?.configure ?: return null
        return Intent(AppWidgetManager.ACTION_APPWIDGET_CONFIGURE).apply {
            setComponent(component)
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId)
        }
    }

    fun deleteWidget(widgetId: Int) {
        runCatching { host.deleteAppWidgetId(widgetId) }
    }

    fun installedProviders(): List<android.appwidget.AppWidgetProviderInfo> =
        manager.installedProviders ?: emptyList()
}
