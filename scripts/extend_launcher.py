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
        }
        view.setIconShape(p.getString("icon_shape","native"));
        view.setLabelTextSizeSp(p.getFloat("label_size",12f));
        if(p.contains("label_color")) view.setLabelTextColor(p.getInt("label_color",0xffffffff));
        view.setIconTint(p.getInt("icon_tint",0));
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
import android.view.Gravity;
import android.widget.*;
import java.util.*;

public final class MiMaxPersonalizationActivity extends Activity {
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
            Button save=new Button(this);save.setText("Save "+label);card.addView(save);
            save.setOnClickListener(v->{String text=alias.getText().toString().trim();prefs.edit().putString("label:"+pkg,text).putBoolean("hide_home:"+pkg,home.isChecked()).putBoolean("hide_drawer:"+pkg,drawer.isChecked()).apply();Toast.makeText(this,"Saved "+label,Toast.LENGTH_SHORT).show();});
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
