from pathlib import Path
import shutil

def replace_once(path, old, new, label):
    p = Path(path)
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise SystemExit("Missing patch marker: " + label)
    p.write_text(text.replace(old, new, 1))

# Identity, universal ABIs, and About attribution.
gradle = Path("app/build.gradle")
source = gradle.read_text()
replacements = [
    ('applicationId "com.benny.openlauncher"', 'applicationId "com.mimax.launcher"'),
    ('resValue \'string\', \'app_name\', "OpenLauncher"', 'resValue \'string\', \'app_name\', "Mi_Max Launcher"'),
    ('resValue "string", "manifest_package_id", "com.benny.openlauncher"', 'resValue "string", "manifest_package_id", "com.mimax.launcher"'),
    ('versionCode 37', 'versionCode 38'),
    ('versionName "0.6.1"', 'versionName "1.0.0-mimax.1"'),
]
for old, new in replacements:
    if old in source:
        source = source.replace(old, new, 1)
    elif new not in source:
        raise SystemExit("Expected Gradle marker not found: " + old)
marker = "        multiDexEnabled false"
if 'abiFilters "armeabi-v7a", "arm64-v8a"' not in source:
    if marker not in source:
        raise SystemExit("Could not locate defaultConfig ABI insertion point")
    source = source.replace(marker, marker + '\n\n        // Universal Mi_Max APK for ARMv7 and ARM64.\n        ndk { abiFilters "armeabi-v7a", "arm64-v8a" }', 1)
source = source.replace(
    "        release {\n            minifyEnabled false",
    "        release {\n            signingConfig signingConfigs.debug\n            minifyEnabled false",
    1
)
gradle.write_text(source)
settings = Path("settings.gradle")
settings.write_text(settings.read_text().replace('rootProject.name = "OpenLauncher"', 'rootProject.name = "Mi_Max Launcher"'))

strings = Path("app/src/main/res/values/strings.xml")
s = strings.read_text()
if 'name="mimax_developer_title"' not in s:
    s = s.replace("</resources>", """    <string name="mimax_developer_title">Mi_Max Developer</string>
    <string name="mimax_developer_summary">محمد السعيد علي&#10;mmgg3yn@gmail.com&#10;Telegram: @Mi_Max12</string>
    <string name="mimax_island_settings">Me Island</string>
    <string name="mimax_island_summary">Live activity capsule overlay and timer</string>
</resources>""", 1)
strings.write_text(s)

about = Path("app/src/main/res/xml/preferences_about.xml")
s = about.read_text()
if 'mimax_developer_title' not in s:
    marker = '    </PreferenceCategory>\n\n    <PreferenceCategory'
    if marker not in s:
        raise SystemExit("Could not find About category insertion point")
    s = s.replace(marker, """        <Preference
            android:icon="@drawable/ic_info_black_24dp"
            android:title="@string/mimax_developer_title"
            android:summary="@string/mimax_developer_summary" />
\n    </PreferenceCategory>\n\n    <PreferenceCategory""", 1)
about.write_text(s)

