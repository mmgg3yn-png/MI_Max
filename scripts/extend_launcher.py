from pathlib import Path

BASE = Path("app/src/main")
JAVA = BASE / "java/com/benny/openlauncher/mimax"
JAVA.mkdir(parents=True, exist_ok=True)

def replace_once(path, old, new, label):
    p = Path(path)
    s = p.read_text()
    if new in s:
        return
    if old not in s:
        raise SystemExit("Missing patch marker: " + label)
    p.write_text(s.replace(old, new, 1))

# Per-app display names, per-surface label hiding, icon shape/tint and label styling.
item_view = Path("app/src/main/java/com/benny/openlauncher/widget/AppItemView.java")
s = item_view.read_text()
if "private String _iconShape" not in s:
    s = s.replace("import android.graphics.Paint;", "import android.graphics.Paint;\nimport android.graphics.Path;\nimport android.graphics.PorterDuff;", 1)
    s = s.replace("    private boolean _vibrateWhenLongPress;", "    private boolean _vibrateWhenLongPress;\n    private String _iconShape = \"native\";\n    private int _iconTint = Color.TRANSPARENT;", 1)
    anchor = """    public boolean getShowLabel() {
        return _showLabel;
    }
"""
    methods = anchor + """
    public void setShowLabel(boolean show) {
        _showLabel = show;
        requestLayout();
        invalidate();
    }

    public void setIconShape(String shape) {
        _iconShape = shape == null ? \"native\" : shape;
        invalidate();
    }

    public void setIconTint(int tint) {
        _iconTint = tint;
        invalidate();
    }

    public void setLabelTextSizeSp(float size) {
        _textPaint.setTextSize(size * getResources().getDisplayMetrics().scaledDensity);
        invalidate();
    }

    public void setLabelTextColor(int color) {
        _textPaint.setColor(color);
        invalidate();
    }
"""
    s = s.replace(anchor, methods, 1)
    old = """            canvas.save();
            canvas.translate((getWidth() - _iconSize) / 2, _heightPadding);
            _icon.setBounds(0, 0, (int) _iconSize, (int) _iconSize);
            _icon.draw(canvas);
            canvas.restore();"""
    new = """            canvas.save();
            canvas.translate((getWidth() - _iconSize) / 2, _heightPadding);
            if (!\"native\".equals(_iconShape)) {
                Path shape = new Path();
                RectF bounds = new RectF(0, 0, _iconSize, _iconSize);
                if (\"circle\".equals(_iconShape)) {
                    shape.addCircle(_iconSize / 2f, _iconSize / 2f, _iconSize / 2f, Path.Direction.CW);
                } else {
                    float radius = \"square\".equals(_iconShape) ? 0 : \"rounded\".equals(_iconShape) ? _iconSize * .12f : _iconSize * .24f;
                    shape.addRoundRect(bounds, radius, radius, Path.Direction.CW);
                }
                canvas.clipPath(shape);
            }
            _icon.setBounds(0, 0, (int) _iconSize, (int) _iconSize);
            if (_iconTint != Color.TRANSPARENT) _icon.setColorFilter(_iconTint, PorterDuff.Mode.SRC_IN);
            _icon.draw(canvas);
            if (_iconTint != Color.TRANSPARENT) _icon.setColorFilter(null);
            canvas.restore();"""
    if old not in s:
        raise SystemExit("Could not patch AppItemView icon rendering")
    s = s.replace(old, new, 1)
    item_view.write_text(s)

