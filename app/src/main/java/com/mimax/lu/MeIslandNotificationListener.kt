package com.mimax.lu

import android.app.Notification
import android.content.ComponentName
import android.content.Intent
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.view.Gravity
import android.view.WindowManager
import android.widget.TextView

/**
 * Optional notification activity provider for Me Island.
 * Android requires the user to explicitly enable Notification Access.
 */
class MeIslandNotificationListener : NotificationListenerService() {
    private val handler = Handler(Looper.getMainLooper())
    private var windowManager: WindowManager? = null
    private var currentView: TextView? = null
    private var removeTask: Runnable? = null

    override fun onCreate() {
        super.onCreate()
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
    }

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        if (sbn.packageName == packageName || sbn.isGroup || sbn.notification.flags and Notification.FLAG_GROUP_SUMMARY != 0) return
        val notification = sbn.notification
        val extras = notification.extras
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString().orEmpty()
        val text = (extras.getCharSequence(Notification.EXTRA_BIG_TEXT)
            ?: extras.getCharSequence(Notification.EXTRA_TEXT))?.toString().orEmpty()
        if (title.isBlank() && text.isBlank()) return
        if (notification.category == Notification.CATEGORY_SERVICE && notification.flags and Notification.FLAG_ONGOING_EVENT != 0) return
        showNotificationCard(sbn, title, text)
    }

    private fun showNotificationCard(sbn: StatusBarNotification, title: String, body: String) {
        if (!Settings.canDrawOverlays(this)) return
        val theme = MeIslandThemeManager(this).current()
        val view = TextView(this).apply {
            setTextColor(Color.WHITE)
            textSize = 12.5f
            typeface = Typeface.create("sans-serif-medium", Typeface.NORMAL)
            gravity = Gravity.CENTER_VERTICAL
            maxLines = 3
            ellipsize = android.text.TextUtils.TruncateAt.END
            text = if (body.isBlank()) title.take(90) else "$title\n$body".take(180)
            setPadding(dp(17), dp(10), dp(17), dp(10))
            background = GradientDrawable().apply {
                setColor(if (theme.style == "ltin") Color.BLACK else theme.background.toInt())
                cornerRadius = dp(theme.cornerDp).toFloat()
                setStroke(dp(1), Color.argb(55, 255, 255, 255))
            }
            elevation = dp(14).toFloat()
            setOnClickListener {
                runCatching { sbn.notification.contentIntent?.send() }
                dismissCard()
            }
        }
        dismissCard()
        val width = dp(theme.widthDp.coerceIn(150, 300))
        val params = WindowManager.LayoutParams(
            width,
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL
            y = cameraSafeTop() + dp(5)
            if (Build.VERSION.SDK_INT >= 31 && MeIslandThemeManager(this@MeIslandNotificationListener).blurEnabled()) {
                flags = flags or WindowManager.LayoutParams.FLAG_BLUR_BEHIND
                setBlurBehindRadius(dp(theme.blur))
            }
        }
        currentView = view
        runCatching { windowManager?.addView(view, params) }.onFailure { currentView = null }
        view.alpha = 0f
        view.scaleX = .82f
        view.scaleY = .82f
        view.animate().alpha(1f).scaleX(1f).scaleY(1f).setDuration(theme.animationMs.toLong()).start()
        removeTask = Runnable { dismissCard() }
        handler.postDelayed(removeTask!!, 4500L)
    }

    private fun dismissCard() {
        removeTask?.let { handler.removeCallbacks(it) }
        removeTask = null
        currentView?.let { view ->
            view.animate().alpha(0f).scaleX(.86f).scaleY(.86f).setDuration(160).withEndAction {
                runCatching { windowManager?.removeView(view) }
            }.start()
        }
        currentView = null
    }

    private fun cameraSafeTop(): Int {
        if (Build.VERSION.SDK_INT >= 30) {
            val cutout = runCatching { windowManager?.currentWindowMetrics?.windowInsets?.displayCutout?.boundingRects?.firstOrNull() }.getOrNull()
            if (cutout != null) return cutout.bottom
        }
        val id = resources.getIdentifier("status_bar_height", "dimen", "android")
        return if (id > 0) resources.getDimensionPixelSize(id) else dp(24)
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    override fun onDestroy() {
        dismissCard()
        handler.removeCallbacksAndMessages(null)
        super.onDestroy()
    }
}
