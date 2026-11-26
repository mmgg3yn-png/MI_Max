package com.mimax.lu

import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.tween
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private val glass = Color.White.copy(alpha = .13f)
private data class AppEntry(val name:String,val pkg:String,val icon:android.graphics.drawable.Drawable)

class MainActivity : ComponentActivity() {
    private lateinit var widgetController: LauncherWidgetController
    override fun onStart() {
        super.onStart()
        if (::widgetController.isInitialized) widgetController.startListening()
    }
    override fun onStop() {
        if (::widgetController.isInitialized) widgetController.stopListening()
        super.onStop()
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        widgetController = LauncherWidgetController(this)
        setContent { MiMaxLauncher(widgetController) }
    }
}

@Composable
private fun MiMaxLauncher(widgetController: LauncherWidgetController) {
    val ctx= LocalContext.current
    val prefs= remember { ctx.getSharedPreferences("mimax_launcher",0) }
    var tab by remember { mutableStateOf("home") }
    var query by remember { mutableStateOf("") }
    var blur by remember { mutableFloatStateOf(prefs.getFloat("blur",12f)) }
    var opacity by remember { mutableFloatStateOf(prefs.getFloat("opacity",.22f)) }
    var columns by remember { mutableIntStateOf(prefs.getInt("columns",4)) }
    var theme by remember { mutableStateOf(prefs.getString("theme","Midnight Glass") ?: "Midnight Glass") }
    var endpoint by remember { mutableStateOf(prefs.getString("ai_endpoint","") ?: "") }
    var model by remember { mutableStateOf(prefs.getString("ai_model","") ?: "") }
    var apiKey by remember { mutableStateOf(prefs.getString("ai_key","") ?: "") }
    var showAccount by remember { mutableStateOf(false) }
    val colors = when(theme) {
        "Snow Glass" -> listOf(Color(0xFF66788C),Color(0xFF263747),Color(0xFF101923))
        "Ocean" -> listOf(Color(0xFF126E82),Color(0xFF132C42),Color(0xFF07131F))
        "Aurora" -> listOf(Color(0xFF59477A),Color(0xFF253B58),Color(0xFF101522))
        else -> listOf(Color(0xFF33465F),Color(0xFF151E2C),Color(0xFF080C13))
    }
    val apps= remember {
        val pm=ctx.packageManager
        val i=Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
        @Suppress("DEPRECATION")
        pm.queryIntentActivities(i,PackageManager.MATCH_ALL).mapNotNull { r ->
            val ai=r.activityInfo?.applicationInfo ?: return@mapNotNull null
            AppEntry(r.loadLabel(pm).toString(),ai.packageName,r.loadIcon(pm))
        }.distinctBy{it.pkg}.sortedBy{it.name.lowercase()}
    }
    val filtered=apps.filter{it.name.contains(query,true)}
    fun save(k:String,v:Any) { prefs.edit().apply {
        when(v){ is Float->putFloat(k,v); is Int->putInt(k,v); is String->putString(k,v) }
    }.apply() }
    MaterialTheme(colorScheme=darkColorScheme(primary=Color(0xFFB9D9FF),surface=Color(0xFF202B3A),background=Color(0xFF0B111B))) {
        Box(Modifier.fillMaxSize().background(Brush.verticalGradient(colors))) {
            Column(Modifier.fillMaxSize().padding(horizontal=18.dp)) {
                Spacer(Modifier.height(38.dp))
                Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween,verticalAlignment=Alignment.CenterVertically) {
                    Column {
                        Text(SimpleDateFormat("EEEE, d MMM",Locale.getDefault()).format(Date()),color=Color.White.copy(.72f),fontSize=13.sp)
                        Text(SimpleDateFormat("HH:mm",Locale.getDefault()).format(Date()),color=Color.White,fontSize=43.sp,fontWeight=FontWeight.Light)
                    }
                    Surface(color=Color.White.copy(opacity),shape=CircleShape) { Text("Mi_Max",Modifier.padding(horizontal=15.dp,vertical=11.dp),color=Color.White,fontWeight=FontWeight.Bold) }
                }
                Spacer(Modifier.height(15.dp))
                AnimatedContent(targetState=tab,transitionSpec={ androidx.compose.animation.fadeIn(tween(180)) togetherWith androidx.compose.animation.fadeOut(tween(120)) },label="pages") { page ->
                    when(page) {
                        "apps" -> AppsPage(filtered,query,{query=it})
                        "ai" -> AiChatPage(endpoint,model,apiKey)
                        "widgets" -> WidgetsPage(widgetController)
                        "themes" -> ThemesPage(theme,{theme=it;save("theme",it)})
                        "settings" -> SettingsPage(blur,{blur=it;save("blur",it)},opacity,{opacity=it;save("opacity",it)},columns,{columns=it;save("columns",it)},endpoint,{endpoint=it;save("ai_endpoint",it)},model,{model=it;save("ai_model",it)},apiKey,{apiKey=it;save("ai_key",it)},{showAccount=true})
                        "account" -> AccountPage { showAccount=false;tab="settings" }
                        else -> HomePage(apps,columns,opacity,{tab="apps"},{tab="settings"})
                    }
                }
                Spacer(Modifier.weight(1f))
                NavigationBar(containerColor=Color.White.copy(opacity),tonalElevation=0.dp) {
                    listOf(Triple("home","Home",Icons.Default.Home),Triple("apps","Apps",Icons.Default.Apps),Triple("ai","AI",Icons.Default.AutoAwesome),Triple("widgets","Widgets",Icons.Default.Widgets),Triple("themes","Themes",Icons.Default.Palette),Triple("settings","Settings",Icons.Default.Settings)).forEach { (id,label,ic) ->
                        NavigationBarItem(selected=tab==id,onClick={tab=id},icon={Icon(ic,null)},label={Text(label,fontSize=10.sp)})
                    }
                }
                Spacer(Modifier.height(9.dp))
            }
        }
        if(showAccount) AccountDialog(onDismiss={showAccount=false})
    }
}