(JAVA / "MiMaxPersonalization.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.BitmapFactory;
import android.graphics.drawable.BitmapDrawable;
import android.net.Uri;
import com.benny.openlauncher.model.Item;
import com.benny.openlauncher.util.DragAction;
import com.benny.openlauncher.widget.AppItemView;

public final class MiMaxPersonalization {
    private MiMaxPersonalization() {}
    public static void apply(Context context, AppItemView view, Item item, DragAction.Action surface) {
        SharedPreferences p=context.getSharedPreferences("mimax_app_customization",Context.MODE_PRIVATE);
        String pkg=null;
        try {
            Intent i=item.getIntent();
            if(i!=null) {
                ComponentName c=i.getComponent();
                pkg=c!=null?c.getPackageName():i.getPackage();
            }
        } catch(Exception ignored) {}
        if(pkg!=null&&!pkg.isEmpty()) {
            String alias=p.getString("label:"+pkg,"");
            if(alias!=null&&!alias.trim().isEmpty()) view.setLabel(alias.trim());
            if(surface==DragAction.Action.DESKTOP && p.getBoolean("hide_home:"+pkg,false)) view.setShowLabel(false);
            if(surface==DragAction.Action.DRAWER && p.getBoolean("hide_drawer:"+pkg,false)) view.setShowLabel(false);
            String icon=p.getString("icon_uri:"+pkg,null);
            if(icon!=null) {
                try(java.io.InputStream in=context.getContentResolver().openInputStream(Uri.parse(icon))) {
                    BitmapFactory.Options options=new BitmapFactory.Options(); options.inSampleSize=2;
                    android.graphics.Bitmap bitmap=in==null?null:BitmapFactory.decodeStream(in,null,options);
                    if(bitmap!=null)view.setIcon(new BitmapDrawable(context.getResources(),bitmap));
                } catch(Exception ignored) {}
            }
        }
        view.setIconShape(p.getString("icon_shape","native"));
        view.setLabelTextSizeSp(p.getFloat("label_size",12f));
        if(p.contains("label_color")) view.setLabelTextColor(p.getInt("label_color",0xffffffff));
        view.setIconTint(p.getInt("icon_tint",0));
    }
    public static void applyFolder(Context context,AppItemView view,Item item) {
        String pkg=null;
        try { Intent i=item.getIntent(); if(i!=null){ComponentName c=i.getComponent();pkg=c!=null?c.getPackageName():i.getPackage();} } catch(Exception ignored) {}
        if(pkg!=null&&context.getSharedPreferences("mimax_app_customization",Context.MODE_PRIVATE).getBoolean("hide_folder:"+pkg,false))view.setShowLabel(false);
    }
}
''')

factory = Path("app/src/main/java/com/benny/openlauncher/viewutil/ItemViewFactory.java")
s = factory.read_text()
marker = """        // TODO find out why tag is set here
        if (view != null) {
            view.setTag(item);
        }"""
replace = """        // Apply Mi_Max per-app labels and icon presentation after the base launcher has built the view.
        if (view instanceof AppItemView) {
            com.benny.openlauncher.mimax.MiMaxPersonalization.apply(context, (AppItemView) view, item, type);
        }

        // TODO find out why tag is set here
        if (view != null) {
            view.setTag(item);
        }"""
replace_once(factory, marker, replace, "ItemViewFactory customization hook")

(JAVA / "MiMaxPersonalizationActivity.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.os.Bundle;
import android.text.InputType;
import android.net.Uri;
import android.view.Gravity;
import android.widget.*;
import java.util.*;

public final class MiMaxPersonalizationActivity extends Activity {
    private static final int PICK_ICON=8411;
    private String pendingIconPackage;
    private android.content.SharedPreferences prefs;
    private LinearLayout list;
    private EditText search;
    private int dp(float v){return (int)(v*getResources().getDisplayMetrics().density+.5f);}
    @Override protected void onCreate(Bundle b){
        super.onCreate(b);prefs=getSharedPreferences("mimax_app_customization",0);
        ScrollView scroll=new ScrollView(this);LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(16),dp(16),dp(16),dp(24));root.setBackgroundColor(0xff111923);scroll.addView(root);
        TextView title=new TextView(this);title.setText("App labels and icons");title.setTextSize(23);title.setTextColor(-1);root.addView(title);
        TextView note=new TextView(this);note.setText("Set a display name for each app, hide its label separately on Home and in the drawer, and change icon shape globally.");note.setTextColor(0xffc4d1df);note.setPadding(0,dp(8),0,dp(12));root.addView(note);
        Spinner shape=new Spinner(this);String[] shapes={"native","squircle","rounded","circle","square"};shape.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,shapes));shape.setSelection(Arrays.asList(shapes).indexOf(prefs.getString("icon_shape","native")));root.addView(shape);
        shape.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){public void onNothingSelected(android.widget.AdapterView<?> p){}public void onItemSelected(android.widget.AdapterView<?> p,android.view.View v,int pos,long id){prefs.edit().putString("icon_shape",shapes[pos]).apply();}});
        TextView sizeLabel=new TextView(this);sizeLabel.setText("Icon label size");sizeLabel.setTextColor(-1);root.addView(sizeLabel);
        SeekBar size=new SeekBar(this);size.setMax(10);size.setProgress(Math.max(0,Math.min(10,Math.round(prefs.getFloat("label_size",12f)-8f))));root.addView(size);
        size.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){public void onProgressChanged(SeekBar b,int v,boolean u){sizeLabel.setText("Icon label size: "+(v+8)+" sp");prefs.edit().putFloat("label_size",v+8f).apply();}public void onStartTrackingTouch(SeekBar b){}public void onStopTrackingTouch(SeekBar b){}});
        search=new EditText(this);search.setSingleLine(true);search.setHint("Search installed apps");search.setTextColor(-1);search.setHintTextColor(0xff9aa9ba);search.setInputType(InputType.TYPE_CLASS_TEXT);root.addView(search);
        list=new LinearLayout(this);list.setOrientation(1);root.addView(list);
        search.addTextChangedListener(new android.text.TextWatcher(){public void beforeTextChanged(CharSequence s,int st,int count,int after){}public void onTextChanged(CharSequence s,int st,int before,int count){populate(s.toString());}public void afterTextChanged(android.text.Editable e){}});
        setContentView(scroll);populate("");
    }
    private void populate(String query){
        list.removeAllViews();
        Intent i=new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER);
        PackageManager pm=getPackageManager();
        @SuppressWarnings("deprecation") List<ResolveInfo> results=pm.queryIntentActivities(i,0);
        TreeMap<String,ResolveInfo> unique=new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        for(ResolveInfo r:results){if(r.activityInfo!=null)unique.put(r.activityInfo.packageName,r);}
        for(ResolveInfo r:unique.values()){
            final String pkg=r.activityInfo.packageName,label=r.loadLabel(pm).toString();
            if(!label.toLowerCase(Locale.ROOT).contains(query.toLowerCase(Locale.ROOT))&&!pkg.toLowerCase(Locale.ROOT).contains(query.toLowerCase(Locale.ROOT)))continue;
            LinearLayout card=new LinearLayout(this);card.setOrientation(1);card.setPadding(dp(10),dp(10),dp(10),dp(10));card.setBackgroundColor(0xff202b39);
            LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(-1,-2);cp.bottomMargin=dp(8);list.addView(card,cp);
            TextView name=new TextView(this);name.setText(label+"  •  "+pkg);name.setTextColor(-1);name.setTextSize(14);card.addView(name);
            EditText alias=new EditText(this);alias.setSingleLine(true);alias.setTextColor(-1);alias.setHint("Custom name (empty = original)");alias.setText(prefs.getString("label:"+pkg,""));card.addView(alias);
            Switch home=new Switch(this);home.setText("Hide label on Home");home.setTextColor(-1);home.setChecked(prefs.getBoolean("hide_home:"+pkg,false));card.addView(home);
            Switch drawer=new Switch(this);drawer.setText("Hide label in app drawer");drawer.setTextColor(-1);drawer.setChecked(prefs.getBoolean("hide_drawer:"+pkg,false));card.addView(drawer);
            Switch folder=new Switch(this);folder.setText("Hide label inside folders");folder.setTextColor(-1);folder.setChecked(prefs.getBoolean("hide_folder:"+pkg,false));card.addView(folder);
            Button icon=new Button(this);icon.setText(prefs.contains("icon_uri:"+pkg)?"Change custom icon":"Choose custom icon");card.addView(icon);
            icon.setOnClickListener(v->{pendingIconPackage=pkg;Intent pick=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("image/*").addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(pick,PICK_ICON);});
            Button clearIcon=new Button(this);clearIcon.setText("Clear custom icon");clearIcon.setEnabled(prefs.contains("icon_uri:"+pkg));card.addView(clearIcon);
            clearIcon.setOnClickListener(v->{prefs.edit().remove("icon_uri:"+pkg).apply();clearIcon.setEnabled(false);icon.setText("Choose custom icon");});
            Button save=new Button(this);save.setText("Save "+label);card.addView(save);
            save.setOnClickListener(v->{String text=alias.getText().toString().trim();prefs.edit().putString("label:"+pkg,text).putBoolean("hide_home:"+pkg,home.isChecked()).putBoolean("hide_drawer:"+pkg,drawer.isChecked()).putBoolean("hide_folder:"+pkg,folder.isChecked()).apply();Toast.makeText(this,"Saved "+label,Toast.LENGTH_SHORT).show();});
        }
    }
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(request==PICK_ICON&&result==RESULT_OK&&data!=null&&data.getData()!=null&&pendingIconPackage!=null){
            Uri uri=data.getData();
            try{getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(Exception ignored){}
            prefs.edit().putString("icon_uri:"+pendingIconPackage,uri.toString()).apply();
            Toast.makeText(this,"Custom icon saved. Reopen the launcher screen to refresh it.",Toast.LENGTH_LONG).show();
            pendingIconPackage=null;
        }
    }
}
''')