# Add a real overlay permission-gated Me Island foreground service and settings entry.
src = Path("app/src/main/java/com/benny/openlauncher/mimax")
src.mkdir(parents=True, exist_ok=True)
(src / "MeIslandService.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.provider.Settings;
import android.view.Gravity;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.TextView;
import android.graphics.drawable.GradientDrawable;
import java.util.Locale;

public final class MeIslandService extends Service {
    public static final String ACTION_START_TIMER = "com.mimax.launcher.action.START_TIMER";
    public static final String ACTION_STOP = "com.mimax.launcher.action.STOP";
    public static final String EXTRA_DURATION = "duration_ms";
    private static final String CHANNEL = "mimax_island";
    private final Handler handler = new Handler();
    private WindowManager windowManager;
    private FrameLayout capsule;
    private TextView label;
    private long endsAt;
    private boolean expanded;

    private final Runnable ticker = new Runnable() {
        @Override public void run() {
            if (label == null) return;
            long remaining = Math.max(0L, endsAt - System.currentTimeMillis());
            long seconds = (remaining + 999L) / 1000L;
            label.setText(String.format(Locale.getDefault(), expanded ? "Timer  %02d:%02d  ·  Mi_Max" : "◷  %02d:%02d",
                    seconds / 60L, seconds % 60L));
            if (remaining == 0L) {
                label.setText("Timer finished");
                handler.postDelayed(() -> stopSelf(), 2500L);
            } else {
                handler.postDelayed(this, 500L);
            }
        }
    };

    @Override public void onCreate() {
        super.onCreate();
        windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);
        createChannel();
        startForeground(4107, buildNotification("Me Island is ready"));
    }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_STOP.equals(intent.getAction())) {
            removeCapsule();
            stopForeground(true);
            stopSelf();
            return START_NOT_STICKY;
        }
        if (intent != null && ACTION_START_TIMER.equals(intent.getAction())) {
            long duration = Math.max(1000L, Math.min(24L * 60L * 60L * 1000L,
                    intent.getLongExtra(EXTRA_DURATION, 60000L)));
            endsAt = System.currentTimeMillis() + duration;
            showCapsule();
            handler.removeCallbacks(ticker);
            handler.post(ticker);
            updateNotification("Timer running");
        }
        return START_STICKY;
    }

    private void showCapsule() {
        if (Build.VERSION.SDK_INT >= 23 && !Settings.canDrawOverlays(this)) return;
        if (capsule == null) {
            capsule = new FrameLayout(this);
            GradientDrawable bg = new GradientDrawable();
            bg.setColor(Color.rgb(12, 13, 17));
            bg.setCornerRadius(dp(28));
            bg.setStroke(dp(1), Color.rgb(65, 68, 78));
            capsule.setBackground(bg);
            label = new TextView(this);
            label.setTextColor(Color.WHITE);
            label.setTextSize(13);
            label.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
            label.setGravity(Gravity.CENTER);
            capsule.addView(label, new FrameLayout.LayoutParams(-1, -1));
            capsule.setPadding(dp(16), 0, dp(16), 0);
            capsule.setOnClickListener(v -> {
                expanded = !expanded;
                if (label != null) ticker.run();
                resizeCapsule();
            });
        }
        if (capsule.getParent() == null) {
            WindowManager.LayoutParams p = new WindowManager.LayoutParams(
                    dp(expanded ? 250 : 150), dp(42),
                    Build.VERSION.SDK_INT >= 26 ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                            : WindowManager.LayoutParams.TYPE_PHONE,
                    WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                            | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
                            | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
                    PixelFormat.TRANSLUCENT);
            p.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL;
            p.y = dp(8);
            try { windowManager.addView(capsule, p); } catch (RuntimeException ignored) { }
        }
    }

    private void resizeCapsule() {
        if (capsule == null || capsule.getParent() == null) return;
        WindowManager.LayoutParams p = (WindowManager.LayoutParams) capsule.getLayoutParams();
        p.width = dp(expanded ? 250 : 150);
        p.height = dp(expanded ? 48 : 42);
        try { windowManager.updateViewLayout(capsule, p); } catch (RuntimeException ignored) { }
    }

    private void removeCapsule() {
        handler.removeCallbacks(ticker);
        if (capsule != null && capsule.getParent() != null) {
            try { windowManager.removeView(capsule); } catch (RuntimeException ignored) { }
        }
        capsule = null;
        label = null;
    }

    private void createChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(CHANNEL, "Me Island", NotificationManager.IMPORTANCE_LOW);
            channel.setDescription("Keeps live activity overlay available while enabled");
            ((NotificationManager) getSystemService(NOTIFICATION_SERVICE)).createNotificationChannel(channel);
        }
    }

    private Notification buildNotification(String text) {
        Intent open = new Intent(this, MeIslandSettingsActivity.class);
        PendingIntent pi = PendingIntent.getActivity(this, 0, open,
                PendingIntent.FLAG_UPDATE_CURRENT | (Build.VERSION.SDK_INT >= 23 ? PendingIntent.FLAG_IMMUTABLE : 0));
        Notification.Builder b = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, CHANNEL) : new Notification.Builder(this);
        return b.setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle("Mi_Max Me Island").setContentText(text)
                .setContentIntent(pi).setOngoing(true).build();
    }

    private void updateNotification(String text) {
        ((NotificationManager) getSystemService(NOTIFICATION_SERVICE)).notify(4107, buildNotification(text));
    }

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }

    @Override public void onDestroy() {
        removeCapsule();
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent intent) { return null; }
}
''')

(src / "MeIslandSettingsActivity.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public final class MeIslandSettingsActivity extends Activity {
    private static final int REQUEST_OVERLAY = 7321;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(22), dp(24), dp(22), dp(22));
        TextView title = new TextView(this);
        title.setText("Mi_Max Me Island");
        title.setTextSize(23);
        title.setGravity(Gravity.CENTER_VERTICAL);
        root.addView(title);
        TextView info = new TextView(this);
        info.setText("A floating live-activity capsule. Android requires you to grant display-over-other-apps permission before it can appear above other apps.");
        info.setTextSize(15);
        info.setPadding(0, dp(14), 0, dp(20));
        root.addView(info);
        Button permission = new Button(this);
        permission.setText("Grant overlay permission");
        permission.setOnClickListener(v -> requestOverlay());
        root.addView(permission);
        Button timer = new Button(this);
        timer.setText("Start 1-minute timer in Me Island");
        timer.setOnClickListener(v -> {
            if (Build.VERSION.SDK_INT >= 23 && !Settings.canDrawOverlays(this)) { requestOverlay(); return; }
            Intent service = new Intent(this, MeIslandService.class);
            service.setAction(MeIslandService.ACTION_START_TIMER);
            service.putExtra(MeIslandService.EXTRA_DURATION, 60000L);
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(service); else startService(service);
            finish();
        });
        root.addView(timer);
        Button stop = new Button(this);
        stop.setText("Stop Me Island");
        stop.setOnClickListener(v -> {
            Intent service = new Intent(this, MeIslandService.class);
            service.setAction(MeIslandService.ACTION_STOP);
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(service); else startService(service);
        });
        root.addView(stop);
        setContentView(root);
    }

    private void requestOverlay() {
        if (Build.VERSION.SDK_INT >= 23 && !Settings.canDrawOverlays(this)) {
            Intent i = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:" + getPackageName()));
            startActivityForResult(i, REQUEST_OVERLAY);
        }
    }

    private int dp(int v) { return Math.round(v * getResources().getDisplayMetrics().density); }
}
''')

