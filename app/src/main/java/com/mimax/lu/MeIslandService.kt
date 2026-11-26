package com.mimax.lu

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.provider.Settings
import android.view.Gravity
import android.view.MotionEvent
import android.view.WindowManager
import android.view.animation.AccelerateDecelerateInterpolator
import android.view.animation.DecelerateInterpolator
import android.view.animation.OvershootInterpolator
import android.widget.TextView
import java.util.Locale

/** Independent live-activity overlay. Requires the user's explicit overlay permission. */
class MeIslandService : Service() {
    companion object {
        const val ACTION_START = "com.mimax.lu.meisland.START"
        const val ACTION_STOP = "com.mimax.lu.meisland.STOP"
        const val EXTRA_SECONDS = "seconds"
        private const val CHANNEL = "mimax_me_island"
        private const val NOTIFICATION_ID = 7401
        private const val STATE_PREFS = "me_island_v1"
    }

    private val handler = Handler(Looper.getMainLooper())
    private var windowManager: WindowManager? = null
    private var island: TextView? = null
    private var layoutParams: WindowManager.LayoutParams? = null
    private var expanded = false
    private var endAt = 0L
    private var touchStartX = 0f
    private var touchStartY = 0f

    private val ticker = object : Runnable {
        override fun run() {
            val remaining = ((endAt - System.currentTimeMillis()) / 1000L).coerceAtLeast(0)
            if (remaining <= 0) {
                removeIsland()
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
                return
            }
            render(remaining)
            handler.postDelayed(this, 1000L)
        }
    }