# Per-page wallpapers: one persistent image URI per desktop page.
desktop = Path("app/src/main/java/com/benny/openlauncher/widget/Desktop.java")
s = desktop.read_text()
if "refreshMiMaxPageWallpaper" not in s:
    s = s.replace("import android.content.Context;", "import android.content.Context;\nimport android.graphics.Bitmap;\nimport android.graphics.BitmapFactory;\nimport android.graphics.drawable.BitmapDrawable;\nimport android.net.Uri;", 1)
    s = s.replace("""    public Desktop(Context context) {
        super(context, null);
    }""", """    public Desktop(Context context) {
        super(context, null);
        installMiMaxPageWallpaperListener();
    }""", 1)
    s = s.replace("""    public Desktop(Context context, AttributeSet attr) {
        super(context, attr);
    }""", """    public Desktop(Context context, AttributeSet attr) {
        super(context, attr);
        installMiMaxPageWallpaperListener();
    }""", 1)
    marker = """    @Override
    protected void onPageScrolled(int position, float offset, int offsetPixels) {"""
    methods = """    private void installMiMaxPageWallpaperListener() {
        addOnPageChangeListener(new ViewPager.OnPageChangeListener() {
            @Override public void onPageScrolled(int position, float offset, int offsetPixels) { }
            @Override public void onPageSelected(int position) { refreshMiMaxPageWallpaper(position); }
            @Override public void onPageScrollStateChanged(int state) { }
        });
    }

    public void refreshMiMaxPageWallpaper() {
        refreshMiMaxPageWallpaper(getCurrentItem());
    }

    private void refreshMiMaxPageWallpaper(int page) {
        String raw = getContext().getSharedPreferences("mimax_page_wallpapers", Context.MODE_PRIVATE)
                .getString("page_" + page, null);
        if (raw == null || raw.trim().isEmpty()) {
            setBackground(null);
            return;
        }
        try {
            BitmapFactory.Options options = new BitmapFactory.Options();
            options.inSampleSize = 2;
            Bitmap bitmap;
            try (java.io.InputStream in = getContext().getContentResolver().openInputStream(Uri.parse(raw))) {
                bitmap = in == null ? null : BitmapFactory.decodeStream(in, null, options);
            }
            setBackground(bitmap == null ? null : new BitmapDrawable(getResources(), bitmap));
        } catch (Exception e) {
            setBackground(null);
        }
    }

"""
    if marker not in s:
        raise SystemExit("Could not find Desktop page-scroll insertion point")
    s = s.replace(marker, methods + marker, 1)
    desktop.write_text(s)