manifest = Path("app/src/main/AndroidManifest.xml")
m = manifest.read_text()
if "com.benny.openlauncher.mimax.MeIslandService" not in m:
    m = m.replace('<application', '''<uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

    <application''', 1)
    m = m.replace('</application>', '''        <activity
            android:name="com.benny.openlauncher.mimax.MeIslandSettingsActivity"
            android:exported="false"
            android:label="Mi_Max Me Island" />
        <service
            android:name="com.benny.openlauncher.mimax.MeIslandService"
            android:exported="false"
            android:foregroundServiceType="specialUse">
            <property
                android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE"
                android:value="User-enabled live activity overlay" />
        </service>
    </application>''', 1)
manifest.write_text(m)

master = Path("app/src/main/res/xml/preferences_master.xml")
m = master.read_text()
if "mimax_island_settings" not in m:
    marker = '        <PreferenceScreen\n            android:icon="@drawable/ic_info_outline_dark_24dp"'
    entry = '''        <Preference
            android:icon="@drawable/ic_info_outline_dark_24dp"
            android:title="@string/mimax_island_settings"
            android:summary="@string/mimax_island_summary">
            <intent android:targetPackage="com.mimax.launcher"
                android:targetClass="com.benny.openlauncher.mimax.MeIslandSettingsActivity" />
        </Preference>

'''
    if marker not in m:
        raise SystemExit("Could not find About preference insertion point")
    master.write_text(m.replace(marker, entry + marker, 1))

# Upstream About screen reads these files as raw resources.
raw_dir = Path("app/src/main/res/raw")
raw_dir.mkdir(parents=True, exist_ok=True)
for name in ["LICENSE", "CONTRIBUTORS.md", "CHANGELOG.md"]:
    if not Path(name).exists():
        raise SystemExit("Required upstream attribution file missing: " + name)
    shutil.copyfile(name, raw_dir / name.lower().replace(".md", ".md"))

# Android 12+ PendingIntent mutability.
context_utils = Path("app/src/main/java/net/gsantner/opoc/util/ContextUtils.java")
s = context_utils.read_text()
old = "PendingIntent.FLAG_CANCEL_CURRENT);"
new = "PendingIntent.FLAG_CANCEL_CURRENT | PendingIntent.FLAG_IMMUTABLE);"
if old in s:
    context_utils.write_text(s.replace(old, new, 1))

print("Mi_Max identity + ARM32/ARM64 + developer page + functional permission-gated Me Island timer overlay applied.")