    override fun onCreate() {
        super.onCreate()
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP -> {
                handler.removeCallbacks(ticker)
                getSharedPreferences(STATE_PREFS, MODE_PRIVATE).edit().remove("timer_end").apply()
                removeIsland()
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
                return START_NOT_STICKY
            }
            ACTION_START, null -> {
                if (!Settings.canDrawOverlays(this)) {
                    stopSelf()
                    return START_NOT_STICKY
                }
                val prefs = getSharedPreferences(STATE_PREFS, MODE_PRIVATE)
                endAt = if (intent?.action == ACTION_START) {
                    val seconds = intent.getIntExtra(EXTRA_SECONDS, 600).coerceIn(1, 86400)
                    (System.currentTimeMillis() + seconds * 1000L).also {
                        prefs.edit().putLong("timer_end", it).apply()
                    }
                } else prefs.getLong("timer_end", 0L)

                if (endAt <= System.currentTimeMillis()) {
                    stopSelf()
                    return START_NOT_STICKY
                }
                val notification = buildNotification()
                if (Build.VERSION.SDK_INT >= 34) {
                    startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
                } else {
                    startForeground(NOTIFICATION_ID, notification)
                }
                ensureIsland()
                handler.removeCallbacks(ticker)
                handler.post(ticker)
            }
        }
        return START_STICKY
    }

    private fun createNotificationChannel() {
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(
            NotificationChannel(CHANNEL, "Me Island activities", NotificationManager.IMPORTANCE_LOW)
        )
    }

    private fun buildNotification(): Notification {
        val builder = if (Build.VERSION.SDK_INT >= 26) Notification.Builder(this, CHANNEL) else Notification.Builder(this)
        return builder.setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setContentTitle("Me Island is active")
            .setContentText("Timer is running")
            .setOngoing(true)
            .build()
    }

    private fun ensureIsland() {
        if (island != null) return
        val theme = MeIslandThemeManager(this).current()
        val view = TextView(this).apply {
            setTextColor(Color.WHITE)
            textSize = if (theme.style == "ltin") 12f else 13f
            typeface = Typeface.create("sans-serif-medium", Typeface.NORMAL)
            gravity = Gravity.CENTER
            setPadding(dp(14), dp(5), dp(14), dp(5))
            background = makeBackground(theme)
            elevation = dp(14).toFloat()
            setOnClickListener {
                expanded = !expanded
                render(((endAt - System.currentTimeMillis()) / 1000L).coerceAtLeast(0))
            }
            setOnTouchListener { _, event ->
                when (event.actionMasked) {
                    MotionEvent.ACTION_DOWN -> {
                        touchStartX = event.rawX
                        touchStartY = event.rawY
                        false
                    }
                    MotionEvent.ACTION_UP -> {
                        val dx = event.rawX - touchStartX
                        val dy = event.rawY - touchStartY
                        if (kotlin.math.abs(dy) > dp(36) && kotlin.math.abs(dy) > kotlin.math.abs(dx)) {
                            expanded = dy > 0
                            render(((endAt - System.currentTimeMillis()) / 1000L).coerceAtLeast(0))
                            true
                        } else false
                    }
                    else -> false
                }
            }
        }

        val width = dp(if (theme.style == "ltin") 154 else theme.widthDp)
        val params = WindowManager.LayoutParams(
            width,
            dp(theme.compactHeightDp),
            if (Build.VERSION.SDK_INT >= 26) WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY else WindowManager.LayoutParams.TYPE_PHONE,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.LEFT
            val cutout = if (Build.VERSION.SDK_INT >= 30) {
                runCatching { windowManager?.currentWindowMetrics?.windowInsets?.displayCutout?.boundingRects?.firstOrNull() }.getOrNull()
            } else null
            if (cutout != null) {
                x = (cutout.centerX() - width / 2).coerceAtLeast(0)
                y = cutout.bottom + dp(2)
            } else {
                gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL
                y = statusBarHeight() + dp(3)
            }
            if (Build.VERSION.SDK_INT >= 31 && MeIslandThemeManager(this@MeIslandService).blurEnabled()) {
                flags = flags or WindowManager.LayoutParams.FLAG_BLUR_BEHIND
                setBlurBehindRadius(dp(theme.blur))
            }
        }
        island = view
        layoutParams = params
        runCatching { windowManager?.addView(view, params) }.onFailure {
            island = null
            layoutParams = null
        }
        view.scaleX = .72f
        view.scaleY = .72f
        view.alpha = 0f
        view.animate().alpha(1f).scaleX(1f).scaleY(1f).setInterpolator(animationInterpolator(theme.animation)).setDuration(theme.animationMs.toLong()).start()
    }

    private fun makeBackground(theme: MeIslandThemeManager.Theme): GradientDrawable {
        val fill = if (theme.style == "ltin") Color.BLACK else theme.background.toInt()
        return GradientDrawable().apply {
            setColor(fill)
            cornerRadius = dp(if (theme.layout == "pill") 40 else theme.cornerDp).toFloat()
            setStroke(dp(1), if (theme.style == "his") Color.argb(65, 210, 232, 255) else Color.argb(35, 255, 255, 255))
        }
    }

    private fun render(seconds: Long) {
        val view = island ?: return
        val theme = MeIslandThemeManager(this).current()
        val minutes = seconds / 60
        val remainder = seconds % 60
        val time = String.format(Locale.getDefault(), "%02d:%02d", minutes, remainder)
        view.text = when (theme.layout) {
            "pill" -> if (expanded) "◷   $time     TIMER" else "◷  $time"
            "split" -> if (expanded) "◷  $time     •     LIVE\nOnePlus-style activity card" else "◷  $time   •"
            "fluid" -> if (expanded) "TIMER  •  $time\nSwipe up to collapse" else "◷   $time"
            else -> if (expanded) "⏱  TIMER     $time\nSwipe up to collapse" else "⏱  $time"
        }
        view.textSize = if (expanded) 13f else 12f
        view.background = makeBackground(theme)
        layoutParams?.let { params ->
            params.width = dp(if (expanded) theme.widthDp.coerceAtLeast(210) else if (theme.layout == "pill") 154 else theme.widthDp)
            params.height = dp(if (expanded) theme.expandedHeightDp else theme.compactHeightDp)
            runCatching { windowManager?.updateViewLayout(view, params) }
        }
        view.animate().setInterpolator(animationInterpolator(theme.animation)).setDuration(theme.animationMs.toLong()).start()
    }

    private fun animationInterpolator(name: String) = when (name) {
        "spring" -> OvershootInterpolator(0.65f)
        "fade_slide" -> DecelerateInterpolator()
        else -> AccelerateDecelerateInterpolator()
    }

    private fun removeIsland() {
        island?.let { view ->
            val duration = MeIslandThemeManager(this).current().animationMs.coerceAtMost(350).toLong()
            view.animate().alpha(0f).scaleX(.78f).scaleY(.78f).setDuration(duration).withEndAction {
                runCatching { windowManager?.removeView(view) }
            }.start()
        }
        island = null
        layoutParams = null
    }

    private fun statusBarHeight(): Int {
        val id = resources.getIdentifier("status_bar_height", "dimen", "android")
        return if (id > 0) resources.getDimensionPixelSize(id) else dp(24)
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    override fun onDestroy() {
        handler.removeCallbacks(ticker)
        removeIsland()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