(JAVA / "MiMaxPageWallpaperActivity.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.widget.*;
import com.benny.openlauncher.activity.HomeActivity;

public final class MiMaxPageWallpaperActivity extends Activity {
    private static final int PICK_IMAGE=7402;
    private EditText page;
    private android.content.SharedPreferences prefs;
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    @Override protected void onCreate(Bundle b){super.onCreate(b);prefs=getSharedPreferences("mimax_page_wallpapers",0);
        LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(20),dp(20),dp(20),dp(20));root.setBackgroundColor(0xff101722);
        TextView title=new TextView(this);title.setText("Per-page wallpapers");title.setTextColor(-1);title.setTextSize(22);root.addView(title);
        TextView hint=new TextView(this);hint.setText("Choose a page number, then select an image for that page. Page numbers start at 1.");hint.setTextColor(0xffc8d4e0);hint.setPadding(0,dp(10),0,dp(14));root.addView(hint);
        page=new EditText(this);page.setInputType(InputType.TYPE_CLASS_NUMBER);int current=HomeActivity._launcher==null?0:HomeActivity._launcher.getDesktop().getCurrentItem();page.setText(String.valueOf(current+1));page.setTextColor(-1);page.setHint("Page number");root.addView(page);
        Button choose=new Button(this);choose.setText("Choose wallpaper image");root.addView(choose);choose.setOnClickListener(v->{Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("image/*").addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(i,PICK_IMAGE);});
        Button clear=new Button(this);clear.setText("Clear wallpaper for this page");root.addView(clear);clear.setOnClickListener(v->{int p=pageNumber();prefs.edit().remove("page_"+p).apply();refresh(p);Toast.makeText(this,"Page wallpaper cleared",Toast.LENGTH_SHORT).show();});
        setContentView(root);
    }
    private int pageNumber(){try{return Math.max(0,Integer.parseInt(page.getText().toString())-1);}catch(Exception e){return 0;}}
    private void refresh(int p){if(HomeActivity._launcher!=null&&HomeActivity._launcher.getDesktop()!=null){HomeActivity._launcher.getDesktop().setCurrentItem(p,false);HomeActivity._launcher.getDesktop().refreshMiMaxPageWallpaper();}}
    @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request==PICK_IMAGE&&result==RESULT_OK&&data!=null&&data.getData()!=null){Uri uri=data.getData();try{getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(Exception ignored){}int p=pageNumber();prefs.edit().putString("page_"+p,uri.toString()).apply();refresh(p);Toast.makeText(this,"Wallpaper assigned to page "+(p+1),Toast.LENGTH_SHORT).show();}}
}
''')

manifest = BASE / "AndroidManifest.xml"
m = manifest.read_text()
if "com.benny.openlauncher.mimax.MiMaxPersonalizationActivity" not in m:
    m = m.replace("</application>", '''        <activity android:name="com.benny.openlauncher.mimax.MiMaxPersonalizationActivity" android:exported="false" android:label="App labels and icons" />
        <activity android:name="com.benny.openlauncher.mimax.MiMaxPageWallpaperActivity" android:exported="false" android:label="Per-page wallpapers" />
    </application>''', 1)
manifest.write_text(m)

master = BASE / "res/xml/preferences_master.xml"
p = master.read_text()
if "mimax_personalization" not in p:
    entry = '''    <PreferenceCategory android:title="Mi_Max Personalization">
        <Preference android:key="mimax_personalization" android:title="App labels and icon styles"
            android:summary="Per-app names, label visibility, icon shape and text size">
            <intent android:targetPackage="com.mimax.launcher" android:targetClass="com.benny.openlauncher.mimax.MiMaxPersonalizationActivity" />
        </Preference>
        <Preference android:key="mimax_page_wallpapers" android:title="Different wallpaper per page"
            android:summary="Choose a separate image for each home page">
            <intent android:targetPackage="com.mimax.launcher" android:targetClass="com.benny.openlauncher.mimax.MiMaxPageWallpaperActivity" />
        </Preference>
    </PreferenceCategory>
'''
    p = p.replace("</PreferenceScreen>", entry + "</PreferenceScreen>", 1)
master.write_text(p)

print("Mi_Max per-app labels, per-surface label hiding, icon masks and per-page wallpaper controls integrated into OpenLauncher views.")


# Extend OpenLauncher's existing backup/restore format with Mi_Max settings and declarative packs.
backup = Path("app/src/main/java/com/benny/openlauncher/util/BackupHelper.java")
backup.write_text(r'''package com.benny.openlauncher.util;

import android.content.Context;
import android.net.Uri;
import android.widget.Toast;
import com.benny.openlauncher.R;
import java.io.*;
import java.util.zip.*;

public class BackupHelper {
    private static final String[] EXTRA_PREFS = new String[] {
        "mimax_island_state.xml",
        "me_island_themes_v1.xml",
        "mimax_app_customization.xml",
        "mimax_page_wallpapers.xml"
    };

