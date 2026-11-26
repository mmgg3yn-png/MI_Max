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
import com.benny.openlauncher.util.Tool;
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
        if(pkg!=null && p.contains("icon_size:"+pkg)) {
            view.setIconSize(Tool.dp2px(p.getInt("icon_size:"+pkg,48)));
            view.requestLayout();
            view.invalidate();
        }
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
            TextView iconSizeLabel=new TextView(this);iconSizeLabel.setTextColor(-1);iconSizeLabel.setText("Per-app icon size: "+prefs.getInt("icon_size:"+pkg,48)+" dp");card.addView(iconSizeLabel);
            SeekBar iconSize=new SeekBar(this);iconSize.setMax(40);iconSize.setProgress(Math.max(0,Math.min(40,prefs.getInt("icon_size:"+pkg,48)-32)));card.addView(iconSize);
            iconSize.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){public void onProgressChanged(SeekBar b,int v,boolean u){iconSizeLabel.setText("Per-app icon size: "+(v+32)+" dp");}public void onStartTrackingTouch(SeekBar b){}public void onStopTrackingTouch(SeekBar b){}});
            Button icon=new Button(this);icon.setText(prefs.contains("icon_uri:"+pkg)?"Change custom icon":"Choose custom icon");card.addView(icon);
            icon.setOnClickListener(v->{pendingIconPackage=pkg;Intent pick=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("image/*").addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(pick,PICK_ICON);});
            Button clearIcon=new Button(this);clearIcon.setText("Clear custom icon");clearIcon.setEnabled(prefs.contains("icon_uri:"+pkg));card.addView(clearIcon);
            clearIcon.setOnClickListener(v->{prefs.edit().remove("icon_uri:"+pkg).apply();clearIcon.setEnabled(false);icon.setText("Choose custom icon");});
            Button save=new Button(this);save.setText("Save "+label);card.addView(save);
            save.setOnClickListener(v->{String text=alias.getText().toString().trim();prefs.edit().putString("label:"+pkg,text).putBoolean("hide_home:"+pkg,home.isChecked()).putBoolean("hide_drawer:"+pkg,drawer.isChecked()).putBoolean("hide_folder:"+pkg,folder.isChecked()).putInt("icon_size:"+pkg,iconSize.getProgress()+32).apply();Toast.makeText(this,"Saved "+label,Toast.LENGTH_SHORT).show();});
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


# Local PIN gate for protected launcher settings and hidden-app management.
(JAVA / "MiMaxPrivacy.java").write_text(r'''package com.benny.openlauncher.mimax;
import android.content.Context;
import android.content.SharedPreferences;
import android.util.Base64;
import java.security.MessageDigest;
import java.security.SecureRandom;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

public final class MiMaxPrivacy {
 private static final String FILE="mimax_privacy";
 private static final int ITERATIONS=70000;
 private MiMaxPrivacy(){}
 public static boolean hasPin(Context c){return c.getSharedPreferences(FILE,0).contains("pin_hash");}
 public static boolean lockHidden(Context c){return c.getSharedPreferences(FILE,0).getBoolean("lock_hidden",false);}
 public static boolean lockSettings(Context c){return c.getSharedPreferences(FILE,0).getBoolean("lock_settings",false);}
 public static void setLocks(Context c,boolean hidden,boolean settings){c.getSharedPreferences(FILE,0).edit().putBoolean("lock_hidden",hidden).putBoolean("lock_settings",settings).apply();}
 public static void setPin(Context c,String pin) throws Exception {
  if(pin==null||!pin.matches("[0-9]{6,12}"))throw new IllegalArgumentException("PIN must contain 6 to 12 digits");
  byte[] salt=new byte[16];new SecureRandom().nextBytes(salt);
  byte[] hash=derive(pin,salt);
  c.getSharedPreferences(FILE,0).edit().putString("pin_salt",Base64.encodeToString(salt,Base64.NO_WRAP))
   .putString("pin_hash",Base64.encodeToString(hash,Base64.NO_WRAP)).apply();
 }
 public static boolean verify(Context c,String pin){
  try{
   SharedPreferences p=c.getSharedPreferences(FILE,0);
   String s=p.getString("pin_salt",null),h=p.getString("pin_hash",null);
   if(s==null||h==null||pin==null)return false;
   return MessageDigest.isEqual(derive(pin,Base64.decode(s,Base64.NO_WRAP)),Base64.decode(h,Base64.NO_WRAP));
  }catch(Exception e){return false;}
 }
 private static byte[] derive(String pin,byte[] salt)throws Exception{
  PBEKeySpec spec=new PBEKeySpec(pin.toCharArray(),salt,ITERATIONS,256);
  try{return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA1").generateSecret(spec).getEncoded();}
  finally{spec.clearPassword();}
 }
}
''')

(JAVA / "MiMaxPrivacyGateActivity.java").write_text(r'''package com.benny.openlauncher.mimax;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.widget.*;
import com.benny.openlauncher.activity.SettingsActivity;
import com.benny.openlauncher.activity.HideAppsActivity;

public final class MiMaxPrivacyGateActivity extends Activity {
 private EditText pin;
 private TextView status;
 private String target;
 private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
 @Override protected void onCreate(Bundle b){super.onCreate(b);target=getIntent().getStringExtra("target");
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setGravity(Gravity.CENTER);root.setPadding(dp(24),dp(24),dp(24),dp(24));root.setBackgroundColor(0xff101722);
  TextView title=new TextView(this);title.setText("Mi_Max privacy lock");title.setTextColor(-1);title.setTextSize(24);root.addView(title);
  TextView hint=new TextView(this);hint.setText("Enter your local PIN to continue.");hint.setTextColor(0xffc5d1df);hint.setPadding(0,dp(12),0,dp(12));root.addView(hint);
  pin=new EditText(this);pin.setSingleLine(true);pin.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_VARIATION_PASSWORD);pin.setHint("6–12 digit PIN");pin.setTextColor(-1);root.addView(pin);
  Button unlock=new Button(this);unlock.setText("Unlock");root.addView(unlock);unlock.setOnClickListener(v->unlock());
  Button cancel=new Button(this);cancel.setText("Cancel");root.addView(cancel);cancel.setOnClickListener(v->finish());
  status=new TextView(this);status.setTextColor(0xffffa1a1);root.addView(status);setContentView(root);
 }
 private void unlock(){
  if(!MiMaxPrivacy.verify(this,pin.getText().toString())){status.setText("Incorrect PIN");pin.setText("");return;}
  if("hidden".equals(target)){startActivity(new Intent(this,HideAppsActivity.class));}
  else if("settings".equals(target)){startActivity(new Intent(this,SettingsActivity.class).putExtra("mimax_verified",true));}
  finish();
 }
}
''')