# Mi_Max extension packages: declarative-only, path-safe install, compatibility checks,
# per-extension error logs, and last-known-good rollback. No extension bytecode is executed.
extensions = Path("app/src/main/java/com/benny/openlauncher/mimax/extensions")
extensions.mkdir(parents=True, exist_ok=True)
(extensions / "ExtensionRegistry.java").write_text(r'''package com.benny.openlauncher.mimax.extensions;

import android.content.Context;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.*;
import java.util.*;
import java.util.zip.*;

public final class ExtensionRegistry {
    private final File root;
    public ExtensionRegistry(Context context) {
        root = new File(context.getFilesDir(), "mimax-extensions");
        if (!root.exists()) root.mkdirs();
    }
    public static final class Entry {
        public final String id, name, version;
        public final int minApi;
        public final List<String> permissions, dependencies;
        Entry(JSONObject j) throws Exception {
            id=j.getString("id"); name=j.getString("name"); version=j.getString("version");
            minApi=j.optInt("minApi",21); permissions=new ArrayList<>(); dependencies=new ArrayList<>();
            JSONArray a=j.optJSONArray("permissions");
            if(a!=null) for(int i=0;i<a.length();i++) {
                String permission=a.getString(i);
                if(!Arrays.asList("island.layout","island.animation","island.activities","island.assets","launcher.shortcuts").contains(permission))
                    throw new SecurityException("Unsupported extension permission: "+permission);
                if(!permissions.contains(permission))permissions.add(permission);
            }
            JSONArray d=j.optJSONArray("dependencies");
            if(d!=null) for(int i=0;i<d.length();i++) {
                String dependency=d.getString(i);
                if(!dependency.matches("[A-Za-z0-9_.-]{3,80}") || dependency.equals(id))
                    throw new SecurityException("Invalid extension dependency");
                dependencies.add(dependency);
            }
            if(!id.matches("[A-Za-z0-9_.-]{3,80}") || name.trim().isEmpty() || name.length()>80 || version.trim().isEmpty())
                throw new SecurityException("Invalid extension identity");
        }
    }
    public Entry install(InputStream archive, int sdk) throws Exception {
        File stage=new File(root,".staging-"+UUID.randomUUID()); stage.mkdirs();
        try(ZipInputStream zin=new ZipInputStream(archive)) {
            ZipEntry e; byte[] b=new byte[8192]; int entryCount=0; long totalBytes=0;
            while((e=zin.getNextEntry())!=null) {
                if(++entryCount>128) throw new IOException("Too many extension archive entries");
                String n=e.getName();
                if(n.startsWith("/") || n.contains("..") || n.contains("\\\\")) throw new SecurityException("Unsafe archive path");
                File out=new File(stage,n);
                if(!out.getCanonicalPath().startsWith(stage.getCanonicalPath()+File.separator)) throw new SecurityException("Path traversal");
                if(e.isDirectory()) out.mkdirs(); else {
                    out.getParentFile().mkdirs();
                    try(FileOutputStream os=new FileOutputStream(out)){
                        int k; while((k=zin.read(b))>0){ totalBytes+=k; if(totalBytes>4L*1024L*1024L) throw new IOException("Extension package exceeds 4 MB"); os.write(b,0,k); }
                    }
                }
            }
        }
        File mf=new File(stage,"manifest.json");
        if(!mf.isFile() || mf.length()>65536) throw new IOException("Missing or oversized manifest.json");
        byte[] bytes=new byte[(int)mf.length()];
        try(FileInputStream in=new FileInputStream(mf)){int n=in.read(bytes);if(n!=bytes.length)throw new IOException("Incomplete manifest");}
        Entry entry=new Entry(new JSONObject(new String(bytes,"UTF-8")));
        if(sdk<entry.minApi) throw new IllegalArgumentException("Android API is too old");
        File live=new File(root,entry.id), backup=new File(root,entry.id+".last-good");
        delete(backup);
        if(live.exists() && !live.renameTo(backup)) throw new IOException("Could not preserve previous extension");
        if(!stage.renameTo(live)){if(backup.exists())backup.renameTo(live);throw new IOException("Activation failed");}
        return entry;
    }
    private android.content.SharedPreferences state(Context c) { return c.getSharedPreferences("mimax_extension_state",Context.MODE_PRIVATE); }
    public Entry getEntry(File dir) throws Exception {
        File mf=new File(dir,"manifest.json");
        if(!mf.isFile()||mf.length()>65536)throw new IOException("Invalid extension manifest");
        byte[] b=new byte[(int)mf.length()];
        try(FileInputStream in=new FileInputStream(mf)){int n=in.read(b);if(n!=b.length)throw new IOException("Incomplete extension manifest");}
        return new Entry(new JSONObject(new String(b,"UTF-8")));
    }
    public boolean isEnabled(Context c,String id) { return state(c).getBoolean("enabled:"+id,false); }
    public boolean canEnable(Context c,Entry e) {
        for(String dependency:e.dependencies)if(!isEnabled(c,dependency))return false;
        return true;
    }
    public boolean enable(Context c,String id) throws Exception {
        File dir=new File(root,id); Entry e=getEntry(dir);
        if(!canEnable(c,e))throw new IllegalStateException("Required dependencies are not enabled");
        java.util.HashSet<String> grants=new java.util.HashSet<>(e.permissions);
        state(c).edit().putStringSet("grants:"+id,grants).putBoolean("enabled:"+id,true).putInt("failures:"+id,0).apply();
        return true;
    }
    public void disable(Context c,String id) { state(c).edit().putBoolean("enabled:"+id,false).apply(); }
    public boolean remove(String id) {
        if(!id.matches("[A-Za-z0-9_.-]{3,80}"))return false;
        File live=new File(root,id),backup=new File(root,id+".last-good");
        delete(live);delete(backup);
        return !live.exists()&&!backup.exists();
    }
    public void recordFailure(Context c,String id,Throwable error) {
        if(id==null||!id.matches("[A-Za-z0-9_.-]{1,80}"))id="unknown";
        int failures=state(c).getInt("failures:"+id,0)+1;
        state(c).edit().putInt("failures:"+id,failures).putBoolean("enabled:"+id,failures<3).apply();
        logError(id,error);
    }
    public File[] list() { File[] a=root.listFiles(File::isDirectory); return a==null?new File[0]:a; }
    public boolean rollback(String id) {
        File live=new File(root,id), backup=new File(root,id+".last-good");
        if(!backup.isDirectory()) return false;
        File failed=new File(root,id+".failed"); delete(failed);
        if(live.exists())live.renameTo(failed);
        boolean ok=backup.renameTo(live); if(ok)delete(failed); return ok;
    }
    public String readLog(String id) {
        File file=new File(new File(root,id),"error.log");
        if(!file.isFile())return "No errors recorded for this extension.";
        StringBuilder out=new StringBuilder();
        try(BufferedReader reader=new BufferedReader(new FileReader(file))){
            String line; java.util.ArrayDeque<String> tail=new java.util.ArrayDeque<>();
            while((line=reader.readLine())!=null){tail.addLast(line);if(tail.size()>60)tail.removeFirst();}
            for(String entry:tail)out.append(entry).append("\\n");
        }catch(Exception e){return "Could not read error log: "+e.getMessage();}
        return out.toString();
    }
    public void logError(String id, Throwable error) {
        try { File d=new File(root,id);d.mkdirs();try(FileWriter w=new FileWriter(new File(d,"error.log"),true)){w.write(new Date()+" "+error+"\\n");} } catch(Exception ignored) {}
    }
    private static void delete(File f) {
        if(f.isDirectory()){File[] a=f.listFiles();if(a!=null)for(File x:a)delete(x);}
        f.delete();
    }
}
''')


