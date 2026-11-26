package com.mimax.lu

import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Apps
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Widgets
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

data class LaunchableApp(val label: String, val packageName: String, val icon: android.graphics.drawable.Drawable)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MiMaxLauncherApp() }
    }
}

@Composable
private fun MiMaxLauncherApp() {
    var page by remember { mutableStateOf("home") }
    var blurAmount by remember { mutableFloatStateOf(18f) }
    var glassAlpha by remember { mutableFloatStateOf(0.30f) }
    var aiEndpoint by remember { mutableStateOf("") }
    var aiModel by remember { mutableStateOf("") }
    val context = LocalContext.current
    val apps = remember {
        val pm = context.packageManager
        val intent = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
        @Suppress("DEPRECATION")
        pm.queryIntentActivities(intent, PackageManager.MATCH_ALL)
            .mapNotNull { info ->
                val appInfo = info.activityInfo?.applicationInfo ?: return@mapNotNull null
                LaunchableApp(
                    info.loadLabel(pm).toString(),
                    appInfo.packageName,
                    info.loadIcon(pm)
                )
            }
            .distinctBy { it.packageName }
            .sortedBy { it.label.lowercase(Locale.getDefault()) }
    }

    MaterialTheme(
        colorScheme = darkColorScheme(
            background = Color(0xFF10131B),
            surface = Color(0xFF1C2230),
            primary = Color(0xFFB6D7FF),
            onBackground = Color.White,
            onSurface = Color.White
        )
    ) {
        Box(
            Modifier.fillMaxSize().background(
                Brush.verticalGradient(listOf(Color(0xFF263B55), Color(0xFF111722), Color(0xFF090C12)))
            )
        ) {
            // Decorative glass layers; blur is adjustable in Settings.
            Box(
                Modifier.fillMaxWidth().height(260.dp)
                    .padding(18.dp)
                    .background(Color.White.copy(alpha = glassAlpha), RoundedCornerShape(36.dp))
                    .blur(blurAmount.dp)
            )
            Column(Modifier.fillMaxSize().padding(horizontal = 20.dp)) {
                Spacer(Modifier.height(42.dp))
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Column {
                        Text(SimpleDateFormat("EEEE, d MMMM", Locale.getDefault()).format(Date()), color = Color.White.copy(.75f), fontSize = 14.sp)
                        Text(SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date()), color = Color.White, fontSize = 48.sp, fontWeight = FontWeight.Light)
                    }
                    Surface(color = Color.White.copy(alpha = glassAlpha), shape = CircleShape) {
                        Text("Mi", Modifier.padding(horizontal = 16.dp, vertical = 12.dp), color = Color.White, fontWeight = FontWeight.Bold)
                    }
                }
                Spacer(Modifier.height(22.dp))
                when (page) {
                    "settings" -> SettingsPage(
                        blurAmount, { blurAmount = it }, glassAlpha, { glassAlpha = it },
                        aiEndpoint, { aiEndpoint = it }, aiModel, { aiModel = it },
                        onAbout = { page = "about" }
                    )
                    "about" -> AboutPage(onBack = { page = "settings" })
                    "widgets" -> PlaceholderPage("Widget Studio", "Stacked widgets, smart rotation, resize handles and widget packs are being built as native modules.")
                    "themes" -> PlaceholderPage("Theme Store", "Theme packs, icon packs, wallpapers, fonts, previews and import/export will live here.")
                    else -> HomePage(apps)
                }
                Spacer(Modifier.weight(1f))
                NavigationBar(containerColor = Color.White.copy(alpha = glassAlpha), tonalElevation = 0.dp) {
                    NavigationBarItem(selected = page == "home", onClick = { page = "home" }, icon = { Icon(Icons.Default.Apps, null) }, label = { Text("Home") })
                    NavigationBarItem(selected = page == "widgets", onClick = { page = "widgets" }, icon = { Icon(Icons.Default.Widgets, null) }, label = { Text("Widgets") })
                    NavigationBarItem(selected = page == "themes", onClick = { page = "themes" }, icon = { Icon(Icons.Default.AutoAwesome, null) }, label = { Text("Themes") })
                    NavigationBarItem(selected = page == "settings" || page == "about", onClick = { page = "settings" }, icon = { Icon(Icons.Default.Settings, null) }, label = { Text("Settings") })
                }
                Spacer(Modifier.height(12.dp))
            }
        }
    }
}