(JAVA / "MiMaxPrivacySettingsActivity.java").write_text(r'''package com.benny.openlauncher.mimax;
import android.app.Activity;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.widget.*;

public final class MiMaxPrivacySettingsActivity extends Activity {
 private EditText first,confirm;
 private Switch hidden,settings;
 private TextView status;
 private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
 @Override protected void onCreate(Bundle b){super.onCreate(b);
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(20),dp(20),dp(20),dp(24));root.setBackgroundColor(0xff101722);
  TextView title=new TextView(this);title.setText("Privacy and app lock");title.setTextColor(-1);title.setTextSize(23);root.addView(title);
  TextView note=new TextView(this);note.setText("Protect the launcher's hidden-app list and settings pages with a local PIN. This is an in-launcher access gate, not an Android system app lock.");note.setTextColor(0xffc5d1df);note.setPadding(0,dp(8),0,dp(14));root.addView(note);
  first=new EditText(this);first.setSingleLine(true);first.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_VARIATION_PASSWORD);first.setHint(MiMaxPrivacy.hasPin(this)?"New PIN (6–12 digits)":"Create PIN (6–12 digits)");first.setTextColor(-1);root.addView(first);
  confirm=new EditText(this);confirm.setSingleLine(true);confirm.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_VARIATION_PASSWORD);confirm.setHint("Confirm PIN");confirm.setTextColor(-1);root.addView(confirm);
  Button save=new Button(this);save.setText(MiMaxPrivacy.hasPin(this)?"Change PIN":"Set PIN");root.addView(save);save.setOnClickListener(v->savePin());
  hidden=new Switch(this);hidden.setText("Require PIN before opening hidden apps list");hidden.setTextColor(-1);hidden.setChecked(MiMaxPrivacy.lockHidden(this));root.addView(hidden);
  settings=new Switch(this);settings.setText("Require PIN before opening launcher settings");settings.setTextColor(-1);settings.setChecked(MiMaxPrivacy.lockSettings(this));root.addView(settings);
  Button apply=new Button(this);apply.setText("Save privacy options");root.addView(apply);apply.setOnClickListener(v->{
   if((hidden.isChecked()||settings.isChecked())&&!MiMaxPrivacy.hasPin(this)){status.setText("Create a PIN before enabling protection");return;}
   MiMaxPrivacy.setLocks(this,hidden.isChecked(),settings.isChecked());status.setText("Privacy options saved");
  });
  Button remove=new Button(this);remove.setText("Remove PIN and locks");root.addView(remove);remove.setOnClickListener(v->{getSharedPreferences("mimax_privacy",0).edit().clear().apply();hidden.setChecked(false);settings.setChecked(false);status.setText("PIN and screen locks removed");});
  status=new TextView(this);status.setTextColor(0xffb8d9ff);status.setPadding(0,dp(12),0,0);root.addView(status);
  setContentView(root);
 }
 private void savePin(){
  String a=first.getText().toString(),b=confirm.getText().toString();
  if(!a.equals(b)){status.setText("PIN entries do not match");return;}
  try{MiMaxPrivacy.setPin(this,a);status.setText("PIN saved. Enable the protections below.");first.setText("");confirm.setText("");}
  catch(Exception e){status.setText(e.getMessage());}
 }
}
''')

manifest=BASE / "AndroidManifest.xml"
m=manifest.read_text()
if "com.benny.openlauncher.mimax.MiMaxPrivacySettingsActivity" not in m:
    m=m.replace("</application>",'''        <activity android:name="com.benny.openlauncher.mimax.MiMaxPrivacySettingsActivity" android:exported="false" android:label="Privacy and app lock" />
        <activity android:name="com.benny.openlauncher.mimax.MiMaxPrivacyGateActivity" android:exported="false" android:label="Mi_Max privacy lock" />
    </application>''',1)
manifest.write_text(m)

settings=Path("app/src/main/java/com/benny/openlauncher/activity/SettingsActivity.java")
s=settings.read_text()
anchor="        super.onCreate(b);"
replacement=anchor+'''
        if (com.benny.openlauncher.mimax.MiMaxPrivacy.lockSettings(this)
                && !getIntent().getBooleanExtra("mimax_verified", false)) {
            Intent gate = new Intent(this, com.benny.openlauncher.mimax.MiMaxPrivacyGateActivity.class);
            gate.putExtra("target", "settings");
            startActivity(gate);
            finish();
            return;
        }'''
if "MiMaxPrivacy.lockSettings" not in s:
    if anchor not in s: raise SystemExit("SettingsActivity onCreate anchor missing")
    settings.write_text(s.replace(anchor,replacement,1))

drawer=Path("app/src/main/java/com/benny/openlauncher/fragment/SettingsAppDrawerFragment.java")
s=drawer.read_text()
anchor='''                Intent intent = new Intent(getActivity(), HideAppsActivity.class);
                intent.addFlags(Intent.FLAG_ACTIVITY_NO_ANIMATION);
                startActivity(intent);
                return true;'''
replacement='''                if (com.benny.openlauncher.mimax.MiMaxPrivacy.lockHidden(getActivity())
                        && com.benny.openlauncher.mimax.MiMaxPrivacy.hasPin(getActivity())) {
                    Intent gate = new Intent(getActivity(), com.benny.openlauncher.mimax.MiMaxPrivacyGateActivity.class);
                    gate.putExtra("target", "hidden");
                    startActivity(gate);
                } else {
                    Intent intent = new Intent(getActivity(), HideAppsActivity.class);
                    intent.addFlags(Intent.FLAG_ACTIVITY_NO_ANIMATION);
                    startActivity(intent);
                }
                return true;'''
if "MiMaxPrivacy.lockHiddenApps" not in s:
    if anchor not in s: raise SystemExit("Settings drawer hidden apps anchor missing")
    drawer.write_text(s.replace(anchor,replacement,1))

master=BASE / "res/xml/preferences_master.xml"
p=master.read_text()
if "mimax_privacy_settings" not in p:
    entry='''    <PreferenceCategory android:title="Mi_Max Privacy">
        <Preference android:key="mimax_privacy_settings" android:title="Privacy and app lock"
            android:summary="Protect hidden apps and launcher settings with a local PIN">
            <intent android:targetPackage="com.mimax.launcher" android:targetClass="com.benny.openlauncher.mimax.MiMaxPrivacySettingsActivity" />
        </Preference>
    </PreferenceCategory>
'''
    p=p.replace("</PreferenceScreen>",entry+"</PreferenceScreen>",1)
master.write_text(p)

print("Added local PIN protection for hidden-app management and the Settings screen.")