# Extension manager UI: import local .zip declarative packs, inspect installed manifests,
# and roll back to the last-known-good version. Store/network updates are intentionally not
# represented as complete until a trusted catalogue endpoint and signing keys exist.
(src / "ExtensionManagerActivity.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.*;
import com.benny.openlauncher.mimax.extensions.ExtensionRegistry;
import org.json.JSONObject;
import java.io.File;
import java.io.FileInputStream;

public final class ExtensionManagerActivity extends Activity {
    private static final int PICK_PACKAGE = 8102;
    private ExtensionRegistry registry;
    private LinearLayout list;
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        registry = new ExtensionRegistry(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(20,20,20,20);
        TextView title = new TextView(this);
        title.setText("Mi_Max Extensions");
        title.setTextSize(23);
        root.addView(title);
        TextView hint = new TextView(this);
        hint.setText("Install declarative .zip extensions. Packages cannot execute code; review requested permissions before enabling them.");
        hint.setPadding(0,12,0,12);
        root.addView(hint);
        Button add = new Button(this);
        add.setText("Import extension ZIP");
        add.setOnClickListener(v -> {
            Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);
            i.setType("application/zip");
            i.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(i,PICK_PACKAGE);
        });
        root.addView(add);
        list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        root.addView(list,new LinearLayout.LayoutParams(-1,0,1));
        setContentView(root);
        refresh();
    }
    private void refresh() {
        list.removeAllViews();
        for(File dir:registry.list()) {
            final String id=dir.getName();
            TextView row=new TextView(this);
            String title=id, permissions="No extra permissions", dependencies="No dependencies";
            boolean canEnable=false;
            try {
                ExtensionRegistry.Entry entry=registry.getEntry(dir);
                title=entry.name+"  "+entry.version+"  ("+id+")";
                permissions="Requested capabilities: "+(entry.permissions.isEmpty()?"none":android.text.TextUtils.join(", ",entry.permissions));
                dependencies="Dependencies: "+(entry.dependencies.isEmpty()?"none":android.text.TextUtils.join(", ",entry.dependencies));
                canEnable=registry.canEnable(this,entry);
            } catch(Exception ignored) {}
            final String permissionSummary=permissions, dependencySummary=dependencies;
            row.setText(title+"\n"+(registry.isEnabled(this,id)?"Enabled":"Disabled")+"\n"+permissionSummary+"\n"+dependencySummary);
            row.setTextSize(14);
            row.setPadding(8,18,8,8);
            list.addView(row);
            Button enable=new Button(this);
            enable.setText(registry.isEnabled(this,id)?"Disable extension":"Review capabilities and enable");
            enable.setEnabled(registry.isEnabled(this,id)||canEnable);
            enable.setOnClickListener(v -> {
                if(registry.isEnabled(this,id)){registry.disable(this,id);refresh();return;}
                new android.app.AlertDialog.Builder(this)
                    .setTitle("Review extension capabilities")
                    .setMessage(permissionSummary+"\n\n"+dependencySummary+"\n\nThis package contains declarative data only. No executable extension code will be loaded.")
                    .setNegativeButton("Cancel",null)
                    .setPositiveButton("Approve and enable",(d,w)->{
                        try{registry.enable(this,id);Toast.makeText(this,"Extension enabled",Toast.LENGTH_SHORT).show();}
                        catch(Exception ex){registry.recordFailure(this,id,ex);Toast.makeText(this,ex.getMessage(),Toast.LENGTH_LONG).show();}
                        refresh();
                    }).show();
            });
            list.addView(enable);
            Button rollback=new Button(this);
            rollback.setText("Rollback to last known good");
            rollback.setOnClickListener(v -> {
                Toast.makeText(this,registry.rollback(id)?"Rolled back":"No backup available",Toast.LENGTH_SHORT).show();
                refresh();
            });
            list.addView(rollback);
            Button remove=new Button(this);
            remove.setText("Remove extension");
            remove.setOnClickListener(v->new android.app.AlertDialog.Builder(this)
                .setTitle("Remove "+id+"?")
                .setMessage("Remove the installed package and its saved rollback copy?")
                .setNegativeButton("Cancel",null)
                .setPositiveButton("Remove",(d,w)->{registry.disable(this,id);registry.remove(id);refresh();})
                .show());
            list.addView(remove);
            Button logs=new Button(this);
            logs.setText("View extension error log");
            logs.setOnClickListener(v->new android.app.AlertDialog.Builder(this)
                .setTitle("Extension log: "+id)
                .setMessage(registry.readLog(id))
                .setPositiveButton("Close",null).show());
            list.addView(logs);
        }
    }
    @Override protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);
        if(request==PICK_PACKAGE && result==RESULT_OK && data!=null && data.getData()!=null) {
            try(java.io.InputStream in=getContentResolver().openInputStream(data.getData())) {
                ExtensionRegistry.Entry e=registry.install(in,android.os.Build.VERSION.SDK_INT);
                Toast.makeText(this,"Installed "+e.name+" ("+e.version+")",Toast.LENGTH_LONG).show();
                refresh();
            } catch(Exception ex) {
                registry.recordFailure(this,"unknown",ex);
                Toast.makeText(this,"Install failed: "+ex.getMessage(),Toast.LENGTH_LONG).show();
            }
        }
    }
}
''')

manifest = Path("app/src/main/AndroidManifest.xml")
m = manifest.read_text()
if "com.benny.openlauncher.mimax.ExtensionManagerActivity" not in m:
    m = m.replace('</application>', '''        <activity
            android:name="com.benny.openlauncher.mimax.ExtensionManagerActivity"
            android:exported="false"
            android:label="Mi_Max Extensions" />
    </application>''', 1)
manifest.write_text(m)

master = Path("app/src/main/res/xml/preferences_master.xml")
m = master.read_text()
if "Mi_Max Extensions" not in m:
    marker = '        <PreferenceScreen\n            android:icon="@drawable/ic_info_outline_dark_24dp"'
    entry = '''        <Preference
            android:title="Mi_Max Extensions"
            android:summary="Import and manage declarative extension packages">
            <intent android:targetPackage="com.mimax.launcher"
                android:targetClass="com.benny.openlauncher.mimax.ExtensionManagerActivity" />
        </Preference>

