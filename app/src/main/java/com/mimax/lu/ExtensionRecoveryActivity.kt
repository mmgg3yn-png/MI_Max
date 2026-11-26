package com.mimax.lu

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/** Separate launcher entry point for disabling broken extensions if the main screen fails. */
class ExtensionRecoveryActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val registry = ExtensionRegistry(this)
        setContent {
            val entries = remember { mutableStateListOf<ExtensionRegistry.Extension>().apply { addAll(registry.all()) } }
            MaterialTheme(colorScheme = darkColorScheme()) {
                Column(Modifier.fillMaxSize().padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("Mi_Max Extension Recovery", style = MaterialTheme.typography.headlineSmall)
                    Text("Use this separate screen to disable extensions that stop the launcher from opening.")
                    Button(onClick = {
                        entries.toList().forEach { registry.setEnabled(it.id, false) }
                        entries.clear()
                        entries.addAll(registry.all())
                    }, modifier = Modifier.fillMaxWidth()) { Text("Disable all extensions") }
                    LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        items(entries, key = { it.id }) { item ->
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Column(Modifier.weight(1f)) {
                                    Text(item.name)
                                    Text(item.id, style = MaterialTheme.typography.labelSmall)
                                    item.lastError?.let { Text("Last error: $it", color = MaterialTheme.colorScheme.error) }
                                }
                                Switch(checked = item.enabled, onCheckedChange = { enabled ->
                                    registry.setEnabled(item.id, enabled)
                                    val index = entries.indexOfFirst { it.id == item.id }
                                    if (index >= 0) entries[index] = item.copy(enabled = enabled, lastError = null)
                                })
                            }
                        }
                    }
                }
            }
        }
    }
}