# App Library: categorized installed-app catalogue with live search and package launch.
(JAVA / "MiMaxAppLibraryActivity.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.widget.*;
import com.benny.openlauncher.util.AppSettings;
import java.util.*;

public final class MiMaxAppLibraryActivity extends Activity {
 private LinearLayout list;
 private EditText search;
 private List<ResolveInfo> apps=new ArrayList<>();
 private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
 @Override protected void onCreate(Bundle b){super.onCreate(b);
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(16),dp(16),dp(16),dp(16));root.setBackgroundColor(0xff101722);
  TextView title=new TextView(this);title.setText("App Library");title.setTextSize(24);title.setTextColor(-1);root.addView(title);
  search=new EditText(this);search.setSingleLine(true);search.setHint("Search apps");search.setTextColor(-1);search.setHintTextColor(0xff91a1b4);root.addView(search);
  ScrollView scroll=new ScrollView(this);list=new LinearLayout(this);list.setOrientation(1);scroll.addView(list);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
  Intent i=new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER);
  @SuppressWarnings("deprecation") List<ResolveInfo> found=getPackageManager().queryIntentActivities(i,0);
  TreeMap<String,ResolveInfo> unique=new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
  for(ResolveInfo r:found)if(r.activityInfo!=null)unique.put(r.activityInfo.packageName,r);
  apps.addAll(unique.values());
  search.addTextChangedListener(new TextWatcher(){public void beforeTextChanged(CharSequence s,int st,int count,int after){}public void onTextChanged(CharSequence s,int st,int before,int count){render(s.toString());}public void afterTextChanged(Editable e){}});
  setContentView(root);render("");
 }
 private String category(ResolveInfo r){
  if(android.os.Build.VERSION.SDK_INT<26)return "Other apps";
  int c=r.activityInfo.applicationInfo.category;
  if(c==ApplicationInfo.CATEGORY_GAME)return "Games";
  if(c==ApplicationInfo.CATEGORY_AUDIO)return "Music and Audio";
  if(c==ApplicationInfo.CATEGORY_VIDEO)return "Video";
  if(c==ApplicationInfo.CATEGORY_IMAGE)return "Photos";
  if(c==ApplicationInfo.CATEGORY_SOCIAL)return "Social";
  if(c==ApplicationInfo.CATEGORY_NEWS)return "News";
  if(c==ApplicationInfo.CATEGORY_MAPS)return "Maps and Travel";
  if(c==ApplicationInfo.CATEGORY_PRODUCTIVITY)return "Productivity";
  return "Other apps";
 }
 private void render(String q){
  list.removeAllViews();
  Set<String> hidden=new HashSet<>(AppSettings.get().getHiddenAppsList());
  TreeMap<String,List<ResolveInfo>> groups=new TreeMap<>();
  for(ResolveInfo r:apps){
   String pkg=r.activityInfo.packageName;
   if(hidden.contains(pkg))continue;
   String name=r.loadLabel(getPackageManager()).toString();
   if(!name.toLowerCase(Locale.ROOT).contains(q.toLowerCase(Locale.ROOT))&&!pkg.toLowerCase(Locale.ROOT).contains(q.toLowerCase(Locale.ROOT)))continue;
   groups.computeIfAbsent(category(r),k->new ArrayList<>()).add(r);
  }
  for(Map.Entry<String,List<ResolveInfo>> group:groups.entrySet()){
   TextView heading=new TextView(this);heading.setText(group.getKey());heading.setTextColor(0xffb8d9ff);heading.setTextSize(17);heading.setPadding(0,dp(14),0,dp(6));list.addView(heading);
   for(ResolveInfo r:group.getValue()){
    LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(8),dp(7),dp(8),dp(7));row.setBackgroundColor(0xff202b39);
    LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=dp(5);list.addView(row,lp);
    ImageView icon=new ImageView(this);icon.setImageDrawable(r.loadIcon(getPackageManager()));row.addView(icon,new LinearLayout.LayoutParams(dp(40),dp(40)));
    TextView label=new TextView(this);label.setText(r.loadLabel(getPackageManager()));label.setTextColor(-1);label.setTextSize(14);label.setPadding(dp(12),0,0,0);row.addView(label,new LinearLayout.LayoutParams(0,-2,1));
    row.setOnClickListener(v->{try{Intent launch=new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER).setComponent(new ComponentName(r.activityInfo.packageName,r.activityInfo.name));launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);startActivity(launch);}catch(Exception ignored){}});
   }
  }
  if(list.getChildCount()==0){TextView empty=new TextView(this);empty.setText("No apps found");empty.setTextColor(-1);list.addView(empty);}
 }
}
''')

# Focus Mode: temporarily add selected packages to OpenLauncher's hidden-app list,
# preserving the user's original hidden list for exact restoration.
(JAVA / "MiMaxFocusModeActivity.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.os.Bundle;
import android.widget.*;
import com.benny.openlauncher.activity.HomeActivity;
import com.benny.openlauncher.util.AppSettings;
import java.util.*;

public final class MiMaxFocusModeActivity extends Activity {
 private static final String FILE="mimax_focus_mode";
 private android.content.SharedPreferences prefs;
 private LinearLayout list;
 private final HashSet<String> selected=new HashSet<>();
 private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
 @Override protected void onCreate(Bundle b){super.onCreate(b);prefs=getSharedPreferences(FILE,0);
  selected.addAll(prefs.getStringSet("selected",new HashSet<>()));
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(16),dp(16),dp(16),dp(20));root.setBackgroundColor(0xff101722);
  TextView title=new TextView(this);title.setText("Focus Mode");title.setTextSize(23);title.setTextColor(-1);root.addView(title);
  TextView note=new TextView(this);note.setText("Choose apps to hide temporarily from the launcher while Focus Mode is active. It does not block Android from opening those apps.");note.setTextColor(0xffc3cfdd);note.setPadding(0,dp(8),0,dp(12));root.addView(note);
  ScrollView scroll=new ScrollView(this);list=new LinearLayout(this);list.setOrientation(1);scroll.addView(list);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
  populate();
  Button save=new Button(this);save.setText("Save Focus selection");root.addView(save);save.setOnClickListener(v->{prefs.edit().putStringSet("selected",new HashSet<>(selected)).apply();Toast.makeText(this,"Focus selection saved",Toast.LENGTH_SHORT).show();});
  Button toggle=new Button(this);toggle.setText(prefs.getBoolean("active",false)?"Turn Focus Mode off":"Turn Focus Mode on");root.addView(toggle);toggle.setOnClickListener(v->{if(prefs.getBoolean("active",false))disableFocus();else enableFocus();toggle.setText(prefs.getBoolean("active",false)?"Turn Focus Mode off":"Turn Focus Mode on");});
  setContentView(root);
 }
 private void populate(){
  Intent intent=new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER);PackageManager pm=getPackageManager();
  @SuppressWarnings("deprecation") List<ResolveInfo> found=pm.queryIntentActivities(intent,0);
  TreeMap<String,ResolveInfo> unique=new TreeMap<>(String.CASE_INSENSITIVE_ORDER);for(ResolveInfo r:found)if(r.activityInfo!=null)unique.put(r.activityInfo.packageName,r);
  for(ResolveInfo r:unique.values()){
   String pkg=r.activityInfo.packageName;CheckBox box=new CheckBox(this);box.setText(r.loadLabel(pm)+"  ("+pkg+")");box.setTextColor(-1);box.setChecked(selected.contains(pkg));box.setEnabled(!prefs.getBoolean("active",false));
   box.setOnCheckedChangeListener((button,checked)->{if(checked)selected.add(pkg);else selected.remove(pkg);});
   list.addView(box);
  }
 }
 private void enableFocus(){
  ArrayList<String> old=AppSettings.get().getHiddenAppsList();
  prefs.edit().putString("previous_hidden",new org.json.JSONArray(old).toString()).putBoolean("active",true).apply();
  HashSet<String> combined=new HashSet<>(old);combined.addAll(selected);
  AppSettings.get().setHiddenAppsList(new ArrayList<>(combined));
  refreshHome();Toast.makeText(this,"Focus Mode enabled",Toast.LENGTH_SHORT).show();
 }
 private void disableFocus(){
  try{org.json.JSONArray a=new org.json.JSONArray(prefs.getString("previous_hidden","[]"));ArrayList<String> restore=new ArrayList<>();for(int i=0;i<a.length();i++)restore.add(a.getString(i));AppSettings.get().setHiddenAppsList(restore);}
  catch(Exception e){Toast.makeText(this,"Could not restore the previous hidden-app list",Toast.LENGTH_LONG).show();return;}
  prefs.edit().remove("previous_hidden").putBoolean("active",false).apply();
  refreshHome();Toast.makeText(this,"Focus Mode disabled",Toast.LENGTH_SHORT).show();
 }
 private void refreshHome(){if(HomeActivity._launcher!=null)HomeActivity._launcher.recreate();}
}
''')

manifest=BASE / "AndroidManifest.xml"
m=manifest.read_text()
if "com.benny.openlauncher.mimax.MiMaxAppLibraryActivity" not in m:
 m=m.replace("</application>",'''        <activity android:name="com.benny.openlauncher.mimax.MiMaxAppLibraryActivity" android:exported="false" android:label="App Library" />
        <activity android:name="com.benny.openlauncher.mimax.MiMaxFocusModeActivity" android:exported="false" android:label="Focus Mode" />
    </application>''',1)
manifest.write_text(m)

master=BASE / "res/xml/preferences_master.xml"
p=master.read_text()
if "mimax_app_library" not in p:
 entry='''    <PreferenceCategory android:title="Mi_Max Apps and Focus">
        <Preference android:key="mimax_app_library" android:title="App Library"
            android:summary="Browse installed apps in automatic categories with search">
            <intent android:targetPackage="com.mimax.launcher" android:targetClass="com.benny.openlauncher.mimax.MiMaxAppLibraryActivity" />
        </Preference>
        <Preference android:key="mimax_focus_mode" android:title="Focus Mode"
            android:summary="Temporarily hide selected apps from the launcher">
            <intent android:targetPackage="com.mimax.launcher" android:targetClass="com.benny.openlauncher.mimax.MiMaxFocusModeActivity" />
        </Preference>
    </PreferenceCategory>
'''
 p=p.replace("</PreferenceScreen>",entry+"</PreferenceScreen>",1)
master.write_text(p)

# Back up Focus Mode state alongside launcher profiles.
backup=Path("app/src/main/java/com/benny/openlauncher/util/BackupHelper.java")
s=backup.read_text()
s=s.replace('"mimax_theme_schedule.xml"\n    };','"mimax_theme_schedule.xml",\n        "mimax_focus_mode.xml",\n        "mimax_privacy.xml"\n    };')
backup.write_text(s)

