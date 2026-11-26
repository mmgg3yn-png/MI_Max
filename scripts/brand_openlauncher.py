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
        public final List<String> permissions;
        Entry(JSONObject j) throws Exception {
            id=j.getString("id"); name=j.getString("name"); version=j.getString("version");
            minApi=j.optInt("minApi",21); permissions=new ArrayList<>();
            JSONArray a=j.optJSONArray("permissions");
            if(a!=null) for(int i=0;i<a.length();i++) permissions.add(a.getString(i));
            if(!id.matches("[A-Za-z0-9_.-]{3,80}")) throw new SecurityException("Invalid extension id");
        }
    }
    public Entry install(InputStream archive, int sdk) throws Exception {
        File stage=new File(root,".staging-"+UUID.randomUUID()); stage.mkdirs();
        try(ZipInputStream zin=new ZipInputStream(archive)) {
            ZipEntry e; byte[] b=new byte[8192];
            while((e=zin.getNextEntry())!=null) {
                String n=e.getName();
                if(n.startsWith("/") || n.contains("..") || n.contains("\\\\")) throw new SecurityException("Unsafe archive path");
                File out=new File(stage,n);
                if(!out.getCanonicalPath().startsWith(stage.getCanonicalPath()+File.separator)) throw new SecurityException("Path traversal");
                if(e.isDirectory()) out.mkdirs(); else {
                    out.getParentFile().mkdirs();
                    try(FileOutputStream os=new FileOutputStream(out)){int k;while((k=zin.read(b))>0)os.write(b,0,k);}
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
    public File[] list() { File[] a=root.listFiles(File::isDirectory); return a==null?new File[0]:a; }
    public boolean rollback(String id) {
        File live=new File(root,id), backup=new File(root,id+".last-good");
        if(!backup.isDirectory()) return false;
        File failed=new File(root,id+".failed"); delete(failed);
        if(live.exists())live.renameTo(failed);
        boolean ok=backup.renameTo(live); if(ok)delete(failed); return ok;
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
            TextView row=new TextView(this);
            String title=dir.getName();
            File mf=new File(dir,"manifest.json");
            try(FileInputStream in=new FileInputStream(mf)) {
                byte[] b=new byte[(int)Math.min(mf.length(),65536)];
                int n=in.read(b);
                if(n>0) { JSONObject j=new JSONObject(new String(b,0,n,"UTF-8")); title=j.optString("name",title)+"  "+j.optString("version",""); }
            } catch(Exception ignored) {}
            row.setText(title);
            row.setTextSize(16);
            row.setPadding(8,18,8,8);
            list.addView(row);
            Button rollback=new Button(this);
            rollback.setText("Rollback to last known good");
            rollback.setOnClickListener(v -> {
                Toast.makeText(this,registry.rollback(dir.getName())?"Rolled back":"No backup available",Toast.LENGTH_SHORT).show();
                refresh();
            });
            list.addView(rollback);
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
