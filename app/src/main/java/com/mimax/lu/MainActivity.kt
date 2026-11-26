package com.mimax.lu

import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.tween
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.painter.DrawablePainter
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private val glass = Color.White.copy(alpha = .13f)
private data class AppEntry(val name:String,val pkg:String,val icon:android.graphics.drawable.Drawable)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MiMaxLauncher() }
    }
}

@Composable
private fun MiMaxLauncher() {
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
                        "widgets" -> WidgetsPage()
                        "themes" -> ThemesPage(theme,{theme=it;save("theme",it)})
                        "settings" -> SettingsPage(blur,{blur=it;save("blur",it)},opacity,{opacity=it;save("opacity",it)},columns,{columns=it;save("columns",it)},endpoint,{endpoint=it;save("ai_endpoint",it)},model,{model=it;save("ai_model",it)},apiKey,{apiKey=it;save("ai_key",it)},{showAccount=true})
                        "account" -> AccountPage { showAccount=false;tab="settings" }
                        else -> HomePage(apps,columns,opacity,{tab="apps"})
                    }
                }
                Spacer(Modifier.weight(1f))
                NavigationBar(containerColor=Color.White.copy(opacity),tonalElevation=0.dp) {
                    listOf(Triple("home","Home",Icons.Default.Home),Triple("apps","Apps",Icons.Default.Apps),Triple("widgets","Widgets",Icons.Default.Widgets),Triple("themes","Themes",Icons.Default.Palette),Triple("settings","Settings",Icons.Default.Settings)).forEach { (id,label,ic) ->
                        NavigationBarItem(selected=tab==id,onClick={tab=id},icon={Icon(ic,null)},label={Text(label,fontSize=10.sp)})
                    }
                }
                Spacer(Modifier.height(9.dp))
            }
        }
        if(showAccount) AccountDialog(onDismiss={showAccount=false})
    }
}

@Composable private fun HomePage(apps:List<AppEntry>,cols:Int,alpha:Float,onAll:()->Unit) {
    val ctx=LocalContext.current
    Column {
        Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween,verticalAlignment=Alignment.CenterVertically) {
            Text("Home",color=Color.White,fontSize=21.sp,fontWeight=FontWeight.SemiBold)
            Text("All apps  →",color=Color(0xFFB9D9FF),modifier=Modifier.clickable{onAll()})
        }
        Spacer(Modifier.height(12.dp))
        Row(horizontalArrangement=Arrangement.spacedBy(10.dp)) {
            GlassTile("Weather","Widget preview","☀",Modifier.weight(1f))
            GlassTile("Calendar",SimpleDateFormat("EEE, d MMM",Locale.getDefault()).format(Date()),"▦",Modifier.weight(1f))
        }
        Spacer(Modifier.height(15.dp))
        Text("Pinned apps",color=Color.White.copy(.8f),fontSize=13.sp)
        Spacer(Modifier.height(8.dp))
        LazyVerticalGrid(columns=GridCells.Fixed(cols),modifier=Modifier.heightIn(max=330.dp),contentPadding=PaddingValues(bottom=8.dp),horizontalArrangement=Arrangement.spacedBy(9.dp),verticalArrangement=Arrangement.spacedBy(13.dp)) {
            items(apps.take(16),key={it.pkg}) { AppIcon(it) }
        }
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
@Composable private fun AppIcon(app:AppEntry) {
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
    androidx.compose.foundation.Image(painter=DrawablePainter(icon),contentDescription=label,modifier=Modifier.padding(9.dp).fillMaxSize())
}
@Composable private fun GlassTile(title:String,sub:String,symbol:String,modifier:Modifier=Modifier) {
    Column(modifier.clip(RoundedCornerShape(22.dp)).background(glass).padding(14.dp)) {
        Text(symbol,color=Color.White,fontSize=23.sp)
        Text(title,color=Color.White,fontWeight=FontWeight.SemiBold)
        Text(sub,color=Color.White.copy(.65f),fontSize=11.sp)
    }
}
@Composable private fun WidgetsPage() {
    var selected by remember{mutableIntStateOf(0)}
    Column {
        Text("Widget Stack Studio",color=Color.White,fontSize=24.sp,fontWeight=FontWeight.Bold)
        Text("Stacked widget layout concept and configuration",color=Color.White.copy(.65f),fontSize=12.sp)
        Spacer(Modifier.height(14.dp))
        listOf("Weather","Calendar","Clock","Battery").forEachIndexed{i,name->
            Row(Modifier.fillMaxWidth().padding(vertical=5.dp).clip(RoundedCornerShape(18.dp)).background(glass).clickable{selected=i}.padding(15.dp),verticalAlignment=Alignment.CenterVertically) {
                Text(name,color=Color.White,modifier=Modifier.weight(1f))
                if(selected==i) Icon(Icons.Default.Check,color=Color(0xFFB9D9FF),contentDescription="Selected")
                else Icon(Icons.Default.Add,color=Color.White,contentDescription="Add to stack")
            }
        }
        Spacer(Modifier.height(12.dp))
        Text("Selected stack card: ${listOf("Weather","Calendar","Clock","Battery")[selected]}",color=Color.White)
        Text("Full Android AppWidgetHost stacking and resize integration is a separate native implementation step.",color=Color.White.copy(.6f),fontSize=11.sp)
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
        Text("Theme packs, icon packs, fonts and wallpapers can be imported in the next store module.",color=Color.White.copy(.6f),fontSize=11.sp)
    }
}
@Composable private fun SettingsPage(blur:Float,onBlur:(Float)->Unit,alpha:Float,onAlpha:(Float)->Unit,cols:Int,onCols:(Int)->Unit,endpoint:String,onEndpoint:(String)->Unit,model:String,onModel:(String)->Unit,key:String,onKey:(String)->Unit,onAccount:()->Unit) {
    Column(Modifier.fillMaxSize()) {
        Text("Settings",color=Color.White,fontSize=26.sp,fontWeight=FontWeight.Bold)
        Spacer(Modifier.height(8.dp))
        Text("Appearance & Liquid Glass",color=Color.White,fontWeight=FontWeight.SemiBold)
        Text("Blur amount: ${blur.toInt()}",color=Color.White.copy(.7f));Slider(value=blur,onValueChange=onBlur,valueRange=0f..28f)
        Text("Glass opacity: ${(alpha*100).toInt()}%",color=Color.White.copy(.7f));Slider(value=alpha,onValueChange=onAlpha,valueRange=.05f..0.75f)
        Text("Home grid columns: $cols",color=Color.White.copy(.7f));Slider(value=cols.toFloat(),onValueChange={onCols(it.toInt().coerceIn(3,6))},valueRange=3f..6f,steps=2)
        HorizontalDivider(color=Color.White.copy(.18f),modifier=Modifier.padding(vertical=9.dp))
        Text("Mi_Max AI connection",color=Color.White,fontWeight=FontWeight.SemiBold)
        GlassInput(endpoint,onEndpoint,"AI API endpoint")
        Spacer(Modifier.height(7.dp));GlassInput(model,onModel,"Model ID")
        Spacer(Modifier.height(7.dp));GlassInput(key,onKey,"API key (stored locally)")
        Text("This stores connection details; live AI chat/API validation is not yet wired in this build.",color=Color.White.copy(.6f),fontSize=11.sp)
        Spacer(Modifier.height(9.dp))
        Button(onClick=onAccount,modifier=Modifier.fillMaxWidth()) { Icon(Icons.Default.Person,null);Spacer(Modifier.width(7.dp));Text("Developer • Account • About") }
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