print("Integrated App Library, searchable category groups and temporary Focus Mode with restoration of the prior hidden-app selection.")




# Real Android AppWidgetHost smart stack anchored to the launcher's root overlay.
(JAVA / "MiMaxSmartStackView.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.appwidget.AppWidgetHostView;
import android.appwidget.AppWidgetProviderInfo;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.drawable.GradientDrawable;
import android.util.AttributeSet;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import com.benny.openlauncher.activity.HomeActivity;
import org.json.JSONArray;
import java.util.*;

public final class MiMaxSmartStackView extends LinearLayout {
 private static final String PREFS="mimax_smart_widgets";
 private static final int ROTATE_MS=15000;
 private final TextView header;
 private final FrameLayout widgetFrame;
 private final android.os.Handler handler=new android.os.Handler(android.os.Looper.getMainLooper());
 private boolean expanded=false;
 private int index=0;
 private float downX,downY;
 private final Runnable autoRotate=new Runnable(){public void run(){if(expanded){cycle(1);handler.postDelayed(this,ROTATE_MS);}}};
 public MiMaxSmartStackView(Context c,AttributeSet a){super(c,a);setOrientation(VERTICAL);setPadding(dp(8),dp(6),dp(8),dp(8));
  GradientDrawable bg=new GradientDrawable();bg.setColor(0xee182230);bg.setCornerRadius(dp(22));bg.setStroke(dp(1),0x557eb5e8);setBackground(bg);setElevation(dp(12));
  header=new TextView(c);header.setTextColor(Color.WHITE);header.setTextSize(13);header.setGravity(Gravity.CENTER);header.setText("Smart Stack +");header.setPadding(dp(8),dp(8),dp(8),dp(8));addView(header,new LayoutParams(-1,dp(34)));
  widgetFrame=new FrameLayout(c);addView(widgetFrame,new LayoutParams(-1,dp(142)));widgetFrame.setVisibility(GONE);
  header.setOnClickListener(v->toggle());
  header.setOnLongClickListener(v->{openManager();return true;});
  header.setOnTouchListener((v,e)->{
   if(e.getAction()==MotionEvent.ACTION_DOWN){downX=e.getRawX();downY=e.getRawY();return true;}
   if(e.getAction()==MotionEvent.ACTION_UP){
    float dx=e.getRawX()-downX,dy=e.getRawY()-downY;
    if(Math.abs(dx)>dp(28)&&Math.abs(dx)>Math.abs(dy)){cycle(dx<0?1:-1);return true;}
    if(Math.abs(dy)>dp(28)){if(dy<0)expand();else collapse();return true;}
    v.performClick();return true;
   }return true;
  });
  post(this::refreshWidgets);
 }
 private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
 private int[] ids(){
  try{JSONArray a=new JSONArray(getContext().getSharedPreferences(PREFS,0).getString("ids","[]"));int[] out=new int[a.length()];for(int i=0;i<a.length();i++)out[i]=a.getInt(i);return out;}
  catch(Exception e){return new int[0];}
 }
 public void refreshWidgets(){
  int[] all=ids();
  if(all.length==0){header.setText("Smart Stack +");widgetFrame.removeAllViews();if(expanded)collapse();return;}
  index=((index%all.length)+all.length)%all.length;
  if(!expanded){header.setText("Smart Stack  •  "+all.length+" widgets");return;}
  header.setText("Smart Stack  •  "+(index+1)+"/"+all.length+"  ↻");
  widgetFrame.removeAllViews();
  if(HomeActivity._appWidgetHost==null||HomeActivity._appWidgetManager==null){TextView wait=new TextView(getContext());wait.setText("Widget host is starting…");wait.setTextColor(Color.WHITE);widgetFrame.addView(wait);return;}
  int id=all[index];AppWidgetProviderInfo info=HomeActivity._appWidgetManager.getAppWidgetInfo(id);
  if(info==null){TextView gone=new TextView(getContext());gone.setText("Widget unavailable — long press to manage");gone.setTextColor(Color.WHITE);widgetFrame.addView(gone);return;}
  try{
   AppWidgetHostView view=HomeActivity._appWidgetHost.createView(getContext(),id,info);
   view.setAppWidget(id,info);
   widgetFrame.addView(view,new FrameLayout.LayoutParams(-1,-1));
  }catch(Exception e){TextView error=new TextView(getContext());error.setText("Could not load this widget");error.setTextColor(Color.WHITE);widgetFrame.addView(error);}
 }
 private void toggle(){if(expanded){cycle(1);}else expand();}
 private void expand(){
  if(ids().length==0){openManager();return;}
  expanded=true;widgetFrame.setVisibility(VISIBLE);LayoutParams p=(LayoutParams)getLayoutParams();if(p!=null){p.height=dp(188);setLayoutParams(p);}
  refreshWidgets();handler.removeCallbacks(autoRotate);handler.postDelayed(autoRotate,ROTATE_MS);
 }
 private void collapse(){expanded=false;handler.removeCallbacks(autoRotate);widgetFrame.setVisibility(GONE);LayoutParams p=(LayoutParams)getLayoutParams();if(p!=null){p.height=dp(46);setLayoutParams(p);}refreshWidgets();}
 private void cycle(int direction){int[] all=ids();if(all.length==0){openManager();return;}index=(index+direction+all.length)%all.length;if(!expanded)expand();else refreshWidgets();}
 private void openManager(){try{getContext().startActivity(new Intent(getContext(),MiMaxSmartStackActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));}catch(Exception ignored){}}
 @Override protected void onAttachedToWindow(){super.onAttachedToWindow();post(this::refreshWidgets);}
 @Override protected void onDetachedFromWindow(){handler.removeCallbacksAndMessages(null);super.onDetachedFromWindow();}
}
''')

(JAVA / "MiMaxSmartStackActivity.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.Activity;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProviderInfo;
import android.content.Intent;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.*;
import com.benny.openlauncher.activity.HomeActivity;
import org.json.JSONArray;
import java.util.*;

public final class MiMaxSmartStackActivity extends Activity {
 private static final int PICK=9211,CONFIGURE=9212;
 private static final String PREFS="mimax_smart_widgets";
 private int pendingId=-1;
 private LinearLayout list;
 private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
 @Override protected void onCreate(Bundle b){super.onCreate(b);
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(18),dp(18),dp(18),dp(24));root.setBackgroundColor(0xff101722);
  TextView title=new TextView(this);title.setText("Smart Widget Stack");title.setTextSize(23);title.setTextColor(-1);root.addView(title);
  TextView note=new TextView(this);note.setText("Add real Android widgets from installed providers. The home-screen stack can be expanded, swiped between widgets, or automatically rotate every 15 seconds.");note.setTextColor(0xffc4d0df);note.setPadding(0,dp(8),0,dp(12));root.addView(note);
  Button add=new Button(this);add.setText("Add Android widget");root.addView(add);add.setOnClickListener(v->pickWidget());
  list=new LinearLayout(this);list.setOrientation(1);root.addView(list,new LinearLayout.LayoutParams(-1,0,1));
  Button refresh=new Button(this);refresh.setText("Refresh Smart Stack on home screen");root.addView(refresh);refresh.setOnClickListener(v->{refreshHome();Toast.makeText(this,"Smart Stack refreshed",Toast.LENGTH_SHORT).show();});
  setContentView(root);refreshList();
 }
 private int[] ids(){try{JSONArray a=new JSONArray(getSharedPreferences(PREFS,0).getString("ids","[]"));int[] out=new int[a.length()];for(int i=0;i<a.length();i++)out[i]=a.getInt(i);return out;}catch(Exception e){return new int[0];}}
 private void save(int[] values){JSONArray a=new JSONArray();for(int id:values)a.put(id);getSharedPreferences(PREFS,0).edit().putString("ids",a.toString()).apply();}
 private void pickWidget(){
  if(HomeActivity._appWidgetHost==null||HomeActivity._appWidgetManager==null){Toast.makeText(this,"Open the launcher home screen first",Toast.LENGTH_LONG).show();return;}
  pendingId=HomeActivity._appWidgetHost.allocateAppWidgetId();
  Intent i=new Intent("android.appwidget.action.APPWIDGET_PICK");i.putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID,pendingId);
  try{startActivityForResult(i,PICK);}catch(Exception e){HomeActivity._appWidgetHost.deleteAppWidgetId(pendingId);pendingId=-1;Toast.makeText(this,"Android widget picker is unavailable",Toast.LENGTH_LONG).show();}
 }
 private void savePending(){
  if(pendingId<0)return;int[] old=ids();int[] next=Arrays.copyOf(old,old.length+1);next[old.length]=pendingId;save(next);pendingId=-1;refreshList();refreshHome();
 }
 @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);
  if(request==PICK){
   if(result!=RESULT_OK){if(pendingId>=0)HomeActivity._appWidgetHost.deleteAppWidgetId(pendingId);pendingId=-1;return;}
   if(data!=null)pendingId=data.getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID,pendingId);
   AppWidgetProviderInfo info=HomeActivity._appWidgetManager.getAppWidgetInfo(pendingId);
   if(info!=null&&info.configure!=null){
    Intent config=new Intent(AppWidgetManager.ACTION_APPWIDGET_CONFIGURE).setComponent(info.configure).putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID,pendingId);
    startActivityForResult(config,CONFIGURE);
   }else savePending();
  }else if(request==CONFIGURE){if(result==RESULT_OK)savePending();else if(pendingId>=0)HomeActivity._appWidgetHost.deleteAppWidgetId(pendingId);pendingId=-1;}
 }
 private void refreshList(){
  list.removeAllViews();int[] all=ids();
  if(all.length==0){TextView empty=new TextView(this);empty.setText("No widgets in the stack yet.");empty.setTextColor(-1);list.addView(empty);return;}
  for(int id:all){
   AppWidgetProviderInfo info=HomeActivity._appWidgetManager==null?null:HomeActivity._appWidgetManager.getAppWidgetInfo(id);
   String label=info==null?"Unavailable widget #"+id:info.loadLabel(getPackageManager()).toString();
   LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(0,dp(6),0,dp(6));list.addView(row);
   TextView name=new TextView(this);name.setText(label);name.setTextColor(-1);name.setTextSize(15);row.addView(name,new LinearLayout.LayoutParams(0,-2,1));
   Button remove=new Button(this);remove.setText("Remove");row.addView(remove);remove.setOnClickListener(v->removeWidget(id));
  }
 }
 private void removeWidget(int id){
  int[] old=ids();ArrayList<Integer> keep=new ArrayList<>();for(int x:old)if(x!=id)keep.add(x);
  int[] next=new int[keep.size()];for(int i=0;i<next.length;i++)next[i]=keep.get(i);save(next);
  if(HomeActivity._appWidgetHost!=null)HomeActivity._appWidgetHost.deleteAppWidgetId(id);
  refreshList();refreshHome();
 }
 private void refreshHome(){
  if(HomeActivity._launcher!=null){MiMaxSmartStackView view=HomeActivity._launcher.findViewById(com.benny.openlauncher.R.id.mimax_smart_stack);if(view!=null)view.refreshWidgets();}
 }
}
''')