'''
    if marker not in m:
        raise SystemExit("Could not find About preference insertion point for Extensions")
    master.write_text(m.replace(marker, entry + marker, 1))



# Extension developer tool: generate a signed-off, declarative ZIP template without executable code.
(src / "ExtensionDeveloperActivity.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.widget.*;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.UUID;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

public final class ExtensionDeveloperActivity extends Activity {
    private static final int CREATE_PACKAGE=8812;
    private EditText id,name,version,dependencies;
    private CheckBox layout,animation,activities,assets,shortcuts;
    private TextView status;
    private JSONObject pendingManifest;
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    @Override protected void onCreate(Bundle state){
        super.onCreate(state);
        LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(18),dp(18),dp(18),dp(24));root.setBackgroundColor(0xff101722);
        TextView title=new TextView(this);title.setText("Extension Developer Studio");title.setTextSize(23);title.setTextColor(-1);root.addView(title);
        TextView note=new TextView(this);note.setText("Create a ZIP manifest for a declarative extension. Packages contain data and layout/theme descriptions only; the launcher never executes downloaded code.");note.setTextColor(0xffc5d1df);note.setPadding(0,dp(8),0,dp(14));root.addView(note);
        id=input("Extension ID (letters, numbers, dot, dash, underscore)","my_extension");root.addView(id);
        name=input("Display name","My Extension");root.addView(name);
        version=input("Version","1.0.0");root.addView(version);
        dependencies=input("Dependencies: comma-separated extension IDs (optional)","");root.addView(dependencies);
        TextView caps=new TextView(this);caps.setText("Requested capabilities");caps.setTextColor(-1);caps.setTextSize(16);caps.setPadding(0,dp(10),0,dp(5));root.addView(caps);
        layout=check("island.layout — alter allowed capsule geometry");animation=check("island.animation — choose allowed animations");activities=check("island.activities — declare activity-card templates");assets=check("island.assets — use static image assets");shortcuts=check("launcher.shortcuts — expose approved launcher shortcuts");
        root.addView(layout);root.addView(animation);root.addView(activities);root.addView(assets);root.addView(shortcuts);
        Button validate=new Button(this);validate.setText("Validate manifest and export ZIP");root.addView(validate);validate.setOnClickListener(v->export());
        status=new TextView(this);status.setTextColor(0xffb8d9ff);status.setPadding(0,dp(12),0,0);root.addView(status);
        setContentView(root);
    }
    private EditText input(String hint,String value){EditText e=new EditText(this);e.setSingleLine(true);e.setHint(hint);e.setText(value);e.setTextColor(-1);e.setHintTextColor(0xff98a8ba);return e;}
    private CheckBox check(String value){CheckBox c=new CheckBox(this);c.setText(value);c.setTextColor(-1);return c;}
    private void export(){
        try{
            String extId=id.getText().toString().trim(),extName=name.getText().toString().trim(),extVersion=version.getText().toString().trim();
            if(!extId.matches("[A-Za-z0-9_.-]{3,80}"))throw new IllegalArgumentException("Invalid extension ID");
            if(extName.isEmpty()||extName.length()>80||extVersion.isEmpty()||extVersion.length()>32)throw new IllegalArgumentException("Invalid name or version");
            JSONArray caps=new JSONArray();if(layout.isChecked())caps.put("island.layout");if(animation.isChecked())caps.put("island.animation");
            if(activities.isChecked())caps.put("island.activities");if(assets.isChecked())caps.put("island.assets");if(shortcuts.isChecked())caps.put("launcher.shortcuts");
            JSONArray deps=new JSONArray();String raw=dependencies.getText().toString().trim();
            if(!raw.isEmpty())for(String part:raw.split(",")){String d=part.trim();if(!d.matches("[A-Za-z0-9_.-]{3,80}")||d.equals(extId))throw new IllegalArgumentException("Invalid dependency: "+d);deps.put(d);}
            pendingManifest=new JSONObject().put("format","mimax-declarative-extension").put("manifestVersion",1)
                .put("id",extId).put("name",extName).put("version",extVersion).put("minApi",21)
                .put("permissions",caps).put("dependencies",deps);
            Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("application/zip").addCategory(Intent.CATEGORY_OPENABLE)
                .putExtra(Intent.EXTRA_TITLE,extId+"-"+extVersion+".zip");
            startActivityForResult(i,CREATE_PACKAGE);
            status.setText("Manifest valid. Choose where to save the ZIP package.");
        }catch(Exception e){status.setText("Validation failed: "+e.getMessage());}
    }
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(request!=CREATE_PACKAGE||result!=RESULT_OK||data==null||data.getData()==null||pendingManifest==null)return;
        try(OutputStream raw=getContentResolver().openOutputStream(data.getData());ZipOutputStream zip=new ZipOutputStream(raw)){
            if(raw==null)throw new java.io.IOException("Could not open destination");
            byte[] manifest=pendingManifest.toString(2).getBytes(StandardCharsets.UTF_8);
            zip.putNextEntry(new ZipEntry("manifest.json"));zip.write(manifest);zip.closeEntry();
            byte[] readme=("Mi_Max declarative extension\\nID: "+pendingManifest.getString("id")+"\\nNo executable code is included.\\n").getBytes(StandardCharsets.UTF_8);
            zip.putNextEntry(new ZipEntry("README.txt"));zip.write(readme);zip.closeEntry();zip.finish();
            status.setText("Created "+pendingManifest.getString("id")+".zip successfully.");
        }catch(Exception e){status.setText("Export failed: "+e.getMessage());}
    }
}
''')