@Composable private fun AiChatPage(endpoint: String, model: String, apiKey: String) {
    val scope = rememberCoroutineScope()
    val client = remember { LauncherAiClient() }
    var prompt by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val messages = remember { mutableStateListOf<Pair<String, String>>() }
    Column(Modifier.fillMaxSize()) {
        Text("Mi_Max AI", color=Color.White, fontSize=25.sp, fontWeight=FontWeight.Bold)
        Text(if (model.isBlank()) "Set endpoint, model and API key in Settings" else "Model: $model", color=Color.White.copy(.65f), fontSize=11.sp)
        Spacer(Modifier.height(8.dp))
        androidx.compose.foundation.lazy.LazyColumn(
            modifier=Modifier.weight(1f).fillMaxWidth(),
            verticalArrangement=Arrangement.spacedBy(8.dp),
            contentPadding=PaddingValues(vertical=8.dp)
        ) {
            items(messages.size) { index ->
                val item = messages[index]
                Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(15.dp))
                    .background(if (item.first == "You") Color.White.copy(.16f) else Color(0xFF23364A))
                    .padding(12.dp)) {
                    Text(item.first, color=Color(0xFFB9D9FF), fontSize=10.sp, fontWeight=FontWeight.Bold)
                    Text(item.second, color=Color.White, fontSize=14.sp)
                }
            }
            if (busy) item { Text("Mi_Max AI is responding…", color=Color.White.copy(.7f)) }
        }
        error?.let { Text(it, color=Color(0xFFFFB4AB), fontSize=12.sp) }
        Row(verticalAlignment=Alignment.CenterVertically) {
            GlassInput(prompt,{prompt=it},"Write a message…")
            Spacer(Modifier.width(7.dp))
            IconButton(onClick={
                val text = prompt.trim()
                if (text.isNotEmpty() && !busy) {
                    prompt = ""
                    error = null
                    messages.add("You" to text)
                    busy = true
                    scope.launch {
                        val result = client.complete(endpoint, model, apiKey, text)
                        result.onSuccess { messages.add("Mi_Max AI" to it) }
                            .onFailure { error = it.message ?: "AI request failed" }
                        busy = false
                    }
                }
            }, enabled=!busy) { Icon(Icons.Default.Send, contentDescription="Send", tint=Color.White) }
        }
    }
}
@Composable private fun HomePage(apps:List<AppEntry>,cols:Int,alpha:Float,onAll:()->Unit,onSettings:()->Unit) {
    val ctx=LocalContext.current
    val store = remember { LauncherLayoutStore(ctx) }
    val gestures = remember { GestureSettings(ctx) }
    var folders by remember { mutableStateOf(store.folders()) }
    var selectedForFolder by remember { mutableStateOf<AppEntry?>(null) }
    var openedFolder by remember { mutableStateOf<LauncherLayoutStore.Folder?>(null) }
    var folderName by remember { mutableStateOf("Folder") }
    var showFolderName by remember { mutableStateOf(false) }
    val membership = remember(folders, apps) { store.entries().associate { it.packageName to it.folderId } }
    val visibleApps = apps.filter { membership[it.pkg] == null }
    fun longPressApp(app: AppEntry) {
        val first = selectedForFolder
        if (first == null) {
            selectedForFolder = app
        } else if (first.pkg != app.pkg) {
            val id = java.util.UUID.randomUUID().toString()
            val nextFolder = LauncherLayoutStore.Folder(id, "Folder", 0, folders.size)
            val oldEntries = store.entries().filterNot { it.packageName == first.pkg || it.packageName == app.pkg }
            store.saveEntries(oldEntries + listOf(
                LauncherLayoutStore.Entry(first.pkg, first.pkg, first.name, folderId=id),
                LauncherLayoutStore.Entry(app.pkg, app.pkg, app.name, folderId=id)
            ))
            folders = folders + nextFolder
            store.saveFolders(folders)
            selectedForFolder = null
            folderName = "Folder"
            openedFolder = nextFolder
            showFolderName = true
        }
    }
    var dragDistance by remember { mutableFloatStateOf(0f) }
    Column(Modifier.fillMaxSize()
        .pointerInput(onAll,onSettings) {
            detectVerticalDragGestures(onVerticalDrag={ change, amount -> dragDistance += amount; change.consume() }, onDragEnd={
                val action = if (dragDistance < -65f) gestures.actionFor(GestureSettings.Gesture.SWIPE_UP) else if (dragDistance > 65f) gestures.actionFor(GestureSettings.Gesture.SWIPE_DOWN) else GestureSettings.Action.NONE
                when(action) { GestureSettings.Action.OPEN_APP_DRAWER, GestureSettings.Action.OPEN_SEARCH -> onAll(); GestureSettings.Action.OPEN_SETTINGS -> onSettings(); else -> Unit }
                dragDistance = 0f
            })
        }
        .pointerInput(onAll,onSettings) {
            detectTapGestures(onDoubleTap={
                when(gestures.actionFor(GestureSettings.Gesture.DOUBLE_TAP_HOME)) {
                    GestureSettings.Action.OPEN_APP_DRAWER, GestureSettings.Action.OPEN_SEARCH -> onAll()
                    GestureSettings.Action.OPEN_SETTINGS -> onSettings()
                    else -> Unit
                }
            })
        }) {
        Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween,verticalAlignment=Alignment.CenterVertically) {
            Text("Home",color=Color.White,fontSize=21.sp,fontWeight=FontWeight.SemiBold)
            Text("All apps  →",color=Color(0xFFB9D9FF),modifier=Modifier.clickable{onAll()})
        }
        Spacer(Modifier.height(12.dp))
        Row(horizontalArrangement=Arrangement.spacedBy(10.dp)) {
            GlassTile("Weather","Add a real Android widget in Widgets","☀",Modifier.weight(1f))
            GlassTile("Calendar",SimpleDateFormat("EEE, d MMM",Locale.getDefault()).format(Date()),"▦",Modifier.weight(1f))
        }
        Spacer(Modifier.height(15.dp))
        Text("Pinned apps",color=Color.White.copy(.8f),fontSize=13.sp)
        if (selectedForFolder != null) {
            Text("Selected: ${selectedForFolder!!.name} • hold another app to create a folder",color=Color(0xFFB9D9FF),fontSize=11.sp)
        } else {
            Text("Hold two apps in sequence to group them into a folder.",color=Color.White.copy(.5f),fontSize=10.sp)
        }
        Spacer(Modifier.height(8.dp))
        if (folders.isNotEmpty()) {
            Row(horizontalArrangement=Arrangement.spacedBy(9.dp)) {
                folders.forEach { folder ->
                    Column(
                        Modifier.weight(1f).clip(RoundedCornerShape(17.dp)).background(Color.White.copy(alpha.coerceIn(.05f,.45f)))
                            .clickable { openedFolder = folder }.padding(10.dp),
                        horizontalAlignment=Alignment.CenterHorizontally
                    ) {
                        Text("▦",color=Color.White,fontSize=24.sp)
                        Text(folder.title,color=Color.White,fontSize=11.sp,maxLines=1)
                        Text("${store.entries().count { it.folderId == folder.id }} apps",color=Color.White.copy(.55f),fontSize=9.sp)
                    }
                }
            }
            Spacer(Modifier.height(10.dp))
        }
        LazyVerticalGrid(columns=GridCells.Fixed(cols),modifier=Modifier.heightIn(max=330.dp),contentPadding=PaddingValues(bottom=8.dp),horizontalArrangement=Arrangement.spacedBy(9.dp),verticalArrangement=Arrangement.spacedBy(13.dp)) {
            items(visibleApps.take(24),key={it.pkg}) { AppIcon(it, onLongClick={ longPressApp(it) }) }
        }
    }
    if (showFolderName && openedFolder != null) {
        AlertDialog(
            onDismissRequest={showFolderName=false},
            title={Text("Name folder")},
            text={ BasicTextField(value=folderName,onValueChange={folderName=it},singleLine=true) },
            confirmButton={ TextButton(onClick={
                val target=openedFolder!!
                folders=folders.map { if(it.id==target.id) it.copy(title=folderName.ifBlank{"Folder"}) else it }
                store.saveFolders(folders)
                openedFolder=folders.firstOrNull{it.id==target.id}
                showFolderName=false
            }) { Text("Save") } },
            dismissButton={ TextButton(onClick={showFolderName=false}) { Text("Cancel") } }
        )
    }
    openedFolder?.takeIf { !showFolderName }?.let { folder ->
        val folderApps=store.entries().filter { it.folderId==folder.id }.mapNotNull { entry -> apps.firstOrNull{it.pkg==entry.packageName} }
        AlertDialog(
            onDismissRequest={openedFolder=null},
            title={Text(folder.title)},
            text={
                Column(verticalArrangement=Arrangement.spacedBy(7.dp)) {
                    folderApps.forEach { app ->
                        TextButton(onClick={ctx.packageManager.getLaunchIntentForPackage(app.pkg)?.let(ctx::startActivity)}) {
                            Text(app.name)
                        }
                    }
                    if(folderApps.isEmpty()) Text("No installed apps in this folder.")
                }
            },
            confirmButton={TextButton(onClick={openedFolder=null}) { Text("Close") }},
            dismissButton={TextButton(onClick={
                store.saveEntries(store.entries().filterNot{it.folderId==folder.id})
                folders=folders.filterNot{it.id==folder.id}
                store.saveFolders(folders)
                openedFolder=null
            }) { Text("Delete folder") }}
        )
    }
}
@Composable private fun AppsPage(apps:List<AppEntry>,query:String,onQuery:(String)->Unit) {
    Column {
        Text("App Library",color=Color.White,fontSize=25.sp,fontWeight=FontWeight.Bold)
        Spacer(Modifier.height(10.dp))
        GlassInput(query,onQuery,"Search installed apps")
        Spacer(Modifier.height(10.dp))
        LazyVerticalGrid(columns=GridCells.Fixed(4),modifier=Modifier.weight(1f),contentPadding=PaddingValues(bottom=12.dp),horizontalArrangement=Arrangement.spacedBy(8.dp),verticalArrangement=Arrangement.spacedBy(14.dp)) { items(apps,key={it.pkg}){AppIcon(it)} }
    }
}
@OptIn(androidx.compose.foundation.ExperimentalFoundationApi::class)\n@Composable private fun AppIcon(app:AppEntry,onLongClick:()->Unit = {}) {
    val ctx=LocalContext.current
    Column(horizontalAlignment=Alignment.CenterHorizontally,modifier=Modifier.clickable {
        ctx.packageManager.getLaunchIntentForPackage(app.pkg)?.let{ctx.startActivity(it)}
    }) {
        Surface(shape=RoundedCornerShape(19.dp),color=glass,modifier=Modifier.size(57.dp)) {
            ImageIcon(app.icon,app.name)
        }
        Spacer(Modifier.height(4.dp))
        Text(app.name,color=Color.White,fontSize=10.sp,maxLines=1)
    }
}
@Composable private fun ImageIcon(icon:android.graphics.drawable.Drawable,label:String) {
    AndroidView(
        modifier = Modifier.padding(9.dp).fillMaxSize(),
        factory = { context -> android.widget.ImageView(context).apply {
            setImageDrawable(icon.constantState?.newDrawable(context.resources)?.mutate() ?: icon)
            contentDescription = label
            scaleType = android.widget.ImageView.ScaleType.FIT_CENTER
        } },
        update = { view ->
            view.setImageDrawable(icon.constantState?.newDrawable(view.resources)?.mutate() ?: icon)
            view.contentDescription = label
        }
    )
}
@Composable private fun GlassTile(title:String,sub:String,symbol:String,modifier:Modifier=Modifier) {
    Column(modifier.clip(RoundedCornerShape(22.dp)).background(glass).padding(14.dp)) {
        Text(symbol,color=Color.White,fontSize=23.sp)
        Text(title,color=Color.White,fontWeight=FontWeight.SemiBold)
        Text(sub,color=Color.White.copy(.65f),fontSize=11.sp)
    }
}
@Composable private fun WidgetsPage(controller: LauncherWidgetController) {
    val ctx = LocalContext.current
    val prefs = remember { ctx.getSharedPreferences("widget_host_v1", 0) }
    val activeIds = remember {
        mutableStateListOf<Int>().apply {
            addAll(prefs.getStringSet("active_widget_ids", emptySet())!!.mapNotNull { it.toIntOrNull() })
        }
    }
    var providers by remember { mutableStateOf(controller.installedProviders()) }
    var pendingId by remember { mutableIntStateOf(-1) }
    fun persistIds() {
        prefs.edit().putStringSet("active_widget_ids", activeIds.map { it.toString() }.toSet()).apply()
    }
    val bindLauncher = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == android.app.Activity.RESULT_OK && pendingId >= 0) {
            if (!activeIds.contains(pendingId)) activeIds.add(pendingId)
            persistIds()
        } else if (pendingId >= 0) {
            controller.deleteWidget(pendingId)
        }
        pendingId = -1
    }
    Column(Modifier.fillMaxSize()) {
        Text("Stacked Android Widgets", color=Color.White, fontSize=24.sp, fontWeight=FontWeight.Bold)
        Text("Add multiple real Android widgets and keep them together in this scrollable stack.", color=Color.White.copy(.65f), fontSize=12.sp)
        Spacer(Modifier.height(9.dp))
        if (activeIds.isEmpty()) {
            Text("No widgets added yet.", color=Color.White.copy(.7f))
        } else {
            androidx.compose.foundation.lazy.LazyColumn(
                modifier=Modifier.weight(1f).fillMaxWidth(),
                verticalArrangement=Arrangement.spacedBy(9.dp),
                contentPadding=PaddingValues(vertical=5.dp)
            ) {
                items(activeIds.toList(), key={it}) { widgetId ->
                    val hostView = remember(widgetId) { controller.createView(widgetId) }
                    Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(17.dp)).background(Color.White.copy(.09f)).padding(8.dp)) {
                        if (hostView != null) {
                            AndroidView(factory={ hostView }, modifier=Modifier.fillMaxWidth().heightIn(min=90.dp, max=330.dp))
                        } else {
                            Text("Widget $widgetId is unavailable.", color=Color.White.copy(.7f))
                        }
                        OutlinedButton(onClick={
                            controller.deleteWidget(widgetId)
                            activeIds.remove(widgetId)
                            persistIds()
                        }, modifier=Modifier.align(Alignment.End)) { Text("Remove") }
                    }
                }
            }
        }
        Spacer(Modifier.height(7.dp))
        Text("Available widget providers", color=Color.White, fontWeight=FontWeight.SemiBold)
        androidx.compose.foundation.lazy.LazyColumn(
            modifier=Modifier.weight(1f),
            verticalArrangement=Arrangement.spacedBy(6.dp)
        ) {
            items(providers, key={ it.provider.flattenToString() }) { info ->
                Row(
                    Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).background(glass).padding(10.dp),
                    verticalAlignment=Alignment.CenterVertically
                ) {
                    Column(Modifier.weight(1f)) {
                        Text(info.loadLabel(ctx.packageManager), color=Color.White)
                        Text(info.provider.packageName, color=Color.White.copy(.55f), fontSize=10.sp)
                    }
                    Button(onClick={
                        val id = controller.allocateId()
                        pendingId = id
                        val intent = controller.bindIntent(id, info.provider)
                        if (intent == null) {
                            activeIds.add(id)
                            persistIds()
                            pendingId = -1
                        } else bindLauncher.launch(intent)
                    }) { Text("Add") }
                }
            }
        }
        if (providers.isEmpty()) Text("No widget providers were found on this device.", color=Color.White.copy(.65f))
        OutlinedButton(onClick={ providers = controller.installedProviders() }, modifier=Modifier.fillMaxWidth()) {
            Text("Refresh providers")
        }
    }
}
@Composable private fun ThemesPage(current:String,onChoose:(String)->Unit) {
    Column {
        Text("Theme Store",color=Color.White,fontSize=25.sp,fontWeight=FontWeight.Bold)
        Text("Built-in theme collection • more online packs can be added",color=Color.White.copy(.65f),fontSize=12.sp)
        Spacer(Modifier.height(14.dp))
        listOf("Midnight Glass","Snow Glass","Ocean","Aurora").forEach { name->
            Row(Modifier.fillMaxWidth().padding(vertical=5.dp).clip(RoundedCornerShape(20.dp)).background(glass).clickable{onChoose(name)}.padding(15.dp),verticalAlignment=Alignment.CenterVertically) {
                Box(Modifier.size(38.dp).clip(CircleShape).background(Brush.linearGradient(listOf(Color(0xFF7CB5D9),Color(0xFF302D58)))))
                Spacer(Modifier.width(12.dp))
                Text(name,color=Color.White,modifier=Modifier.weight(1f))
                if(current==name) Icon(Icons.Default.Check,color=Color(0xFFB9D9FF),contentDescription="Applied")
            }
        }
        Text("Only built-in themes are currently applied. Imported theme-pack application, icon packs, font packs and wallpaper packs are not implemented yet.",color=Color.White.copy(.6f),fontSize=11.sp)
    }
}
@Composable private fun SettingsPage(blur:Float,onBlur:(Float)->Unit,alpha:Float,onAlpha:(Float)->Unit,cols:Int,onCols:(Int)->Unit,endpoint:String,onEndpoint:(String)->Unit,model:String,onModel:(String)->Unit,key:String,onKey:(String)->Unit,onAccount:()->Unit) {
    val context = LocalContext.current
    var backupMessage by remember { mutableStateOf("") }
    val backupManager = remember { LauncherBackupManager(context) }
    val themeManager = remember { ThemePackManager(context) }
    val exportBackup = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { uri ->
        if (uri != null) backupMessage = backupManager.exportTo(uri).fold({ "Backup saved." }, { "Backup failed: ${it.message}" })
    }
    val importBackup = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) backupMessage = backupManager.restoreFrom(uri).fold({ "Backup restored. Restart launcher to refresh all screens." }, { "Restore failed: ${it.message}" })
    }
    val importTheme = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) backupMessage = themeManager.import(uri).fold({ "Theme imported: ${it.name}" }, { "Theme import failed: ${it.message}" })
    }
    Column(Modifier.fillMaxSize()) {
        Text("Settings",color=Color.White,fontSize=26.sp,fontWeight=FontWeight.Bold)
        Spacer(Modifier.height(8.dp))
        Text("Appearance & Liquid Glass",color=Color.White,fontWeight=FontWeight.SemiBold)
        Text("Blur amount: ${blur.toInt()}",color=Color.White.copy(.7f));Slider(value=blur,onValueChange=onBlur,valueRange=0f..28f)
        Text("Glass opacity: ${(alpha*100).toInt()}%",color=Color.White.copy(.7f));Slider(value=alpha,onValueChange=onAlpha,valueRange=.05f..0.75f)
        Text("Home grid columns: $cols",color=Color.White.copy(.7f));Slider(value=cols.toFloat(),onValueChange={onCols(it.toInt().coerceIn(3,6))},valueRange=3f..6f,steps=2)
        HorizontalDivider(color=Color.White.copy(.18f),modifier=Modifier.padding(vertical=9.dp))
        Text("Home gestures",color=Color.White,fontWeight=FontWeight.SemiBold)
        GestureSettingRow("Double tap",GestureSettings.Gesture.DOUBLE_TAP_HOME,context)
        GestureSettingRow("Swipe up",GestureSettings.Gesture.SWIPE_UP,context)
        GestureSettingRow("Swipe down",GestureSettings.Gesture.SWIPE_DOWN,context)
        Text("Supported actions: open app drawer, search, or settings. Notification shade and quick settings require system privileges and are not exposed by a normal launcher.",color=Color.White.copy(.58f),fontSize=10.sp)
        HorizontalDivider(color=Color.White.copy(.18f),modifier=Modifier.padding(vertical=9.dp))
        Text("Mi_Max AI connection",color=Color.White,fontWeight=FontWeight.SemiBold)
        GlassInput(endpoint,onEndpoint,"AI API endpoint")
        Spacer(Modifier.height(7.dp));GlassInput(model,onModel,"Model ID")
        Spacer(Modifier.height(7.dp));GlassInput(key,onKey,"API key (stored locally)")
        Text("Requests use the configured OpenAI-compatible HTTPS endpoint and selected model.",color=Color.White.copy(.6f),fontSize=11.sp)
        Spacer(Modifier.height(9.dp))
        HorizontalDivider(color=Color.White.copy(.18f),modifier=Modifier.padding(vertical=9.dp))
        Text("Backup & themes",color=Color.White,fontWeight=FontWeight.SemiBold)
        Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
            OutlinedButton(onClick={ exportBackup.launch("Mi_Max_Launcher_Backup.json") },modifier=Modifier.weight(1f)) { Text("Export backup") }
            OutlinedButton(onClick={ importBackup.launch(arrayOf("application/json")) },modifier=Modifier.weight(1f)) { Text("Restore backup") }
        }
        OutlinedButton(onClick={ importTheme.launch(arrayOf("application/json")) },modifier=Modifier.fillMaxWidth()) { Text("Import theme pack") }
        if (backupMessage.isNotBlank()) Text(backupMessage,color=Color.White.copy(.75f),fontSize=11.sp)
        Button(onClick=onAccount,modifier=Modifier.fillMaxWidth()) { Icon(Icons.Default.Person,null);Spacer(Modifier.width(7.dp));Text("Developer • Account • About") }
    }
}
@Composable private fun GestureSettingRow(label:String,gesture:GestureSettings.Gesture,context:android.content.Context) {
    val settings = remember { GestureSettings(context) }
    var action by remember { mutableStateOf(settings.actionFor(gesture)) }
    var expanded by remember { mutableStateOf(false) }
    Row(Modifier.fillMaxWidth().padding(vertical=3.dp),verticalAlignment=Alignment.CenterVertically) {
        Text(label,color=Color.White,modifier=Modifier.weight(1f),fontSize=13.sp)
        Box {
            TextButton(onClick={expanded=true}) { Text(action.name.replace('_',' ').lowercase().replaceFirstChar{it.uppercase()}) }
            DropdownMenu(expanded=expanded,onDismissRequest={expanded=false}) {
                listOf(GestureSettings.Action.NONE,GestureSettings.Action.OPEN_APP_DRAWER,GestureSettings.Action.OPEN_SEARCH,GestureSettings.Action.OPEN_SETTINGS).forEach { option ->
                    DropdownMenuItem(text={Text(option.name.replace('_',' ').lowercase().replaceFirstChar{it.uppercase()})},onClick={
                        action=option
                        settings.setAction(gesture,option)
                        expanded=false
                    })
                }
            }
        }
    }
}
@Composable private fun GlassInput(value:String,onValue:(String)->Unit,hint:String) {
    Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).background(Color.White.copy(.12f)).padding(horizontal=12.dp,vertical=13.dp),verticalAlignment=Alignment.CenterVertically) {
        BasicTextField(value=value,onValueChange=onValue,singleLine=true,textStyle=androidx.compose.ui.text.TextStyle(color=Color.White,fontSize=14.sp),modifier=Modifier.weight(1f),decorationBox={inner->if(value.isEmpty())Text(hint,color=Color.White.copy(.48f),fontSize=13.sp);inner()})
    }
}
@Composable private fun AccountPage(back:()->Unit) {
    Column {
        Text("About & Account",color=Color.White,fontSize=25.sp,fontWeight=FontWeight.Bold)
        Spacer(Modifier.height(16.dp))
        GlassTile("Mi_Max Launcher","Version 1.0-alpha2 • com.mimax.lu","✦",Modifier.fillMaxWidth())
        Spacer(Modifier.height(15.dp))
        Text("Developer",color=Color.White.copy(.6f))
        Text("محمد السعيد علي",color=Color.White,fontSize=18.sp,fontWeight=FontWeight.SemiBold)
        Text("mmgg3yn@gmail.com",color=Color.White)
        Text("Telegram: @Mi_Max12",color=Color.White)
        Spacer(Modifier.height(16.dp))
        Text("Account",color=Color.White.copy(.6f))
        Text("Local profile • cloud sign-in and sync not yet connected.",color=Color.White)
        Spacer(Modifier.height(18.dp))
        OutlinedButton(onClick=back){Text("Back")}
    }
}
@Composable private fun AccountDialog(onDismiss:()->Unit) {
    AlertDialog(onDismissRequest=onDismiss,title={Text("Mi_Max account")},text={Text("Account profile is local in this alpha. Cloud account sign-in is not yet connected.")},confirmButton={TextButton(onClick=onDismiss){Text("OK")}})
}