layout=BASE / "res/layout/activity_home.xml"
xml=layout.read_text()
if "MiMaxSmartStackView" not in xml:
    xml=xml.replace("</FrameLayout>",'''    <com.benny.openlauncher.mimax.MiMaxSmartStackView
        android:id="@+id/mimax_smart_stack"
        android:layout_width="232dp"
        android:layout_height="46dp"
        android:layout_gravity="bottom|end"
        android:layout_margin="10dp" />
</FrameLayout>''',1)
layout.write_text(xml)

manifest=BASE / "AndroidManifest.xml"
m=manifest.read_text()
if "com.benny.openlauncher.mimax.MiMaxSmartStackActivity" not in m:
    m=m.replace("</application>",'''        <activity android:name="com.benny.openlauncher.mimax.MiMaxSmartStackActivity" android:exported="false" android:label="Smart Widget Stack" />
    </application>''',1)
manifest.write_text(m)

master=BASE / "res/xml/preferences_master.xml"
p=master.read_text()
if "mimax_smart_stack" not in p:
    entry='''    <PreferenceCategory android:title="Mi_Max Widgets">
        <Preference android:key="mimax_smart_stack" android:title="Smart Widget Stack"
            android:summary="Add and rotate real Android widgets in a home-screen stack">
            <intent android:targetPackage="com.mimax.launcher" android:targetClass="com.benny.openlauncher.mimax.MiMaxSmartStackActivity" />
        </Preference>
    </PreferenceCategory>
'''
    p=p.replace("</PreferenceScreen>",entry+"</PreferenceScreen>",1)
master.write_text(p)

backup=Path("app/src/main/java/com/benny/openlauncher/util/BackupHelper.java")
s=backup.read_text()
s=s.replace('"mimax_privacy.xml"\n    };','"mimax_privacy.xml",\n        "mimax_smart_widgets.xml"\n    };')
backup.write_text(s)

print("Added a real AppWidgetHost smart stack overlay on the launcher home screen, provider picker/configuration, swipe/tap cycling and timed rotation.")