    public static void backupConfig(Context context, Uri uri) {
        File data = new File(context.getApplicationInfo().dataDir);
        try (OutputStream raw = context.getContentResolver().openOutputStream(uri);
             ZipOutputStream zip = new ZipOutputStream(new BufferedOutputStream(raw))) {
            if (raw == null) throw new IOException("Backup destination is unavailable");
            addIfExists(zip, new File(data, "databases/home.db"), "home.db");
            addIfExists(zip, new File(data, "shared_prefs/app.xml"), "app.xml");
            for (String name : EXTRA_PREFS) {
                addIfExists(zip, new File(data, "shared_prefs/" + name), "prefs/" + name);
            }
            File extensions = new File(context.getFilesDir(), "mimax-extensions");
            addDirectoryToZip(zip, extensions, "extensions");
            zip.finish();
            Toast.makeText(context, R.string.toast_backup_success, Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            Toast.makeText(context, R.string.toast_backup_error, Toast.LENGTH_SHORT).show();
        }
    }

    public static void restoreConfig(Context context, Uri uri) {
        File data = new File(context.getApplicationInfo().dataDir);
        long total = 0;
        try (InputStream raw = context.getContentResolver().openInputStream(uri);
             ZipInputStream zip = new ZipInputStream(new BufferedInputStream(raw))) {
            if (raw == null) throw new IOException("Backup source is unavailable");
            ZipEntry entry;
            byte[] buffer = new byte[8192];
            while ((entry = zip.getNextEntry()) != null) {
                String name = entry.getName();
                File target = restoreTarget(context, data, name);
                if (target == null) { zip.closeEntry(); continue; }
                String root = data.getCanonicalPath() + File.separator;
                if (!target.getCanonicalPath().startsWith(root)) throw new SecurityException("Unsafe restore path");
                if (entry.isDirectory()) {
                    target.mkdirs();
                    zip.closeEntry();
                    continue;
                }
                File parent = target.getParentFile();
                if (parent != null && !parent.exists() && !parent.mkdirs()) throw new IOException("Cannot create restore folder");
                long entryBytes = 0;
                try (FileOutputStream out = new FileOutputStream(target)) {
                    int count;
                    while ((count = zip.read(buffer)) != -1) {
                        entryBytes += count;
                        total += count;
                        if (entryBytes > 16L * 1024L * 1024L || total > 64L * 1024L * 1024L)
                            throw new IOException("Backup exceeds safe extraction limits");
                        out.write(buffer, 0, count);
                    }
                }
                zip.closeEntry();
            }
            Toast.makeText(context, R.string.toast_backup_success, Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            Toast.makeText(context, R.string.toast_backup_error, Toast.LENGTH_SHORT).show();
        }
    }

    private static File restoreTarget(Context context, File data, String name) throws IOException {
        if ("home.db".equals(name)) return new File(data, "databases/home.db");
        if ("app.xml".equals(name)) return new File(data, "shared_prefs/app.xml");
        if (name.startsWith("prefs/")) {
            String leaf = name.substring("prefs/".length());
            for (String allowed : EXTRA_PREFS) {
                if (allowed.equals(leaf)) return new File(data, "shared_prefs/" + leaf);
            }
            return null;
        }
        if (name.startsWith("extensions/")) {
            String relative = name.substring("extensions/".length());
            if (relative.isEmpty() || relative.startsWith("/") || relative.contains("..") || relative.contains("\\\\"))
                throw new SecurityException("Unsafe extension path");
            return new File(new File(context.getFilesDir(), "mimax-extensions"), relative);
        }
        return null;
    }

    private static void addIfExists(ZipOutputStream zip, File file, String entry) throws IOException {
        if (file.isFile()) addFileToZip(zip, file, entry);
    }

    private static void addDirectoryToZip(ZipOutputStream zip, File directory, String prefix) throws IOException {
        if (!directory.isDirectory()) return;
        File[] children = directory.listFiles();
        if (children == null) return;
        for (File child : children) {
            String name = prefix + "/" + child.getName();
            if (child.isDirectory()) addDirectoryToZip(zip, child, name);
            else if (child.isFile()) addFileToZip(zip, child, name);
        }
    }

    public static void addFileToZip(ZipOutputStream zip, File file, String name) throws IOException {
        zip.putNextEntry(new ZipEntry(name));
        try (InputStream in = new BufferedInputStream(new FileInputStream(file))) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = in.read(buffer)) != -1) zip.write(buffer, 0, count);
        }
        zip.closeEntry();
    }
}
''')

print("Extended BackupHelper to preserve OpenLauncher database/settings, Mi_Max personalization, island themes and declarative extension packages with safe restore paths.")


# User profiles: independent snapshots of launcher settings, app visibility,
# per-app customizations, per-page wallpaper assignments and the selected Me Island engine.
(JAVA / "MiMaxProfileManager.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.content.Context;
import android.content.SharedPreferences;
import com.benny.openlauncher.R;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.*;

public final class MiMaxProfileManager {
    private final Context context;
    private final SharedPreferences profiles;
    private final String[] resourceKeys;
    private final String[] extraFiles = {"mimax_app_customization","mimax_page_wallpapers"};
    public static final class Profile {
        public final String id,name,updated;
        public Profile(String i,String n,String u){id=i;name=n;updated=u;}
    }
    public MiMaxProfileManager(Context c){
        context=c.getApplicationContext();
        profiles=context.getSharedPreferences("mimax_profiles",Context.MODE_PRIVATE);
        resourceKeys=new String[]{
            context.getString(R.string.pref_key__desktop_columns),
            context.getString(R.string.pref_key__desktop_rows),
            context.getString(R.string.pref_key__desktop_show_label),
            context.getString(R.string.pref_key__desktop_lock),
            context.getString(R.string.pref_key__dock_enable),
            context.getString(R.string.pref_key__dock_columns),
            context.getString(R.string.pref_key__dock_rows),
            context.getString(R.string.pref_key__dock_show_label),
            context.getString(R.string.pref_key__drawer_columns),
            context.getString(R.string.pref_key__drawer_rows),
            context.getString(R.string.pref_key__drawer_style),
            context.getString(R.string.pref_key__drawer_show_label),
            context.getString(R.string.pref_key__hidden_apps),
            context.getString(R.string.pref_key__theme),
            context.getString(R.string.pref_key__primary_color),
            context.getString(R.string.pref_key__icon_size),
            context.getString(R.string.pref_key__icon_pack),
            context.getString(R.string.pref_key__gesture_double_tap),
            context.getString(R.string.pref_key__gesture_swipe_up),
            context.getString(R.string.pref_key__gesture_swipe_down),
            context.getString(R.string.pref_key__gesture_pinch),
            context.getString(R.string.pref_key__gesture_unpinch)
        };
    }
    public List<Profile> all(){
        ArrayList<Profile> result=new ArrayList<>();
        for(Map.Entry<String,?> e:profiles.getAll().entrySet()){
            if(!e.getKey().startsWith("profile_")||!(e.getValue() instanceof String))continue;
            try{JSONObject o=new JSONObject((String)e.getValue());result.add(new Profile(o.getString("id"),o.getString("name"),o.optString("updated","")));}
            catch(Exception ignored){}
        }
        Collections.sort(result,(a,b)->a.name.compareToIgnoreCase(b.name));
        return result;
    }
    public void save(String name) throws Exception{
        String clean=name==null?"":name.trim();
        if(clean.isEmpty()||clean.length()>32)throw new IllegalArgumentException("Profile name must contain 1 to 32 characters");
        String id=UUID.randomUUID().toString();
        JSONObject root=new JSONObject().put("format","mimax-profile").put("id",id).put("name",clean)
            .put("updated",new Date().toString()).put("launcher",snapshot(context.getSharedPreferences("app",0),resourceKeys));
        JSONObject extra=new JSONObject();
        for(String file:extraFiles)extra.put(file,snapshot(context.getSharedPreferences(file,0),null));
        root.put("extra",extra);
        root.put("islandTheme",context.getSharedPreferences(MeIslandThemeManager.PREFS,0).getString("selected_theme","his"));
        profiles.edit().putString("profile_"+id,root.toString()).apply();
    }
    public boolean activate(String id) throws Exception{
        String raw=profiles.getString("profile_"+id,null);if(raw==null)return false;
        JSONObject root=new JSONObject(raw);
        if(!"mimax-profile".equals(root.optString("format")))throw new IllegalArgumentException("Invalid profile");
        restore(context.getSharedPreferences("app",0),root.getJSONObject("launcher"));
        JSONObject extra=root.optJSONObject("extra");
        if(extra!=null)for(String file:extraFiles){JSONObject values=extra.optJSONObject(file);if(values!=null)restore(context.getSharedPreferences(file,0),values);}
        String theme=root.optString("islandTheme","his");
        MeIslandThemeManager manager=new MeIslandThemeManager(context);
        if(manager.findTheme(theme)!=null)manager.select(theme);
        return true;
    }
    public boolean remove(String id){return profiles.edit().remove("profile_"+id).commit();}
    private JSONObject snapshot(SharedPreferences prefs,String[] allow) throws Exception{
        JSONObject out=new JSONObject();
        for(Map.Entry<String,?> e:prefs.getAll().entrySet()){
            if(allow!=null&&!Arrays.asList(allow).contains(e.getKey()))continue;
            Object v=e.getValue();
            if(v instanceof String||v instanceof Boolean||v instanceof Integer||v instanceof Long||v instanceof Float)out.put(e.getKey(),v);
            else if(v instanceof Set){JSONArray a=new JSONArray();for(Object item:(Set<?>)v)if(item instanceof String)a.put(item);out.put(e.getKey(),a);}
        }
        return out;
    }
    private void restore(SharedPreferences prefs,JSONObject values){
        SharedPreferences.Editor edit=prefs.edit();
        JSONArray keys=new JSONArray();
        for(Iterator<String> it=values.keys();it.hasNext();)keys.put(it.next());
        for(int i=0;i<keys.length();i++){
            String key=keys.optString(i);
            try{
                Object v=values.get(key);
                if(v instanceof String)edit.putString(key,(String)v);
                else if(v instanceof Boolean)edit.putBoolean(key,(Boolean)v);
                else if(v instanceof Integer)edit.putInt(key,(Integer)v);
                else if(v instanceof Long)edit.putLong(key,(Long)v);
                else if(v instanceof Double)edit.putFloat(key,((Double)v).floatValue());
                else if(v instanceof JSONArray){Set<String> set=new HashSet<>();JSONArray a=(JSONArray)v;for(int n=0;n<a.length();n++)set.add(a.getString(n));edit.putStringSet(key,set);}
            }catch(Exception ignored){}
        }
        edit.apply();
    }
}
''')

