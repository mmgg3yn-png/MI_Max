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
import android.view.WindowManager
import android.widget.TextView
import java.util.Locale

/** User-started live activity overlay. It is intentionally independent from the launcher Activity. */
class MeIslandService : Service() {
    companion object {
        const val ACTION_START = "com.mimax.lu.meisland.START"
        const val ACTION_STOP = "com.mimax.lu.meisland.STOP"
        const val EXTRA_SECONDS = "seconds"
        private const val CHANNEL = "mimax_me_island"
        private const val NOTIFICATION_ID = 7401
    }

    private val handler = Handler(Looper.getMainLooper())
    private var windowManager: WindowManager? = null
    private var island: TextView? = null
    private var expanded = false
    private var endAt = 0L

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
                removeIsland()
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
                return START_NOT_STICKY
            }
            ACTION_START -> {
                if (!Settings.canDrawOverlays(this)) {
                    stopSelf()
                    return START_NOT_STICKY
                }
                val seconds = (intent.getIntExtra(EXTRA_SECONDS, 600)).coerceIn(1, 86400)
                endAt = System.currentTimeMillis() + seconds * 1000L
                getSharedPreferences("me_island_v1", MODE_PRIVATE).edit().putLong("timer_end", endAt).apply()
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
        manager.createNotificationChannel(NotificationChannel(CHANNEL, "Me Island activities", NotificationManager.IMPORTANCE_LOW))
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
        val view = TextView(this).apply {
            setTextColor(Color.WHITE)
            textSize = 13f
            typeface = Typeface.create("sans-serif-medium", Typeface.NORMAL)
            gravity = Gravity.CENTER
            setPadding(dp(20), dp(10), dp(20), dp(10))
            background = GradientDrawable().apply {
                setColor(Color.argb(238, 15, 18, 25))
                cornerRadius = dp(28).toFloat()
                setStroke(dp(1), Color.argb(90, 255, 255, 255))
            }
            elevation = dp(12).toFloat()
            setOnClickListener { expanded = !expanded; render(((endAt-System.currentTimeMillis())/1000L).coerceAtLeast(0)) }
        }
        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            if (Build.VERSION.SDK_INT >= 26) WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY else WindowManager.LayoutParams.TYPE_PHONE,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL
            y = statusBarHeight() + dp(3)
            if (Build.VERSION.SDK_INT >= 31) {
                flags = flags or WindowManager.LayoutParams.FLAG_BLUR_BEHIND
                setBlurBehindRadius(dp(22))
            }
        }
        island = view
        runCatching { windowManager?.addView(view, params) }.onFailure { island = null }
        view.scaleX = .78f
        view.scaleY = .78f
        view.alpha = 0f
        view.animate().alpha(1f).scaleX(1f).scaleY(1f).setDuration(280).start()
    }

    private fun render(seconds: Long) {
        val view = island ?: return
        val minutes = seconds / 60
        val remainder = seconds % 60
        val time = String.format(Locale.getDefault(), "%02d:%02d", minutes, remainder)
        view.text = if (expanded) "⏱  TIMER   $time\nTap to collapse" else "⏱  $time"
        view.textSize = if (expanded) 14f else 13f
    }

    private fun removeIsland() {
        island?.let { view ->
            view.animate().alpha(0f).scaleX(.8f).scaleY(.8f).setDuration(180).withEndAction {
                runCatching { windowManager?.removeView(view) }
            }.start()
        }
        island = null
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
