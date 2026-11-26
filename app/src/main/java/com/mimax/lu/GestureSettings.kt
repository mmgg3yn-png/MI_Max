package com.mimax.lu

import android.content.Context

/** Gesture bindings are configurable and resolved by the launcher surface. */
class GestureSettings(context: Context) {
    enum class Gesture { DOUBLE_TAP_HOME, SWIPE_UP, SWIPE_DOWN, TWO_FINGER_SWIPE_UP, TWO_FINGER_SWIPE_DOWN, PINCH_IN }
    enum class Action { NONE, OPEN_SEARCH, OPEN_APP_DRAWER, OPEN_NOTIFICATIONS, OPEN_QUICK_SETTINGS, LOCK_SCREEN_REQUEST, OPEN_SETTINGS }

    private val prefs = context.getSharedPreferences("gesture_settings_v1", Context.MODE_PRIVATE)

    fun actionFor(gesture: Gesture): Action =
        runCatching { Action.valueOf(prefs.getString(gesture.name, defaultFor(gesture).name)!!) }
            .getOrDefault(Action.NONE)

    fun setAction(gesture: Gesture, action: Action) {
        prefs.edit().putString(gesture.name, action.name).apply()
    }

    private fun defaultFor(gesture: Gesture): Action = when (gesture) {
        Gesture.DOUBLE_TAP_HOME -> Action.OPEN_SEARCH
        Gesture.SWIPE_UP -> Action.OPEN_APP_DRAWER
        Gesture.SWIPE_DOWN -> Action.OPEN_NOTIFICATIONS
        Gesture.TWO_FINGER_SWIPE_UP -> Action.OPEN_SETTINGS
        Gesture.TWO_FINGER_SWIPE_DOWN -> Action.OPEN_QUICK_SETTINGS
        Gesture.PINCH_IN -> Action.NONE
    }
}