# Native Mi_Max assistant with a live OpenRouter free-model catalogue.
(JAVA / "MiMaxAiActivity.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.Activity;
import android.os.Build;
import android.os.Bundle;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.text.InputType;
import android.view.Gravity;
import android.widget.*;
import android.content.*;
import android.util.Base64;
import org.json.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.util.*;
import java.util.concurrent.*;
import javax.crypto.*;
import javax.crypto.spec.GCMParameterSpec;

public final class MiMaxAiActivity extends Activity {
 private static final String FILE="mimax_ai",ALIAS="mimax_openrouter_key";
 private static final String BASE="https://openrouter.ai/api/v1";
 private final ExecutorService worker=Executors.newSingleThreadExecutor();
 private final ArrayList<JSONObject> history=new ArrayList<>();
 private EditText keyInput,prompt;
 private Spinner models;
 private TextView output,status,tempLabel;
 private SeekBar temperature;
 private ArrayAdapter<String> adapter;
 private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
 @Override protected void onCreate(Bundle b){super.onCreate(b);
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(16),dp(16),dp(16),dp(16));root.setBackgroundColor(0xff101722);
  TextView title=new TextView(this);title.setText("Mi_Max AI Assistant");title.setTextSize(23);title.setTextColor(-1);root.addView(title);
  TextView privacy=new TextView(this);privacy.setText("Requests are sent to OpenRouter over HTTPS. Your API key is stored locally using Android Keystore encryption on Android 6.0 and newer.");privacy.setTextColor(0xffc0ccda);privacy.setPadding(0,dp(6),0,dp(10));root.addView(privacy);
  keyInput=new EditText(this);keyInput.setSingleLine(true);keyInput.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);keyInput.setHint(hasKey()?"API key saved — enter to replace":"OpenRouter API key");keyInput.setTextColor(-1);root.addView(keyInput);
  Button saveKey=new Button(this);saveKey.setText("Save API key securely");root.addView(saveKey);saveKey.setOnClickListener(v->saveKey());
  LinearLayout modelRow=new LinearLayout(this);modelRow.setGravity(Gravity.CENTER_VERTICAL);root.addView(modelRow);
  models=new Spinner(this);adapter=new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new ArrayList<>());models.setAdapter(adapter);modelRow.addView(models,new LinearLayout.LayoutParams(0,-2,1));
  Button load=new Button(this);load.setText("Load free models");modelRow.addView(load);load.setOnClickListener(v->loadModels());
  tempLabel=new TextView(this);tempLabel.setTextColor(-1);root.addView(tempLabel);
  temperature=new SeekBar(this);temperature.setMax(100);temperature.setProgress(Math.round(getSharedPreferences(FILE,0).getFloat("temperature",0.7f)*100));root.addView(temperature);
  temperature.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){public void onProgressChanged(SeekBar s,int p,boolean u){tempLabel.setText(String.format(Locale.US,"Temperature: %.2f",p/100f));getSharedPreferences(FILE,0).edit().putFloat("temperature",p/100f).apply();}public void onStartTrackingTouch(SeekBar s){}public void onStopTrackingTouch(SeekBar s){}});
  ScrollView transcriptScroll=new ScrollView(this);output=new TextView(this);output.setTextColor(0xffe5edf5);output.setTextSize(14);output.setPadding(dp(10),dp(10),dp(10),dp(10));transcriptScroll.addView(output);transcriptScroll.setBackgroundColor(0xff202b39);root.addView(transcriptScroll,new LinearLayout.LayoutParams(-1,0,1));
  prompt=new EditText(this);prompt.setTextColor(-1);prompt.setHintTextColor(0xff98a8ba);prompt.setHint("Ask Mi_Max AI");prompt.setMinLines(2);prompt.setGravity(Gravity.TOP);root.addView(prompt);
  Button send=new Button(this);send.setText("Send");root.addView(send);send.setOnClickListener(v->sendMessage());
  status=new TextView(this);status.setTextColor(0xffb8d9ff);root.addView(status);
  setContentView(root);updateTempLabel();restoreModel();
 }
 private void updateTempLabel(){tempLabel.setText(String.format(Locale.US,"Temperature: %.2f",temperature.getProgress()/100f));}
 private boolean hasKey(){return getSharedPreferences(FILE,0).contains("key_cipher")||getSharedPreferences(FILE,0).contains("key_legacy");}
 private void saveKey(){
  String key=keyInput.getText().toString().trim();if(key.isEmpty()){status.setText("Enter your OpenRouter API key");return;}
  try{
   if(Build.VERSION.SDK_INT>=23){
    KeyStore ks=KeyStore.getInstance("AndroidKeyStore");ks.load(null);
    if(!ks.containsAlias(ALIAS)){KeyGenerator gen=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");gen.init(new KeyGenParameterSpec.Builder(ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setRandomizedEncryptionRequired(true).build());gen.generateKey();}
    SecretKey secret=(SecretKey)ks.getKey(ALIAS,null);Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.ENCRYPT_MODE,secret);
    byte[] encrypted=cipher.doFinal(key.getBytes(StandardCharsets.UTF_8));
    getSharedPreferences(FILE,0).edit().putString("key_iv",Base64.encodeToString(cipher.getIV(),Base64.NO_WRAP)).putString("key_cipher",Base64.encodeToString(encrypted,Base64.NO_WRAP)).remove("key_legacy").apply();
   }else getSharedPreferences(FILE,0).edit().putString("key_legacy",key).apply();
   keyInput.setText("");keyInput.setHint("API key saved");status.setText("API key saved locally");
  }catch(Exception e){status.setText("Could not secure API key: "+e.getMessage());}
 }
 private String readKey(){
  try{
   if(Build.VERSION.SDK_INT<23)return getSharedPreferences(FILE,0).getString("key_legacy",null);
   String iv=getSharedPreferences(FILE,0).getString("key_iv",null),data=getSharedPreferences(FILE,0).getString("key_cipher",null);
   if(iv==null||data==null)return null;
   KeyStore ks=KeyStore.getInstance("AndroidKeyStore");ks.load(null);SecretKey secret=(SecretKey)ks.getKey(ALIAS,null);
   Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.DECRYPT_MODE,secret,new GCMParameterSpec(128,Base64.decode(iv,Base64.NO_WRAP)));
   return new String(cipher.doFinal(Base64.decode(data,Base64.NO_WRAP)),StandardCharsets.UTF_8);
  }catch(Exception e){return null;}
 }
 private void restoreModel(){
  String m=getSharedPreferences(FILE,0).getString("model","");
  if(!m.isEmpty()){adapter.add(m);adapter.notifyDataSetChanged();}
 }
 private void loadModels(){
  status.setText("Loading OpenRouter free models…");
  worker.execute(()->{
   try{
    JSONObject response=request("GET",BASE+"/models",null,null);
    JSONArray data=response.optJSONArray("data");ArrayList<String> free=new ArrayList<>();
    if(data!=null)for(int i=0;i<data.length();i++){
     JSONObject item=data.optJSONObject(i);if(item==null)continue;
     String id=item.optString("id","");JSONObject price=item.optJSONObject("pricing");
     boolean isFree=id.endsWith(":free");
     if(price!=null){double in=parsePrice(price.optString("prompt","-1")),out=parsePrice(price.optString("completion","-1"));isFree=isFree||(in==0.0&&out==0.0);}
     if(isFree&&!id.isEmpty())free.add(id);
    }
    Collections.sort(free);
    runOnUiThread(()->{
     String selected=getSharedPreferences(FILE,0).getString("model","");
     adapter.clear();adapter.addAll(free);adapter.notifyDataSetChanged();
     int i=free.indexOf(selected);if(i>=0)models.setSelection(i);
     status.setText("Loaded "+free.size()+" free models");
    });
   }catch(Exception e){runOnUiThread(()->status.setText("Model list error: "+e.getMessage()));}
  });
 }
 private double parsePrice(String s){try{return Double.parseDouble(s);}catch(Exception e){return -1;}}
 private void sendMessage(){
  String text=prompt.getText().toString().trim();if(text.isEmpty())return;
  String key=readKey();if(key==null||key.isEmpty()){status.setText("Save your OpenRouter API key first");return;}
  Object chosen=models.getSelectedItem();String model=chosen==null?"":chosen.toString();
  if(model.isEmpty()){status.setText("Load and select a free model first");return;}
  prompt.setText("");append("You",text);status.setText("Thinking…");
  worker.execute(()->{
   try{
    history.add(new JSONObject().put("role","user").put("content",text));
    while(history.size()>20)history.remove(0);
    JSONArray messages=new JSONArray();for(JSONObject m:history)messages.put(m);
    JSONObject body=new JSONObject().put("model",model).put("messages",messages).put("temperature",temperature.getProgress()/100.0).put("max_tokens",1024);
    JSONObject result=request("POST",BASE+"/chat/completions",body,key);
    JSONArray choices=result.optJSONArray("choices");if(choices==null||choices.length()==0)throw new IOException("The model returned no answer");
    String answer=choices.getJSONObject(0).getJSONObject("message").optString("content","");
    if(answer.isEmpty())throw new IOException("The model returned an empty answer");
    history.add(new JSONObject().put("role","assistant").put("content",answer));
    getSharedPreferences(FILE,0).edit().putString("model",model).apply();
    runOnUiThread(()->{append("Mi_Max",answer);status.setText("Model: "+model);});
   }catch(Exception e){runOnUiThread(()->status.setText("Request failed: "+e.getMessage()));}
  });
 }
 private JSONObject request(String method,String address,JSONObject body,String key)throws Exception{
  HttpURLConnection connection=(HttpURLConnection)new URL(address).openConnection();
  connection.setRequestMethod(method);connection.setConnectTimeout(15000);connection.setReadTimeout(45000);connection.setRequestProperty("Accept","application/json");
  if(key!=null){connection.setRequestProperty("Authorization","Bearer "+key);connection.setRequestProperty("HTTP-Referer","https://github.com/mmgg3yn-png/MI_Max");connection.setRequestProperty("X-Title","Mi_Max Launcher");}
  if(body!=null){connection.setDoOutput(true);connection.setRequestProperty("Content-Type","application/json");try(OutputStream out=connection.getOutputStream()){out.write(body.toString().getBytes(StandardCharsets.UTF_8));}}
  int code=connection.getResponseCode();InputStream stream=code>=200&&code<300?connection.getInputStream():connection.getErrorStream();
  StringBuilder json=new StringBuilder();if(stream!=null)try(BufferedReader br=new BufferedReader(new InputStreamReader(stream,StandardCharsets.UTF_8))){String line;while((line=br.readLine())!=null)json.append(line);}
  connection.disconnect();
  JSONObject parsed=new JSONObject(json.toString());
  if(code<200||code>=300){JSONObject err=parsed.optJSONObject("error");throw new IOException(err==null?"HTTP "+code:err.optString("message","HTTP "+code));}
  return parsed;
 }
 private void append(String who,String text){output.append("\n"+who+":\n"+text+"\n");}
 @Override protected void onDestroy(){worker.shutdownNow();super.onDestroy();}
}
''')

manifest=BASE / "AndroidManifest.xml"
m=manifest.read_text()
if "com.benny.openlauncher.mimax.MiMaxAiActivity" not in m:
    m=m.replace("</application>",'''        <activity android:name="com.benny.openlauncher.mimax.MiMaxAiActivity" android:exported="false" android:label="Mi_Max AI Assistant" />
    </application>''',1)
manifest.write_text(m)

master=BASE / "res/xml/preferences_master.xml"
p=master.read_text()
if "mimax_ai_assistant" not in p:
    entry='''    <PreferenceCategory android:title="Mi_Max AI">
        <Preference android:key="mimax_ai_assistant" android:title="Mi_Max AI Assistant"
            android:summary="Choose a real OpenRouter free model and chat from the launcher">
            <intent android:targetPackage="com.mimax.launcher" android:targetClass="com.benny.openlauncher.mimax.MiMaxAiActivity" />
        </Preference>
    </PreferenceCategory>