manifest = Path("app/src/main/AndroidManifest.xml")
m = manifest.read_text()
if "com.benny.openlauncher.mimax.ExtensionDeveloperActivity" not in m:
    m = m.replace('</application>', '''        <activity
            android:name="com.benny.openlauncher.mimax.ExtensionDeveloperActivity"
            android:exported="false"
            android:label="Extension Developer Studio" />
    </application>''', 1)
manifest.write_text(m)

master = Path("app/src/main/res/xml/preferences_master.xml")
m = master.read_text()
if "Extension Developer Studio" not in m:
    entry = '''        <Preference
            android:title="Extension Developer Studio"
            android:summary="Create and validate declarative extension ZIP templates">
            <intent android:targetPackage="com.mimax.launcher"
                android:targetClass="com.benny.openlauncher.mimax.ExtensionDeveloperActivity" />
        </Preference>
'''
    m=m.replace("</PreferenceScreen>",entry+"</PreferenceScreen>",1)
    master.write_text(m)




# Replace the upstream launcher mark with a Mi_Max vector icon on every density.
icon = Path("app/src/main/res/drawable/ic_mimax_launcher.xml")
icon.parent.mkdir(parents=True, exist_ok=True)
icon.write_text(r'''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path android:fillColor="#0B1320" android:pathData="M0,0h108v108h-108z" />
    <path android:fillColor="#B8D9FF" android:pathData="M17,76V31c0,-4 5,-6 8,-3l29,31 29,-31c3,-3 8,-1 8,3v45h-14V49L57,69c-2,2 -5,2 -7,0L31,49v27z" />
    <path android:fillColor="#55D8C7" android:pathData="M91,11m-7,0a7,7 0,1 0,14 0a7,7 0,1 0,-14 0" />
    <path android:fillColor="#55D8C7" android:pathData="M20,84h68v5h-68z" />
</vector>
''')
manifest = Path("app/src/main/AndroidManifest.xml")
m = manifest.read_text()
m = m.replace('android:icon="@mipmap/ic_launcher"', 'android:icon="@drawable/ic_mimax_launcher"')
if 'android:roundIcon=' not in m:
    m = m.replace('android:icon="@drawable/ic_mimax_launcher"', 'android:icon="@drawable/ic_mimax_launcher"\n        android:roundIcon="@drawable/ic_mimax_launcher"', 1)
manifest.write_text(m)

print("Applied the Mi_Max launcher vector brand icon to the app manifest.")
