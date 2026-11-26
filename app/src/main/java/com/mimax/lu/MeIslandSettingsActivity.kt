package com.mimax.lu

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/** Settings screen for the first working Me Island activity: a live countdown overlay. */
class MeIslandSettingsActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(colorScheme = darkColorScheme()) {
                var seconds by remember { mutableIntStateOf(600) }
                var status by remember { mutableStateOf("Choose a timer and grant overlay permission.") }
                Column(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                    Text("Me Island", style = MaterialTheme.typography.headlineLarge)
                    Text("Live island stays visible over other apps while an activity is running.")
                    Text("Timer duration: ${seconds / 60} minutes")
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        listOf(60, 300, 600, 1800).forEach { value ->
                            OutlinedButton(onClick = { seconds = value }) { Text(if (value < 60) "${value}s" else "${value / 60}m") }
                        }
                    }
                    Button(onClick = {
                        if (!Settings.canDrawOverlays(this@MeIslandSettingsActivity)) {
                            status = "Allow Display over other apps, then return here and start the timer."
                            startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
                        } else {
                            val service = Intent(this@MeIslandSettingsActivity, MeIslandService::class.java)
                                .setAction(MeIslandService.ACTION_START)
                                .putExtra(MeIslandService.EXTRA_SECONDS, seconds)
                            if (Build.VERSION.SDK_INT >= 26) startForegroundService(service) else startService(service)
                            status = "Me Island timer started. It remains visible while you use other apps."
                        }
                    }, modifier = Modifier.fillMaxWidth()) { Text("Start Me Island timer") }
                    OutlinedButton(onClick = {
                        startService(Intent(this@MeIslandSettingsActivity, MeIslandService::class.java).setAction(MeIslandService.ACTION_STOP))
                        status = "Me Island activity stopped."
                    }, modifier = Modifier.fillMaxWidth()) { Text("Stop activity") }
                    Text(status, style = MaterialTheme.typography.bodyMedium)
                    Spacer(Modifier.height(8.dp))
                    Text("Current implementation: timer overlay, compact/expanded tap interaction and animated glass capsule. More activity providers and visual engines are still to be implemented.")
                }
            }
        }
    }
}