(JAVA / "MiMaxProfilesActivity.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.Activity;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.*;
import java.util.*;

public final class MiMaxProfilesActivity extends Activity {
    private MiMaxProfileManager manager;
    private LinearLayout list;
    private EditText name;
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    @Override protected void onCreate(Bundle b){super.onCreate(b);manager=new MiMaxProfileManager(this);
        ScrollView scroll=new ScrollView(this);LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(18),dp(18),dp(18),dp(24));root.setBackgroundColor(0xff101722);scroll.addView(root);
        TextView title=new TextView(this);title.setText("Mi_Max Profiles");title.setTextSize(23);title.setTextColor(-1);root.addView(title);
        TextView hint=new TextView(this);hint.setText("Save and switch launcher settings, hidden-app selections, icon personalization, page wallpapers and Me Island engine.");hint.setTextColor(0xffc5d1df);hint.setPadding(0,dp(8),0,dp(12));root.addView(hint);
        name=new EditText(this);name.setSingleLine(true);name.setTextColor(-1);name.setHint("Profile name");root.addView(name);
        Button save=new Button(this);save.setText("Save current setup as profile");root.addView(save);save.setOnClickListener(v->{try{manager.save(name.getText().toString());name.setText("");refresh();Toast.makeText(this,"Profile saved",Toast.LENGTH_SHORT).show();}catch(Exception e){Toast.makeText(this,e.getMessage(),Toast.LENGTH_LONG).show();}});
        list=new LinearLayout(this);list.setOrientation(1);root.addView(list);setContentView(scroll);refresh();
    }
    private void refresh(){list.removeAllViews();for(MiMaxProfileManager.Profile p:manager.all()){
        LinearLayout card=new LinearLayout(this);card.setOrientation(1);card.setPadding(dp(10),dp(10),dp(10),dp(10));card.setBackgroundColor(0xff202b39);LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=dp(8);list.addView(card,lp);
        TextView t=new TextView(this);t.setText(p.name);t.setTextColor(-1);t.setTextSize(17);card.addView(t);
        TextView date=new TextView(this);date.setText(p.updated);date.setTextColor(0xffaebdcb);date.setTextSize(11);card.addView(date);
        LinearLayout actions=new LinearLayout(this);card.addView(actions);
        Button activate=new Button(this);activate.setText("Activate");actions.addView(activate,new LinearLayout.LayoutParams(0,-2,1));activate.setOnClickListener(v->{try{manager.activate(p.id);Toast.makeText(this,"Activated "+p.name+". Reopen the launcher to refresh all screens.",Toast.LENGTH_LONG).show();}catch(Exception e){Toast.makeText(this,"Profile could not be activated: "+e.getMessage(),Toast.LENGTH_LONG).show();}});
        Button remove=new Button(this);remove.setText("Delete");actions.addView(remove,new LinearLayout.LayoutParams(0,-2,1));remove.setOnClickListener(v->{manager.remove(p.id);refresh();});
    }}
}
''')

(JAVA / "MiMaxThemeScheduleReceiver.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import java.util.Calendar;

public final class MiMaxThemeScheduleReceiver extends BroadcastReceiver {
    public static final String ACTION_APPLY="com.mimax.launcher.action.APPLY_SCHEDULED_THEME";
    public static final String EXTRA_THEME="theme_id";
    static void schedule(Context c,int hour,int minute,String theme,int request){
        AlarmManager am=(AlarmManager)c.getSystemService(Context.ALARM_SERVICE);
        PendingIntent pi=pending(c,theme,request);
        Calendar next=Calendar.getInstance();next.set(Calendar.HOUR_OF_DAY,hour);next.set(Calendar.MINUTE,minute);next.set(Calendar.SECOND,0);next.set(Calendar.MILLISECOND,0);
        if(next.getTimeInMillis()<=System.currentTimeMillis())next.add(Calendar.DAY_OF_YEAR,1);
        am.setInexactRepeating(AlarmManager.RTC_WAKEUP,next.getTimeInMillis(),AlarmManager.INTERVAL_DAY,pi);
    }
    static void cancel(Context c,int request){
        AlarmManager am=(AlarmManager)c.getSystemService(Context.ALARM_SERVICE);
        PendingIntent pi=PendingIntent.getBroadcast(c,request,new Intent(c,MiMaxThemeScheduleReceiver.class).setAction(ACTION_APPLY),PendingIntent.FLAG_NO_CREATE|(android.os.Build.VERSION.SDK_INT>=23?PendingIntent.FLAG_IMMUTABLE:0));
        if(pi!=null){am.cancel(pi);pi.cancel();}
    }
    private static PendingIntent pending(Context c,String theme,int request){
        Intent i=new Intent(c,MiMaxThemeScheduleReceiver.class).setAction(ACTION_APPLY).putExtra(EXTRA_THEME,theme);
        return PendingIntent.getBroadcast(c,request,i,PendingIntent.FLAG_UPDATE_CURRENT|(android.os.Build.VERSION.SDK_INT>=23?PendingIntent.FLAG_IMMUTABLE:0));
    }
    @Override public void onReceive(Context c,Intent i){
        if(i==null)return;
        if(Intent.ACTION_BOOT_COMPLETED.equals(i.getAction())){
            android.content.SharedPreferences p=c.getSharedPreferences("mimax_theme_schedule",0);
            if(p.getBoolean("enabled",false)){
                schedule(c,p.getInt("day_hour",8),p.getInt("day_minute",0),p.getString("day_theme","ltin"),8211);
                schedule(c,p.getInt("night_hour",20),p.getInt("night_minute",0),p.getString("night_theme","his"),8212);
            }
            return;
        }
        if(!ACTION_APPLY.equals(i.getAction()))return;
        String id=i.getStringExtra(EXTRA_THEME);
        if(id==null)return;
        try{
            MeIslandThemeManager m=new MeIslandThemeManager(c);
            if(m.findTheme(id)==null)return;
            m.select(id);
            Intent refresh=new Intent(c,MeIslandService.class).setAction(MeIslandService.ACTION_REFRESH);
            try{c.startService(refresh);}catch(Exception ignored){}
        }catch(Exception ignored){}
    }
}
''')

