package com.mimax.lu

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

class MeIslandSettingsActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(colorScheme = darkColorScheme()) {
                val manager = remember { MeIslandThemeManager(this@MeIslandSettingsActivity) }
                var selected by remember { mutableStateOf(manager.selectedId()) }
                var themes by remember { mutableStateOf(manager.all()) }
                var blurEnabled by remember { mutableStateOf(manager.blurEnabled()) }
                var seconds by remember { mutableIntStateOf(600) }
                var status by remember { mutableStateOf("Choose a design, then start a timer to preview Me Island over other apps.") }

                val importTheme = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri: Uri? ->
                    if (uri != null) {
                        manager.import(uri).fold(
                            { imported ->
                                themes = manager.all()
                                selected = imported.id
                                manager.select(imported.id)
                                status = "Imported and applied: ${imported.name}"
                            },
                            { error -> status = "Import failed: ${error.message}" }
                        )
                    }
                }

                Column(
                    Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(18.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text("Me Island", style = MaterialTheme.typography.headlineLarge)
                    Text("An independent live island that can remain visible above other apps after you grant overlay permission.")

                    Text("ثيمات الجزيرة", style = MaterialTheme.typography.titleLarge)
                    themes.forEach { theme ->
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(20.dp),
                            colors = CardDefaults.cardColors(containerColor = Color(0xFF202A38))
                        ) {
                            Row(
                                Modifier.fillMaxWidth().padding(10.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                RadioButton(
                                    selected = selected == theme.id,
                                    onClick = {
                                        selected = theme.id
                                        manager.select(theme.id)
                                        status = "Applied ${theme.name}. Start a timer to preview the island."
                                    }
                                )
                                Column(Modifier.weight(1f)) {
                                    Text(theme.name, style = MaterialTheme.typography.titleMedium)
                                    Text(
                                        when (theme.style) {
                                            "ltin" -> "iPhone Dynamic Island layout and compact pill"
                                            "his" -> "Xiaomi HyperIsland-inspired activity card"
                                            "coloros" -> "ColorOS-inspired translucent alert capsule"
                                            else -> "Imported custom design"
                                        },
                                        style = MaterialTheme.typography.bodySmall
                                    )
                                }
                                Spacer(Modifier.height(1.dp))
                            }
                        }
                    }

                    OutlinedButton(
                        onClick = { importTheme.launch(arrayOf("application/zip", "application/octet-stream", "*/*")) },
                        modifier = Modifier.fillMaxWidth()
                    ) { Text("Import theme (.mt1)") }

                    OutlinedButton(
                        onClick = {
                            runCatching { startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)) }
                            status = "Enable Mi_Max Launcher under Notification Access to show notification cards in Me Island."
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) { Text("Enable notification access") }

                    Text("Glass / Blur", style = MaterialTheme.typography.titleMedium)
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Background blur", modifier = Modifier.weight(1f))
                        Switch(checked = blurEnabled, onCheckedChange = {
                            blurEnabled = it
                            manager.setBlurEnabled(it)
                        })
                    }
                    Text("Blur is applied only when the Android version and device support it.")

                    Text("Timer test", style = MaterialTheme.typography.titleMedium)
                    Text("Duration: ${seconds / 60} minute(s)")
                    Slider(
                        value = seconds.toFloat(),
                        onValueChange = { seconds = it.toInt().coerceIn(60, 3600) },
                        valueRange = 60f..3600f
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        listOf(60, 300, 600, 1800).forEach { value ->
                            OutlinedButton(onClick = { seconds = value }, modifier = Modifier.weight(1f)) {
                                Text(if (value < 60) "${value}s" else "${value / 60}m")
                            }
                        }
                    }

                    Button(
                        onClick = {
                            if (!Settings.canDrawOverlays(this@MeIslandSettingsActivity)) {
                                status = "Allow Display over other apps, then return and start the timer."
                                startActivity(
                                    Intent(
                                        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                                        Uri.parse("package:$packageName")
                                    )
                                )
                            } else {
                                val service = Intent(this@MeIslandSettingsActivity, MeIslandService::class.java)
                                    .setAction(MeIslandService.ACTION_START)
                                    .putExtra(MeIslandService.EXTRA_SECONDS, seconds)
                                if (Build.VERSION.SDK_INT >= 26) startForegroundService(service) else startService(service)
                                status = "Me Island timer started. Open another app to test the persistent overlay."
                            }
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) { Text("Start Me Island timer") }

                    OutlinedButton(
                        onClick = {
                            startService(
                                Intent(this@MeIslandSettingsActivity, MeIslandService::class.java)
                                    .setAction(MeIslandService.ACTION_STOP)
                            )
                            status = "Me Island activity stopped."
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) { Text("Stop activity") }

                    Text(status, style = MaterialTheme.typography.bodyMedium)
                    Text(
                        "Current activity provider: countdown timer. Music, calls, downloads, notifications, multi-activity switching and the full extension runtime are separate modules still under development.",
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }
        }
    }
}