'''
    p=p.replace("</PreferenceScreen>",entry+"</PreferenceScreen>",1)
master.write_text(p)

backup=Path("app/src/main/java/com/benny/openlauncher/util/BackupHelper.java")
s=backup.read_text()
s=s.replace('"mimax_smart_widgets.xml"\n    };','"mimax_smart_widgets.xml",\n        "mimax_ai.xml"\n    };')
backup.write_text(s)

print("Added Mi_Max AI chat, encrypted local API key on supported Android versions, live catalogue of actual free OpenRouter models and temperature setting.")




# Spotlight: search installed apps, recent launches, settings destinations and optional contacts.
(JAVA / "MiMaxSpotlightUsage.java").write_text(r'''package com.benny.openlauncher.mimax;
import android.content.Context;
import android.content.ComponentName;
import android.content.Intent;
import android.content.SharedPreferences;
import java.util.*;
public final class MiMaxSpotlightUsage {
 private MiMaxSpotlightUsage(){}
 public static void record(Context c,Intent intent){
  if(intent==null)return;String pkg=null;
  try{ComponentName n=intent.getComponent();pkg=n!=null?n.getPackageName():intent.getPackage();}catch(Exception ignored){}
  if(pkg==null||pkg.isEmpty()||pkg.equals(c.getPackageName()))return;
  SharedPreferences p=c.getSharedPreferences("mimax_spotlight",0);
  p.edit().putInt("count:"+pkg,p.getInt("count:"+pkg,0)+1).putLong("last:"+pkg,System.currentTimeMillis()).apply();
 }
 public static List<String> recent(Context c,int limit){
  SharedPreferences p=c.getSharedPreferences("mimax_spotlight",0);
  ArrayList<Map.Entry<String,Long>> entries=new ArrayList<>();
  for(Map.Entry<String,?> e:p.getAll().entrySet())if(e.getKey().startsWith("last:")&&e.getValue() instanceof Long)
   entries.add(new AbstractMap.SimpleEntry<>(e.getKey().substring(5),(Long)e.getValue()));
  Collections.sort(entries,(a,b)->Long.compare(b.getValue(),a.getValue()));
  ArrayList<String> result=new ArrayList<>();for(Map.Entry<String,Long> e:entries){if(result.size()>=limit)break;result.add(e.getKey());}
  return result;
 }
}
''')

(JAVA / "MiMaxSpotlightButton.java").write_text(r'''package com.benny.openlauncher.mimax;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.util.AttributeSet;
import android.view.Gravity;
import android.widget.FrameLayout;
import android.widget.TextView;
public final class MiMaxSpotlightButton extends FrameLayout {
 public MiMaxSpotlightButton(Context c,AttributeSet a){super(c,a);
  TextView label=new TextView(c);label.setText("⌕  Search");label.setTextColor(Color.WHITE);label.setTextSize(13);label.setGravity(Gravity.CENTER);label.setPadding(dp(12),dp(8),dp(12),dp(8));
  GradientDrawable bg=new GradientDrawable();bg.setColor(0xee182230);bg.setCornerRadius(dp(22));bg.setStroke(dp(1),0x557eb5e8);label.setBackground(bg);label.setElevation(dp(12));addView(label,new FrameLayout.LayoutParams(-1,-1));
  setOnClickListener(v->c.startActivity(new Intent(c,MiMaxSpotlightActivity.class)));
 }
 private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
}
''')

(JAVA / "MiMaxSpotlightActivity.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.Manifest;
import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.database.Cursor;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.ContactsContract;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.widget.*;
import com.benny.openlauncher.activity.SettingsActivity;
import com.benny.openlauncher.activity.HomeActivity;
import com.benny.openlauncher.util.AppSettings;
import java.util.*;

public final class MiMaxSpotlightActivity extends Activity {
 private static final int CONTACTS_PERMISSION=9411;
 private LinearLayout results;
 private EditText query;
 private final ArrayList<ResolveInfo> apps=new ArrayList<>();
 private final HashMap<String,ResolveInfo> byPackage=new HashMap<>();
 private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
 @Override protected void onCreate(Bundle b){super.onCreate(b);
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(16),dp(16),dp(16),dp(16));root.setBackgroundColor(0xff101722);
  TextView title=new TextView(this);title.setText("Spotlight");title.setTextColor(-1);title.setTextSize(24);root.addView(title);
  query=new EditText(this);query.setSingleLine(true);query.setHint("Search apps, contacts and settings");query.setTextColor(-1);query.setHintTextColor(0xff9aabba);root.addView(query);
  Button contacts=new Button(this);contacts.setText("Enable contact search");root.addView(contacts);contacts.setOnClickListener(v->requestContacts());
  ScrollView scroll=new ScrollView(this);results=new LinearLayout(this);results.setOrientation(1);scroll.addView(results);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
  Intent launch=new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER);PackageManager pm=getPackageManager();
  @SuppressWarnings("deprecation") List<ResolveInfo> found=pm.queryIntentActivities(launch,0);
  TreeMap<String,ResolveInfo> unique=new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
  for(ResolveInfo r:found)if(r.activityInfo!=null)unique.put(r.activityInfo.packageName,r);
  apps.addAll(unique.values());for(ResolveInfo r:apps)byPackage.put(r.activityInfo.packageName,r);
  query.addTextChangedListener(new TextWatcher(){public void beforeTextChanged(CharSequence s,int st,int count,int after){}public void onTextChanged(CharSequence s,int st,int before,int count){render(s.toString());}public void afterTextChanged(Editable e){}});
  setContentView(root);render("");
 }
 private boolean hasContactsPermission(){return Build.VERSION.SDK_INT<23||checkSelfPermission(Manifest.permission.READ_CONTACTS)==PackageManager.PERMISSION_GRANTED;}
 private void requestContacts(){if(Build.VERSION.SDK_INT>=23&&!hasContactsPermission())requestPermissions(new String[]{Manifest.permission.READ_CONTACTS},CONTACTS_PERMISSION);else render(query.getText().toString());}
 @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] grants){super.onRequestPermissionsResult(request,permissions,grants);if(request==CONTACTS_PERMISSION)render(query.getText().toString());}
 private boolean match(String text,String q){return text!=null&&text.toLowerCase(Locale.ROOT).contains(q.toLowerCase(Locale.ROOT));}
 private void render(String raw){
  results.removeAllViews();String q=raw.trim();
  Set<String> hidden=new HashSet<>(AppSettings.get().getHiddenAppsList());
  if(q.isEmpty()){
   section("Recent apps");
   int shown=0;
   for(String pkg:MiMaxSpotlightUsage.recent(this,8)){ResolveInfo r=byPackage.get(pkg);if(r!=null&&!hidden.contains(pkg)){appRow(r,"Recently used");shown++;}}
   if(shown==0)textRow("No recent apps yet","Apps you launch from the home screen appear here");
  }
  section("Apps");
  int count=0;
  for(ResolveInfo r:apps){String pkg=r.activityInfo.packageName,name=r.loadLabel(getPackageManager()).toString();if(hidden.contains(pkg))continue;
   if(!q.isEmpty()&&(match(name,q)||match(pkg,q))){appRow(r,pkg);count++;if(count>=30)break;}
  }
  if(!q.isEmpty()&&count==0)textRow("No matching apps","");
  if(hasContactsPermission()&&!q.isEmpty())renderContacts(q);
  else if(!q.isEmpty()){Button contact=new Button(this);contact.setText("Search contacts (requires permission)");results.addView(contact);contact.setOnClickListener(v->requestContacts());}
  renderSettings(q);
 }
 private void section(String name){TextView h=new TextView(this);h.setText(name);h.setTextColor(0xffb8d9ff);h.setTextSize(16);h.setPadding(0,dp(12),0,dp(5));results.addView(h);}
 private void textRow(String name,String sub){TextView t=new TextView(this);t.setText(sub.isEmpty()?name:name+"\n"+sub);t.setTextColor(0xffc8d4e0);t.setPadding(dp(8),dp(8),dp(8),dp(8));results.addView(t);}
 private void appRow(ResolveInfo r,String sub){
  LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(8),dp(7),dp(8),dp(7));row.setBackgroundColor(0xff202b39);
  LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=dp(4);results.addView(row,lp);
  ImageView icon=new ImageView(this);icon.setImageDrawable(r.loadIcon(getPackageManager()));row.addView(icon,new LinearLayout.LayoutParams(dp(38),dp(38)));
  TextView title=new TextView(this);title.setText(r.loadLabel(getPackageManager())+"\n"+sub);title.setTextColor(-1);title.setPadding(dp(10),0,0,0);row.addView(title);
  row.setOnClickListener(v->{String pkg=r.activityInfo.packageName;MiMaxSpotlightUsage.record(this,new Intent().setComponent(new ComponentName(pkg,r.activityInfo.name)));try{Intent i=new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER).setComponent(new ComponentName(pkg,r.activityInfo.name));startActivity(i);}catch(Exception ignored){}});
 }
 private void renderContacts(String q){
  Cursor cursor=null;int added=0;
  try{
   cursor=getContentResolver().query(ContactsContract.Contacts.CONTENT_URI,
    new String[]{ContactsContract.Contacts._ID,ContactsContract.Contacts.DISPLAY_NAME},
    ContactsContract.Contacts.DISPLAY_NAME+" LIKE ?",new String[]{"%"+q+"%"},ContactsContract.Contacts.DISPLAY_NAME+" ASC");
   if(cursor==null||!cursor.moveToFirst())return;
   section("Contacts");
   do{
    String id=cursor.getString(0),name=cursor.getString(1);
    TextView row=new TextView(this);row.setText("●  "+name);row.setTextColor(-1);row.setTextSize(15);row.setPadding(dp(10),dp(10),dp(10),dp(10));results.addView(row);
    row.setOnClickListener(v->{try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.withAppendedPath(ContactsContract.Contacts.CONTENT_URI,id)));}catch(Exception ignored){}});
    if(++added>=20)break;
   }while(cursor.moveToNext());
  }catch(SecurityException ignored){}finally{if(cursor!=null)cursor.close();}
 }
 private void renderSettings(String q){
  String[][] entries={
   {"Launcher settings","settings"},{"App Library","library"},{"Focus Mode","focus"},
   {"Me Island","island"},{"Privacy and app lock","privacy"},{"Profiles","profiles"},
   {"Smart Widget Stack","widgets"},{"Mi_Max AI Assistant","ai"},{"Theme schedule","schedule"},
   {"Extension Manager","extensions"},{"App labels and icons","personalization"},{"Page wallpapers","wallpaper"}
  };
  ArrayList<String[]> matches=new ArrayList<>();
  for(String[] e:entries)if(q.isEmpty()||match(e[0],q))matches.add(e);
  if(matches.isEmpty())return;
  section("Settings and tools");
  for(String[] e:matches){TextView row=new TextView(this);row.setText("⚙  "+e[0]);row.setTextColor(-1);row.setTextSize(15);row.setPadding(dp(10),dp(10),dp(10),dp(10));results.addView(row);row.setOnClickListener(v->open(e[1]));}
 }
 private void open(String key){
  Class<?> cls;
  switch(key){
   case "library":cls=MiMaxAppLibraryActivity.class;break;
   case "focus":cls=MiMaxFocusModeActivity.class;break;
   case "island":cls=MeIslandSettingsActivity.class;break;
   case "privacy":cls=MiMaxPrivacySettingsActivity.class;break;
   case "profiles":cls=MiMaxProfilesActivity.class;break;
   case "widgets":cls=MiMaxSmartStackActivity.class;break;
   case "ai":cls=MiMaxAiActivity.class;break;
   case "schedule":cls=MiMaxThemeScheduleActivity.class;break;
   case "extensions":cls=ExtensionManagerActivity.class;break;
   case "personalization":cls=MiMaxPersonalizationActivity.class;break;
   case "wallpaper":cls=MiMaxPageWallpaperActivity.class;break;
   default:cls=SettingsActivity.class;
  }
  startActivity(new Intent(this,cls));
 }
}
''')