(JAVA / "MiMaxThemeScheduleActivity.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.Activity;
import android.app.TimePickerDialog;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.*;
import java.util.*;

public final class MiMaxThemeScheduleActivity extends Activity {
    private android.content.SharedPreferences prefs;
    private int dayHour=8,dayMinute=0,nightHour=20,nightMinute=0;
    private Spinner dayTheme,nightTheme;
    private TextView dayTime,nightTime,status;
    private String[] ids,names;
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    @Override protected void onCreate(Bundle b){super.onCreate(b);prefs=getSharedPreferences("mimax_theme_schedule",0);
        List<MeIslandThemeManager.Theme> all=new MeIslandThemeManager(this).all();ids=new String[all.size()];names=new String[all.size()];
        for(int i=0;i<all.size();i++){ids[i]=all.get(i).id;names[i]=all.get(i).name;}
        dayHour=prefs.getInt("day_hour",8);dayMinute=prefs.getInt("day_minute",0);nightHour=prefs.getInt("night_hour",20);nightMinute=prefs.getInt("night_minute",0);
        LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(18),dp(18),dp(18),dp(24));root.setBackgroundColor(0xff101722);
        TextView title=new TextView(this);title.setText("Scheduled Me Island themes");title.setTextSize(23);title.setTextColor(-1);root.addView(title);
        TextView hint=new TextView(this);hint.setText("Apply one visual engine during the day and another at night. Android may deliver inexact alarms a little later to save battery.");hint.setTextColor(0xffbfccda);hint.setPadding(0,dp(8),0,dp(14));root.addView(hint);
        dayTheme=spinner(prefs.getString("day_theme","ltin"));root.addView(label("Day theme"));root.addView(dayTheme);
        dayTime=new TextView(this);dayTime.setTextColor(-1);dayTime.setTextSize(17);root.addView(dayTime);
        Button day=new Button(this);day.setText("Choose day start time");root.addView(day);day.setOnClickListener(v->choose(true));
        nightTheme=spinner(prefs.getString("night_theme","his"));root.addView(label("Night theme"));root.addView(nightTheme);
        nightTime=new TextView(this);nightTime.setTextColor(-1);nightTime.setTextSize(17);root.addView(nightTime);
        Button night=new Button(this);night.setText("Choose night start time");root.addView(night);night.setOnClickListener(v->choose(false));
        Button save=new Button(this);save.setText("Save and enable daily schedule");root.addView(save);save.setOnClickListener(v->save());
        Button disable=new Button(this);disable.setText("Disable schedule");root.addView(disable);disable.setOnClickListener(v->{prefs.edit().putBoolean("enabled",false).apply();MiMaxThemeScheduleReceiver.cancel(this,8211);MiMaxThemeScheduleReceiver.cancel(this,8212);status.setText("Schedule disabled");});
        status=new TextView(this);status.setTextColor(0xffb9d9ff);status.setPadding(0,dp(10),0,0);root.addView(status);
        updateTimes();setContentView(root);
    }
    private TextView label(String text){TextView t=new TextView(this);t.setText(text);t.setTextColor(-1);t.setTextSize(16);t.setPadding(0,dp(12),0,dp(4));return t;}
    private Spinner spinner(String selected){Spinner s=new Spinner(this);s.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,names));int index=Arrays.asList(ids).indexOf(selected);s.setSelection(Math.max(0,index));return s;}
    private void choose(boolean day){int h=day?dayHour:nightHour,m=day?dayMinute:nightMinute;new TimePickerDialog(this,(v,hh,mm)->{if(day){dayHour=hh;dayMinute=mm;}else{nightHour=hh;nightMinute=mm;}updateTimes();},h,m,true).show();}
    private void updateTimes(){dayTime.setText(String.format(Locale.getDefault(),"Day begins at %02d:%02d",dayHour,dayMinute));nightTime.setText(String.format(Locale.getDefault(),"Night begins at %02d:%02d",nightHour,nightMinute));}
    private void save(){
        String d=ids[Math.max(0,dayTheme.getSelectedItemPosition())],n=ids[Math.max(0,nightTheme.getSelectedItemPosition())];
        if(d.equals(n)){status.setText("Choose two different themes for day and night");return;}
        prefs.edit().putBoolean("enabled",true).putString("day_theme",d).putString("night_theme",n)
            .putInt("day_hour",dayHour).putInt("day_minute",dayMinute).putInt("night_hour",nightHour).putInt("night_minute",nightMinute).apply();
        MiMaxThemeScheduleReceiver.schedule(this,dayHour,dayMinute,d,8211);
        MiMaxThemeScheduleReceiver.schedule(this,nightHour,nightMinute,n,8212);
        status.setText("Daily theme schedule enabled");
    }
}
''')

manifest = BASE / "AndroidManifest.xml"
m=manifest.read_text()
if "com.benny.openlauncher.mimax.MiMaxProfilesActivity" not in m:
    m=m.replace('<application','<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />\n    <application',1)
    m=m.replace('</application>','''        <activity android:name="com.benny.openlauncher.mimax.MiMaxProfilesActivity" android:exported="false" android:label="Mi_Max Profiles" />
        <activity android:name="com.benny.openlauncher.mimax.MiMaxThemeScheduleActivity" android:exported="false" android:label="Scheduled themes" />
        <receiver android:name="com.benny.openlauncher.mimax.MiMaxThemeScheduleReceiver" android:exported="false">
            <intent-filter>
                <action android:name="com.mimax.launcher.action.APPLY_SCHEDULED_THEME" />
                <action android:name="android.intent.action.BOOT_COMPLETED" />
            </intent-filter>
        </receiver>
    </application>''',1)
manifest.write_text(m)

master = BASE / "res/xml/preferences_master.xml"
p=master.read_text()
if "mimax_profiles" not in p:
    entry='''    <PreferenceCategory android:title="Mi_Max Workspace">
        <Preference android:key="mimax_profiles" android:title="Multiple profiles and Focus layouts"
            android:summary="Save and switch app visibility, gestures, icons and workspace settings">
            <intent android:targetPackage="com.mimax.launcher" android:targetClass="com.benny.openlauncher.mimax.MiMaxProfilesActivity" />
        </Preference>
        <Preference android:key="mimax_theme_schedule" android:title="Scheduled Me Island themes"
            android:summary="Automatically switch LTIN, HIS, ColorOS or imported themes by time">
            <intent android:targetPackage="com.mimax.launcher" android:targetClass="com.benny.openlauncher.mimax.MiMaxThemeScheduleActivity" />
        </Preference>
    </PreferenceCategory>