@Composable
private fun HomePage(apps: List<LaunchableApp>) {
    val context = LocalContext.current
    Column {
        Text("Your apps", color = Color.White, fontSize = 20.sp, fontWeight = FontWeight.SemiBold)
        Spacer(Modifier.height(12.dp))
        LazyVerticalGrid(columns = GridCells.Fixed(4), modifier = Modifier.weight(1f), contentPadding = PaddingValues(bottom = 16.dp), verticalArrangement = Arrangement.spacedBy(18.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            items(apps, key = { it.packageName }) { app ->
                Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.clickable {
                    context.packageManager.getLaunchIntentForPackage(app.packageName)?.let(context::startActivity)
                }) {
                    Surface(shape = RoundedCornerShape(19.dp), color = Color.White.copy(.16f), modifier = Modifier.size(58.dp)) {
                        Box(contentAlignment = Alignment.Center) {
                            androidx.compose.foundation.Image(
                                painter = androidx.compose.ui.graphics.painter.DrawablePainter(app.icon),
                                contentDescription = app.label,
                                modifier = Modifier.padding(9.dp).fillMaxSize()
                            )
                        }
                    }
                    Spacer(Modifier.height(5.dp))
                    Text(app.label, color = Color.White, fontSize = 11.sp, maxLines = 1)
                }
            }
        }
    }
}

@Composable
private fun SettingsPage(
    blur: Float, onBlur: (Float) -> Unit,
    alpha: Float, onAlpha: (Float) -> Unit,
    endpoint: String, onEndpoint: (String) -> Unit,
    model: String, onModel: (String) -> Unit,
    onAbout: () -> Unit
) {
    Column(Modifier.fillMaxSize()) {
        Text("Settings", color = Color.White, fontSize = 28.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(14.dp))
        Text("Liquid Glass", color = Color.White, fontWeight = FontWeight.SemiBold)
        Text("Blur strength: ${blur.toInt()}", color = Color.White.copy(.7f))
        Slider(value = blur, onValueChange = onBlur, valueRange = 0f..32f)
        Text("Glass transparency: ${(alpha * 100).toInt()}%", color = Color.White.copy(.7f))
        Slider(value = alpha, onValueChange = onAlpha, valueRange = 0.05f..0.85f)
        HorizontalDivider(color = Color.White.copy(.2f), modifier = Modifier.padding(vertical = 12.dp))
        Text("Mi_Max AI", color = Color.White, fontWeight = FontWeight.SemiBold)
        OutlinedTextField(value = endpoint, onValueChange = onEndpoint, label = { Text("AI API endpoint") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        OutlinedTextField(value = model, onValueChange = onModel, label = { Text("Model ID") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        Text("Connect your Mi_Max AI backend here. No credentials are hard-coded.", color = Color.White.copy(.65f), fontSize = 12.sp)
        Spacer(Modifier.height(12.dp))
        Button(onClick = onAbout, modifier = Modifier.fillMaxWidth()) { Text("About / Developer / Account") }
    }
}

@Composable
private fun AboutPage(onBack: () -> Unit) {
    Column(Modifier.fillMaxSize()) {
        Text("About Mi_Max Launcher", color = Color.White, fontSize = 25.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(18.dp))
        Text("Mi_Max Launcher", color = Color.White, fontSize = 20.sp)
        Text("Version 1.0-alpha1  •  com.mimax.lu", color = Color.White.copy(.7f))
        HorizontalDivider(color = Color.White.copy(.2f), modifier = Modifier.padding(vertical = 14.dp))
        Text("Developer", color = Color.White.copy(.65f))
        Text("محمد السعيد علي", color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
        Text("mmgg3yn@gmail.com", color = Color.White.copy(.85f))
        Text("Telegram: @Mi_Max12", color = Color.White.copy(.85f))
        Spacer(Modifier.height(18.dp))
        Text("Account", color = Color.White.copy(.65f))
        Text("Local profile • Sign-in and cloud sync can be connected later.", color = Color.White)
        Spacer(Modifier.height(18.dp))
        OutlinedButton(onClick = onBack) { Text("Back to Settings") }
    }
}

@Composable
private fun PlaceholderPage(title: String, description: String) {
    Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.Center) {
        Text(title, color = Color.White, fontSize = 27.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(10.dp))
        Text(description, color = Color.White.copy(.75f), fontSize = 15.sp)
    }
}