# Track launches from the upstream app and shortcut tiles to populate recent-app suggestions.
itemView=Path("app/src/main/java/com/benny/openlauncher/widget/AppItemView.java")
s=itemView.read_text()
mark="App app = AppManager.getInstance(_view.getContext()).findApp(item._intent);"
if "MiMaxSpotlightUsage.record" not in s:
 if mark not in s: raise SystemExit("Could not find app launch callback for Spotlight tracking")
 s=s.replace(mark,"com.benny.openlauncher.mimax.MiMaxSpotlightUsage.record(_view.getContext(), item.getIntent());\n                            "+mark,1)
itemView.write_text(s)

manifest=BASE / "AndroidManifest.xml"
m=manifest.read_text()
if "android.permission.READ_CONTACTS" not in m:m=m.replace('<application','<uses-permission android:name="android.permission.READ_CONTACTS" />\n    <application',1)
if "com.benny.openlauncher.mimax.MiMaxSpotlightActivity" not in m:
 m=m.replace("</application>",'''        <activity android:name="com.benny.openlauncher.mimax.MiMaxSpotlightActivity" android:exported="false" android:label="Spotlight" />
    </application>''',1)
manifest.write_text(m)

layout=BASE / "res/layout/activity_home.xml"
xml=layout.read_text()
if "MiMaxSpotlightButton" not in xml:
 xml=xml.replace("</FrameLayout>",'''    <com.benny.openlauncher.mimax.MiMaxSpotlightButton
        android:id="@+id/mimax_spotlight_button"
        android:layout_width="104dp"
        android:layout_height="46dp"
        android:layout_gravity="bottom|start"
        android:layout_margin="10dp" />
</FrameLayout>''',1)
layout.write_text(xml)

master=BASE / "res/xml/preferences_master.xml"
p=master.read_text()
if "mimax_spotlight" not in p:
 entry='''    <PreferenceCategory android:title="Mi_Max Search">
        <Preference android:key="mimax_spotlight" android:title="Spotlight Search"
            android:summary="Search apps, recent launches, settings and optional contacts">
            <intent android:targetPackage="com.mimax.launcher" android:targetClass="com.benny.openlauncher.mimax.MiMaxSpotlightActivity" />
        </Preference>
    </PreferenceCategory>
'''
 p=p.replace("</PreferenceScreen>",entry+"</PreferenceScreen>",1)
master.write_text(p)

backup=Path("app/src/main/java/com/benny/openlauncher/util/BackupHelper.java")
s=backup.read_text()
s=s.replace('"mimax_ai.xml"\n    };','"mimax_ai.xml",\n        "mimax_spotlight.xml"\n    };')
backup.write_text(s)

print("Added home-screen Spotlight button with app search, recent app history, launcher settings tools and permission-gated contacts search.")