'''
    p=p.replace("</PreferenceScreen>",entry+"</PreferenceScreen>",1)
master.write_text(p)

# Include the new profile and schedule state in the standard backup archive.
backup=Path("app/src/main/java/com/benny/openlauncher/util/BackupHelper.java")
s=backup.read_text()
s=s.replace('"mimax_page_wallpapers.xml"\n    };','"mimax_page_wallpapers.xml",\n        "mimax_profiles.xml",\n        "mimax_theme_schedule.xml"\n    };')
backup.write_text(s)

print("Added switchable launcher profiles and daily Me Island theme scheduling with reboot restoration; included both in backup.")



# Extend folder rendering with a separate per-app hide-label switch.
group_popup = Path("app/src/main/java/com/benny/openlauncher/widget/GroupPopupView.java")
g = group_popup.read_text()
marker = "final View view = ItemViewFactory.getItemView(getContext(), callback, DragAction.Action.DESKTOP, groupItem);"
if "MiMaxPersonalization.applyFolder" not in g:
    if marker not in g:
        raise SystemExit("Could not find GroupPopupView item factory marker")
    g = g.replace(marker, marker + """
                if (view instanceof AppItemView) {
                    com.benny.openlauncher.mimax.MiMaxPersonalization.applyFolder(getContext(), (AppItemView) view, groupItem);
                }""", 1)
    group_popup.write_text(g)
