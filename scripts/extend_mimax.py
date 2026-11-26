from pathlib import Path
import json

BASE = Path("app/src/main")
JAVA = BASE / "java/com/benny/openlauncher/mimax"
JAVA.mkdir(parents=True, exist_ok=True)

(JAVA / "MeIslandThemeManager.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.content.Context;
import android.net.Uri;
import org.json.JSONObject;
import java.io.*;
import java.util.*;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public final class MeIslandThemeManager {
    public static final String PREFS = "me_island_themes_v1";
    private final Context context;
    private final android.content.SharedPreferences prefs;

    public static final class Theme {
        public final String id, name, style, layout, animation;
        public final int blur, cornerDp, widthDp, compactHeightDp, expandedHeightDp, animationMs;
        public final long background, accent;
        Theme(String id, String name, String style, String layout, String animation,
              long background, long accent, int blur, int corner, int width,
              int compact, int expanded, int animationMs) {
            this.id=id; this.name=name; this.style=style; this.layout=layout; this.animation=animation;
            this.background=background; this.accent=accent; this.blur=clamp(blur,0,80);
            this.cornerDp=clamp(corner,8,48); this.widthDp=clamp(width,120,300);
            this.compactHeightDp=clamp(compact,24,70); this.expandedHeightDp=clamp(expanded,60,220);
            this.animationMs=clamp(animationMs,100,900);
        }
        JSONObject json() throws Exception {
            return new JSONObject().put("format","mimax-island-theme")
                .put("id",id).put("name",name).put("style",style).put("layout",layout)
                .put("animation",animation).put("background",background).put("accent",accent)
                .put("blur",blur).put("cornerDp",cornerDp).put("widthDp",widthDp)
                .put("compactHeightDp",compactHeightDp).put("expandedHeightDp",expandedHeightDp)
                .put("animationMs",animationMs);
        }
    }
    private static int clamp(int v,int min,int max) { return Math.max(min,Math.min(max,v)); }

    public MeIslandThemeManager(Context c) {
        context=c.getApplicationContext();
        prefs=context.getSharedPreferences(PREFS,Context.MODE_PRIVATE);
    }
    public List<Theme> all() {
        ArrayList<Theme> result=new ArrayList<>();
        for(Theme t:builtIns()) result.add(readOverride(t));
        for(Map.Entry<String,?> e:prefs.getAll().entrySet()) {
            if(!e.getKey().startsWith("pack_") || !(e.getValue() instanceof String)) continue;
            try {
                Theme t=parse(new JSONObject((String)e.getValue()));
                if(find(result,t.id)==null) result.add(t);
            } catch(Exception ignored) {}
        }
        return result;
    }
    public String selectedId() { return prefs.getString("selected_theme","his"); }
    public void select(String id) {
        if(find(all(),id)==null) throw new IllegalArgumentException("Unknown theme: "+id);
        prefs.edit().putString("selected_theme",id).apply();
    }
    public Theme current() {
        Theme t=find(all(),selectedId());
        return t==null ? builtIns().get(1) : t;
    }
    public boolean blurEnabled() { return prefs.getBoolean("blur_enabled",true); }
    public void setBlurEnabled(boolean enabled) { prefs.edit().putBoolean("blur_enabled",enabled).apply(); }
    public boolean lowPerformanceEnabled() { return prefs.getBoolean("low_performance",false); }
    public void setLowPerformanceEnabled(boolean enabled) { prefs.edit().putBoolean("low_performance",enabled).apply(); }
    public boolean reducedMotionEnabled() { return prefs.getBoolean("reduced_motion",false); }
    public void setReducedMotionEnabled(boolean enabled) { prefs.edit().putBoolean("reduced_motion",enabled).apply(); }
    public void save(Theme t) throws Exception {
        String key="pack_"+t.id;
        String previous=prefs.getString(key,null);
        if(previous!=null) prefs.edit().putString("previous_"+t.id,previous).apply();
        prefs.edit().putString(key,t.json().toString()).apply();
    }
    public Theme findTheme(String id) { return find(all(),id); }
    public boolean rollback(String id) {
        String previous=prefs.getString("previous_"+id,null);
        if(previous==null)return false;
        prefs.edit().putString("pack_"+id,previous).remove("previous_"+id).apply();
        return true;
    }
    public boolean remove(String id) {
        if(isBuiltIn(id))return false;
        prefs.edit().remove("pack_"+id).remove("previous_"+id).apply();
        if(id.equals(selectedId()))select("his");
        return true;
    }
    public void removeAllImported() {
        android.content.SharedPreferences.Editor e=prefs.edit();
        for(String key:prefs.getAll().keySet()) if(key.startsWith("pack_")||key.startsWith("previous_"))e.remove(key);
        e.putString("selected_theme","his").apply();
    }
    public Theme withStyle(Theme t,String style) {
        String layout=style.equals("ltin")?"pill":style.equals("his")?"wide_card":"fluid";
        int width=style.equals("ltin")?178:style.equals("his")?196:190;
        return new Theme(t.id,t.name,style,layout,t.animation,t.background,t.accent,t.blur,
            t.cornerDp,width,t.compactHeightDp,t.expandedHeightDp,t.animationMs);
    }
    public Theme importTheme(Uri uri) throws Exception {
        byte[] data;
        try(InputStream in=context.getContentResolver().openInputStream(uri);
            ByteArrayOutputStream out=new ByteArrayOutputStream()) {
            if(in==null) throw new IOException("Unable to read selected file");
            byte[] b=new byte[8192]; int n; int total=0;
            while((n=in.read(b))!=-1) { total+=n; if(total>2*1024*1024) throw new IOException("Theme package exceeds 2 MB"); out.write(b,0,n); }
            data=out.toByteArray();
        }
        String manifest;
        if(data.length>=4 && data[0]==0x50 && data[1]==0x4b) {
            manifest=null;
            try(ZipInputStream zip=new ZipInputStream(new ByteArrayInputStream(data))) {
                ZipEntry e;
                while((e=zip.getNextEntry())!=null) {
                    String name=e.getName();
                    if(name.startsWith("/") || name.contains("..") || name.contains("\\")) throw new SecurityException("Unsafe theme path");
                    if(name.equals("manifest.json")) {
                        ByteArrayOutputStream out=new ByteArrayOutputStream(); byte[] b=new byte[4096]; int n,total=0;
                        while((n=zip.read(b))!=-1) { total+=n; if(total>128*1024) throw new IOException("Theme manifest too large"); out.write(b,0,n); }
                        manifest=out.toString("UTF-8"); break;
                    }
                }
            }
            if(manifest==null) throw new IOException("No manifest.json found");
        } else manifest=new String(data,"UTF-8");
        Theme t=parse(new JSONObject(manifest));
        if(!t.id.matches("[A-Za-z0-9_.-]{1,48}") || t.name.trim().isEmpty()) throw new IllegalArgumentException("Invalid theme identity");
        save(t); select(t.id); return t;
    }
    public Theme installJson(String json) throws Exception { return installJson(json,true); }
    public Theme installJson(String json, boolean activate) throws Exception {
        Theme t=parse(new JSONObject(json));
        if(!t.id.matches("[A-Za-z0-9_.-]{1,48}") || t.name.trim().isEmpty()) throw new IllegalArgumentException("Invalid theme identity");
        save(t);
        if(activate)select(t.id);
        return t;
    }
    public boolean isBuiltIn(String id) {
        return "ltin".equals(id) || "his".equals(id) || "coloros".equals(id) || "oneplus_sample".equals(id);
    }
    public void exportTheme(Uri uri) throws Exception {
        try(OutputStream out=context.getContentResolver().openOutputStream(uri)) {
            if(out==null) throw new IOException("Unable to open export destination");
            out.write(current().json().toString(2).getBytes("UTF-8"));
        }
    }
    private Theme readOverride(Theme base) {
        String raw=prefs.getString("pack_"+base.id,null);
        if(raw==null) return base;
        try { return parse(new JSONObject(raw)); } catch(Exception ignored) { return base; }
    }
    private static Theme find(List<Theme> list,String id) { for(Theme t:list) if(t.id.equals(id)) return t; return null; }
    private static List<Theme> builtIns() {
        return Arrays.asList(
            new Theme("ltin","LTIN","ltin","pill","spring",0xff050505L,0xffffffffL,18,28,178,34,104,260),
            new Theme("his","HIS","his","wide_card","morph",0xee10151dL,0xffb8d9ffL,28,24,196,38,116,340),
            new Theme("coloros","ColorOS","coloros","fluid","spring",0xcc263442L,0xffbdebffL,32,22,190,38,112,300),
            new Theme("oneplus_sample","OnePlus Split","custom","split","spring",0xef101820L,0xff59d6c2L,34,20,224,40,124,360)
        );
    }
    private static Theme parse(JSONObject root) throws Exception {
        JSONObject o=root.optJSONObject("theme"); if(o==null) o=root;
        String style=o.optString("style","custom");
        if(!Arrays.asList("ltin","his","coloros","custom").contains(style)) throw new IllegalArgumentException("Unknown island engine");
        String layout=o.optString("layout","wide_card");
        if(!Arrays.asList("pill","wide_card","split","fluid").contains(layout)) throw new IllegalArgumentException("Unknown layout");
        String animation=o.optString("animation","spring");
        if(!Arrays.asList("spring","morph","fade_slide").contains(animation)) throw new IllegalArgumentException("Unknown animation");
        return new Theme(o.getString("id"),o.optString("name","Custom Me Island").substring(0,Math.min(48,o.optString("name","Custom Me Island").length())),
            style,layout,animation,o.optLong("background",0xee10151dL),o.optLong("accent",0xffb8d9ffL),
            o.optInt("blur",24),o.optInt("cornerDp",26),o.optInt("widthDp",190),
            o.optInt("compactHeightDp",38),o.optInt("expandedHeightDp",112),o.optInt("animationMs",300));
    }
}
''')

(JAVA / "MeIslandService.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.*;
import android.content.*;
import android.graphics.*;
import android.graphics.drawable.GradientDrawable;
import android.os.*;
import android.provider.Settings;
import android.view.*;
import android.view.animation.*;
import android.widget.*;
import java.util.*;

public final class MeIslandService extends Service {
    public static final String ACTION_TIMER="com.mimax.launcher.island.TIMER";
    public static final String ACTION_ACTIVITY="com.mimax.launcher.island.ACTIVITY";
    public static final String ACTION_CLEAR="com.mimax.launcher.island.CLEAR";
    public static final String ACTION_STOP="com.mimax.launcher.island.STOP";
    public static final String ACTION_REFRESH="com.mimax.launcher.island.REFRESH";
    public static final String EXTRA_ID="id", EXTRA_TITLE="title", EXTRA_BODY="body", EXTRA_TTL="ttl", EXTRA_PRIORITY="priority";
    public static final String EXTRA_DURATION="duration_ms";
    private static final String CHANNEL="mimax_me_island";
    private static final int NOTIFICATION_ID=7401;
    private static final String TIMER_ID="mimax.timer";

    private static final class Item {
        String id,title,body; int priority; long expiresAt; PendingIntent pending;
        Item(String i,String t,String b,int p,long e,PendingIntent pi){id=i;title=t;body=b;priority=p;expiresAt=e;pending=pi;}
    }
    private final LinkedHashMap<String,Item> items=new LinkedHashMap<>();
    private final Handler handler=new Handler(Looper.getMainLooper());
    private WindowManager wm; private LinearLayout root; private TextView title,detail,mark;
    private WindowManager.LayoutParams params; private String shownId="";
    private boolean expanded=false; private float downX,downY; private long timerEnds=0;
    private BroadcastReceiver batteryReceiver;

    private final Runnable tick=new Runnable(){@Override public void run(){
        long now=System.currentTimeMillis();
        Iterator<Item> it=items.values().iterator();
        while(it.hasNext()){Item item=it.next(); if(item.expiresAt>0 && item.expiresAt<=now) it.remove();}
        if(timerEnds>0){
            long left=Math.max(0,timerEnds-now);
            if(left==0){items.put(TIMER_ID,new Item(TIMER_ID,"Timer finished","Your timer has ended",100,now+5000,null));timerEnds=0;
                getSharedPreferences("mimax_island_state",0).edit().remove("timer_end").apply();}
            else items.put(TIMER_ID,new Item(TIMER_ID,"Timer",format(left),100,0,null));
        }
        render();
        if(!items.isEmpty()) handler.postDelayed(this,500); else {stopForeground(true);stopSelf();}
    }};

    @Override public void onCreate(){super.onCreate();wm=(WindowManager)getSystemService(WINDOW_SERVICE);createChannel();registerBattery();}
    @Override public int onStartCommand(Intent intent,int flags,int startId){
        String action=intent==null?null:intent.getAction();
        if(intent==null){
            timerEnds=getSharedPreferences("mimax_island_state",0).getLong("timer_end",0L);
            if(timerEnds>System.currentTimeMillis())items.put(TIMER_ID,new Item(TIMER_ID,"Timer",format(timerEnds-System.currentTimeMillis()),100,0,null));
        }
        if(ACTION_STOP.equals(action)){handler.removeCallbacks(tick);items.clear();getSharedPreferences("mimax_island_state",0).edit().remove("timer_end").apply();removeView();stopForeground(true);stopSelf();return START_NOT_STICKY;}
        if(ACTION_TIMER.equals(action)){
            long duration=Math.max(1000,Math.min(86400000,intent.getLongExtra(EXTRA_DURATION,60000)));
            timerEnds=System.currentTimeMillis()+duration;
            getSharedPreferences("mimax_island_state",0).edit().putLong("timer_end",timerEnds).apply();
            items.put(TIMER_ID,new Item(TIMER_ID,"Timer",format(duration),100,0,null));
        } else if(ACTION_ACTIVITY.equals(action)){
            String id=intent.getStringExtra(EXTRA_ID); if(id==null) id="activity";
            String t=intent.getStringExtra(EXTRA_TITLE); String b=intent.getStringExtra(EXTRA_BODY);
            int priority=intent.getIntExtra(EXTRA_PRIORITY,30); long ttl=intent.getLongExtra(EXTRA_TTL,6000);
            PendingIntent pi=intent.getParcelableExtra("content_intent");
            boolean hide=getSharedPreferences("mimax_island_state",0).getBoolean("privacy",false);
            if(hide){t="New activity";b="";}
            items.put(id,new Item(id,t==null?"Activity":t,b==null?"":b,priority,ttl>0?System.currentTimeMillis()+ttl:0,pi));
        } else if(ACTION_CLEAR.equals(action)){String id=intent.getStringExtra(EXTRA_ID);if(id!=null)items.remove(id);}
        else if(ACTION_REFRESH.equals(action)){removeView();}
        if(!items.isEmpty()){
            startForeground(NOTIFICATION_ID,notification());
            handler.removeCallbacks(tick);handler.post(tick);
        }
        return START_STICKY;
    }

    private void registerBattery(){
        batteryReceiver=new BroadcastReceiver(){@Override public void onReceive(Context c,Intent i){
            int state=i.getIntExtra(android.os.BatteryManager.EXTRA_STATUS,-1);
            boolean charging=state==android.os.BatteryManager.BATTERY_STATUS_CHARGING||state==android.os.BatteryManager.BATTERY_STATUS_FULL;
            if(charging) items.put("mimax.battery",new Item("mimax.battery","Charging","Power connected",15,0,null));
            else items.remove("mimax.battery");
            if(!items.isEmpty()){startForeground(NOTIFICATION_ID,notification());render();}else render();
        }};
        registerReceiver(batteryReceiver,new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
    }
    private void createChannel(){if(Build.VERSION.SDK_INT>=26){NotificationChannel c=new NotificationChannel(CHANNEL,"Me Island activities",NotificationManager.IMPORTANCE_LOW);c.setDescription("Live activity overlay");((NotificationManager)getSystemService(NOTIFICATION_SERVICE)).createNotificationChannel(c);}}
    private Notification notification(){
        Intent i=new Intent(this,MeIslandSettingsActivity.class);
        PendingIntent pi=PendingIntent.getActivity(this,0,i,PendingIntent.FLAG_UPDATE_CURRENT|(Build.VERSION.SDK_INT>=23?PendingIntent.FLAG_IMMUTABLE:0));
        Notification.Builder b=Build.VERSION.SDK_INT>=26?new Notification.Builder(this,CHANNEL):new Notification.Builder(this);
        return b.setSmallIcon(android.R.drawable.ic_lock_idle_alarm).setContentTitle("Mi_Max Me Island")
            .setContentText(items.size()+" live activity item(s)").setContentIntent(pi).setOngoing(true).build();
    }
    private Item current(){
        Item best=null;
        for(Item v:items.values()) if(best==null||v.priority>best.priority)best=v;
        return best;
    }
    private void render(){
        if(items.isEmpty()){removeView();return;}
        Item item=current(); if(item==null)return;
        MeIslandThemeManager performance=new MeIslandThemeManager(this);
        MeIslandThemeManager.Theme theme=performance.current();
        if(root==null || !shownId.equals(item.id+"|"+theme.style+"|"+theme.layout)){removeView();buildView(theme,item);}
        if(title!=null) title.setText(formatTitle(item,theme));
        if(detail!=null) detail.setText(expanded||"wide_card".equals(theme.layout)||"split".equals(theme.layout)?item.body:"");
        if(mark!=null) mark.setText(theme.style.equals("ltin")?"●":theme.style.equals("his")?"◉":"✦");
        if(params!=null){
            params.width=dp(expanded?Math.max(theme.widthDp,220):theme.widthDp);
            params.height=dp(expanded?theme.expandedHeightDp:theme.compactHeightDp);
            params.y=cameraSafeTop()+dp(expanded?5:2);
            try{wm.updateViewLayout(root,params);}catch(Exception ignored){}
        }
        if(root!=null){
            root.setBackground(background(theme));
            long motion=performance.reducedMotionEnabled()?0L:(performance.lowPerformanceEnabled()?Math.min(120,theme.animationMs):theme.animationMs);
            if(motion==0L){root.setAlpha(1f);root.setScaleX(1f);root.setScaleY(1f);}
            else root.animate().setInterpolator(interpolator(theme.animation)).setDuration(motion).start();
        }
        shownId=item.id+"|"+theme.style+"|"+theme.layout;
    }
    private void buildView(MeIslandThemeManager.Theme theme,Item item){
        root=new LinearLayout(this);
        root.setGravity(Gravity.CENTER_VERTICAL);
        root.setOrientation(("his".equals(theme.style)||"wide_card".equals(theme.layout)||"split".equals(theme.layout))?LinearLayout.VERTICAL:LinearLayout.HORIZONTAL);
        root.setPadding(dp(theme.style.equals("ltin")?16:14),dp(5),dp(14),dp(5));
        root.setBackground(background(theme));root.setElevation(dp(18));
        mark=new TextView(this);mark.setTextColor((int)theme.accent);mark.setTextSize(theme.style.equals("coloros")?14:11);mark.setPadding(0,0,dp(8),0);
        root.addView(mark,new LinearLayout.LayoutParams(-2,-2));
        LinearLayout texts=new LinearLayout(this);texts.setOrientation("split".equals(theme.layout)?LinearLayout.HORIZONTAL:LinearLayout.VERTICAL);texts.setGravity(Gravity.CENTER_VERTICAL);
        title=new TextView(this);title.setTextColor(Color.WHITE);title.setTextSize(theme.style.equals("ltin")?12:13);title.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));title.setMaxLines(1);
        detail=new TextView(this);detail.setTextColor(Color.argb(215,245,248,255));detail.setTextSize(11);detail.setMaxLines(2);
        texts.addView(title);texts.addView(detail);
        root.addView(texts,new LinearLayout.LayoutParams(0,-2,1));
        root.setOnClickListener(v->{expanded=!expanded;render();});
        root.setOnLongClickListener(v->{Item cur=current();if(cur!=null && !TIMER_ID.equals(cur.id))items.remove(cur.id);render();return true;});
        root.setOnTouchListener((v,e)->{
            if(e.getAction()==MotionEvent.ACTION_DOWN){downX=e.getRawX();downY=e.getRawY();return true;}
            if(e.getAction()==MotionEvent.ACTION_UP){
                float dx=e.getRawX()-downX,dy=e.getRawY()-downY;
                if(Math.abs(dx)>dp(36)&&Math.abs(dx)>Math.abs(dy)){cycle(dx<0?1:-1);return true;}
                if(Math.abs(dy)>dp(28)){expanded=dy>0;render();return true;}
                if(Math.abs(dx)<dp(20)&&Math.abs(dy)<dp(20)){
                    Item active=current();
                    if(active!=null&&active.pending!=null)try{active.pending.send();}catch(Exception ignored){}
                    expanded=!expanded;render();return true;
                }
                return true;
            }return true;
        });
        params=new WindowManager.LayoutParams(dp(theme.widthDp),dp(theme.compactHeightDp),
            Build.VERSION.SDK_INT>=26?WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY:WindowManager.LayoutParams.TYPE_PHONE,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE|WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN|WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT);
        params.gravity=Gravity.TOP|Gravity.CENTER_HORIZONTAL;params.y=cameraSafeTop()+dp(2);
        MeIslandThemeManager performance=new MeIslandThemeManager(this);
        if(Build.VERSION.SDK_INT>=31&&performance.blurEnabled()&&!performance.lowPerformanceEnabled()){params.flags|=WindowManager.LayoutParams.FLAG_BLUR_BEHIND;params.setBlurBehindRadius(dp(theme.blur));}
        try{
            wm.addView(root,params);
            long motion=performance.reducedMotionEnabled()?0L:(performance.lowPerformanceEnabled()?Math.min(120,theme.animationMs):theme.animationMs);
            if(motion==0L){root.setAlpha(1f);root.setScaleX(1f);root.setScaleY(1f);}
            else {root.setAlpha(0f);root.setScaleX(.86f);root.setScaleY(.86f);root.animate().alpha(1f).scaleX(1f).scaleY(1f).setDuration(motion).setInterpolator(interpolator(theme.animation)).start();}
        } catch(Exception e){root=null;title=null;detail=null;mark=null;params=null;}
        shownId=item.id+"|"+theme.style+"|"+theme.layout;
    }
    private void cycle(int direction){
        ArrayList<Item> all=new ArrayList<>(items.values());if(all.size()<2)return;
        Item cur=current();int index=all.indexOf(cur);Item next=all.get((index+direction+all.size())%all.size());
        for(Item i:all)i.priority-=1;next.priority+=100;render();
    }
    private CharSequence formatTitle(Item item,MeIslandThemeManager.Theme theme){
        if(TIMER_ID.equals(item.id)&&timerEnds>0)return theme.style.equals("ltin")?"◷  "+item.body:"TIMER  •  "+item.body;
        if(expanded)return item.title;
        if(theme.style.equals("ltin"))return item.title.length()>18?item.title.substring(0,18)+"…":item.title;
        return item.title;
    }
    private GradientDrawable background(MeIslandThemeManager.Theme t){
        int color=t.style.equals("ltin")?Color.BLACK:(int)t.background;
        GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(t.style.equals("ltin")?40:t.cornerDp));
        d.setStroke(dp(1),t.style.equals("his")?Color.argb(80,190,220,255):Color.argb(50,255,255,255));return d;
    }
    private android.view.animation.Interpolator interpolator(String a){if("spring".equals(a))return new OvershootInterpolator(.55f);if("fade_slide".equals(a))return new DecelerateInterpolator();return new AccelerateDecelerateInterpolator();}
    private String format(long ms){long s=(ms+999)/1000;return String.format(Locale.getDefault(),"%02d:%02d",s/60,s%60);}
    private int cameraSafeTop(){
        if(Build.VERSION.SDK_INT>=30){try{android.view.DisplayCutout c=wm.getCurrentWindowMetrics().getWindowInsets().getDisplayCutout();if(c!=null&&!c.getBoundingRects().isEmpty())return c.getBoundingRects().get(0).bottom;}catch(Exception ignored){}}
        int id=getResources().getIdentifier("status_bar_height","dimen","android");return id>0?getResources().getDimensionPixelSize(id):dp(24);
    }
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    private void removeView(){if(root!=null){final View old=root;try{old.animate().alpha(0).setDuration(120).withEndAction(()->{try{wm.removeView(old);}catch(Exception ignored){}}).start();}catch(Exception e){try{wm.removeView(old);}catch(Exception ignored){}}}root=null;title=null;detail=null;mark=null;params=null;shownId="";}
    @Override public void onDestroy(){handler.removeCallbacksAndMessages(null);if(batteryReceiver!=null)try{unregisterReceiver(batteryReceiver);}catch(Exception ignored){}removeView();super.onDestroy();}
    @Override public IBinder onBind(Intent i){return null;}
}
''')

(JAVA / "MeIslandNotificationListener.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.Notification;
import android.app.PendingIntent;
import android.content.Intent;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;

public final class MeIslandNotificationListener extends NotificationListenerService {
    @Override public void onNotificationPosted(StatusBarNotification sbn){
        if(sbn==null||sbn.isGroup()||sbn.getPackageName().equals(getPackageName()))return;
        Notification n=sbn.getNotification(); if(n==null||n.extras==null)return;
        String category=n.category;
        if(Notification.CATEGORY_SERVICE.equals(category)&& (n.flags&Notification.FLAG_ONGOING_EVENT)!=0)return;
        CharSequence title=n.extras.getCharSequence(Notification.EXTRA_TITLE);
        CharSequence body=n.extras.getCharSequence(Notification.EXTRA_BIG_TEXT);
        if(body==null)body=n.extras.getCharSequence(Notification.EXTRA_TEXT);
        if((title==null||title.length()==0)&&(body==null||body.length()==0))return;
        int priority=30; long ttl=6500;
        if(Notification.CATEGORY_CALL.equals(category)){priority=95;ttl=0;}
        else if(Notification.CATEGORY_TRANSPORT.equals(category)){priority=75;ttl=0;}
        else if(Notification.CATEGORY_NAVIGATION.equals(category)){priority=65;ttl=0;}
        else if(Notification.CATEGORY_PROGRESS.equals(category)){priority=55;ttl=0;}
        else if((n.flags & Notification.FLAG_ONGOING_EVENT)!=0){priority=45;ttl=0;}
        Intent i=new Intent(this,MeIslandService.class).setAction(MeIslandService.ACTION_ACTIVITY);
        i.putExtra(MeIslandService.EXTRA_ID,sbn.getPackageName()+":"+sbn.getId());
        i.putExtra(MeIslandService.EXTRA_TITLE,title==null?"Activity":title.toString());
        i.putExtra(MeIslandService.EXTRA_BODY,body==null?"":body.toString());
        i.putExtra(MeIslandService.EXTRA_PRIORITY,priority);
        i.putExtra(MeIslandService.EXTRA_TTL,ttl);
        PendingIntent pi=n.contentIntent;if(pi!=null)i.putExtra("content_intent",pi);
        try{if(android.os.Build.VERSION.SDK_INT>=26)startForegroundService(i);else startService(i);}catch(Exception ignored){}
    }
    @Override public void onNotificationRemoved(StatusBarNotification sbn){
        if(sbn==null)return;
        Intent i=new Intent(this,MeIslandService.class).setAction(MeIslandService.ACTION_CLEAR);
        i.putExtra(MeIslandService.EXTRA_ID,sbn.getPackageName()+":"+sbn.getId());
        try{startService(i);}catch(Exception ignored){}
    }
}
''')

(JAVA / "MeIslandBatteryReceiver.java").write_text(r'''package com.benny.openlauncher.mimax;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
public final class MeIslandBatteryReceiver extends BroadcastReceiver {
 @Override public void onReceive(Context c,Intent source){
  Intent i=new Intent(c,MeIslandService.class).setAction(MeIslandService.ACTION_ACTIVITY);
  i.putExtra(MeIslandService.EXTRA_ID,"mimax.power");
  i.putExtra(MeIslandService.EXTRA_TITLE,"Power connected");
  i.putExtra(MeIslandService.EXTRA_BODY,"Charging activity");
  i.putExtra(MeIslandService.EXTRA_PRIORITY,20);
  i.putExtra(MeIslandService.EXTRA_TTL,0L);
  try{if(Build.VERSION.SDK_INT>=26)c.startForegroundService(i);else c.startService(i);}catch(Exception ignored){}
 }
}
''')

(JAVA / "MeIslandSettingsActivity.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.*;
import android.content.*;
import android.net.Uri;
import android.os.*;
import android.provider.Settings;
import android.view.*;
import android.widget.*;

public final class MeIslandSettingsActivity extends Activity {
 private static final int PICK_THEME=7301,CREATE_THEME=7302;
 private MeIslandThemeManager manager;
 private MeIslandThemeManager.Theme editing;
 private LinearLayout content;
 private SeekBar width,height,radius,blur,animation,duration;
 private Spinner layout,anim;
 private Switch blurSwitch,privacySwitch,lowPerformanceSwitch,reducedMotionSwitch;
 private TextView status,preview;
 @Override protected void onCreate(Bundle b){super.onCreate(b);manager=new MeIslandThemeManager(this);editing=manager.current();build();}
 private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
 private void build(){
  ScrollView scroll=new ScrollView(this);content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);content.setPadding(dp(18),dp(18),dp(18),dp(24));content.setBackgroundColor(0xff101722);scroll.addView(content);
  addText("Mi_Max Me Island",24,true);addText("اختَر محركًا يغيّر شكل الجزيرة وتخطيطها وحركتها، وليس لونها فقط.",14,false);
  addText("الثيمات المثبتة",17,true);
  java.util.List<MeIslandThemeManager.Theme> installed=manager.all();
  String[] themeNames=new String[installed.size()];
  int selectedIndex=0;
  for(int n=0;n<installed.size();n++){themeNames[n]=installed.get(n).name+" ("+installed.get(n).id+")";if(installed.get(n).id.equals(editing.id))selectedIndex=n;}
  Spinner savedThemes=spinner(themeNames,themeNames.length>0?themeNames[selectedIndex]:"HIS");
  content.addView(savedThemes);
  savedThemes.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
   public void onNothingSelected(android.widget.AdapterView<?> p){}
   public void onItemSelected(android.widget.AdapterView<?> p,android.view.View v,int pos,long id){if(pos>=0&&pos<installed.size()){editing=installed.get(pos);applyPreview();}}
  });
  addText("محركات الجزيرة",18,true);
  for(String id:new String[]{"ltin","his","coloros"}){
   MeIslandThemeManager.Theme t=find(id);Button b=button(t.name+" — "+description(id));b.setOnClickListener(v->{editing=manager.withStyle(editing,id);applyPreview();status.setText("تم اختيار "+t.name);});content.addView(b);
  }
  addText("تخطيط البطاقة",16,true);layout=spinner(new String[]{"pill","wide_card","split","fluid"},editing.layout);content.addView(layout);
  addText("نوع الحركة",16,true);anim=spinner(new String[]{"spring","morph","fade_slide"},editing.animation);content.addView(anim);
  width=seek("العرض",120,300,editing.widthDp);height=seek("ارتفاع العرض",24,70,editing.compactHeightDp);radius=seek("استدارة الزوايا",8,48,editing.cornerDp);blur=seek("قوة التمويه",0,80,editing.blur);animation=seek("مدة الحركة",100,900,editing.animationMs);duration=seek("مدة المؤقت بالدقائق",1,120,10);
  blurSwitch=new Switch(this);blurSwitch.setText("تفعيل Blur عند دعم Android");blurSwitch.setChecked(manager.blurEnabled());content.addView(blurSwitch);
  privacySwitch=new Switch(this);privacySwitch.setText("وضع الخصوصية: إخفاء نص الإشعارات");privacySwitch.setChecked(getSharedPreferences("mimax_island_state",0).getBoolean("privacy",false));content.addView(privacySwitch);
  lowPerformanceSwitch=new Switch(this);lowPerformanceSwitch.setText("وضع الأداء المنخفض: تعطيل Blur وتقليل الحركة");lowPerformanceSwitch.setChecked(manager.lowPerformanceEnabled());content.addView(lowPerformanceSwitch);
  reducedMotionSwitch=new Switch(this);reducedMotionSwitch.setText("تقليل الحركة والانتقالات");reducedMotionSwitch.setChecked(manager.reducedMotionEnabled());content.addView(reducedMotionSwitch);
  preview=new TextView(this);preview.setText("◉   Me Island preview   12:45");preview.setTextColor(-1);preview.setGravity(Gravity.CENTER);preview.setPadding(dp(12),dp(12),dp(12),dp(12));content.addView(preview,new LinearLayout.LayoutParams(-1,dp(52)));
  Button rollback=button("استرجاع آخر نسخة محفوظة من هذا الثيم");content.addView(rollback);rollback.setOnClickListener(v->{if(manager.rollback(editing.id)){editing=manager.findTheme(editing.id);status.setText("تم استرجاع النسخة السابقة");applyPreview();}else status.setText("لا توجد نسخة سابقة لهذا الثيم");});
  Button removeTheme=button("حذف الثيم المستورد");content.addView(removeTheme);removeTheme.setOnClickListener(v->{if(manager.remove(editing.id)){editing=manager.current();status.setText("تم حذف الثيم");applyPreview();}else status.setText("لا يمكن حذف محركات الجزيرة الأساسية");});
  Button save=button("حفظ التصميم وتطبيقه");content.addView(save);save.setOnClickListener(v->save());
  Button overlay=button("السماح بالظهور فوق التطبيقات");content.addView(overlay);overlay.setOnClickListener(v->{if(Build.VERSION.SDK_INT>=23&&!Settings.canDrawOverlays(this))startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,Uri.parse("package:"+getPackageName())));});
  Button access=button("تفعيل Notification Access");content.addView(access);access.setOnClickListener(v->startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)));
  Button timerButton=button("تشغيل المؤقت في الجزيرة");content.addView(timerButton);timerButton.setOnClickListener(v->startTimer());
  Button importButton=button("استيراد ثيم .mt1");content.addView(importButton);importButton.setOnClickListener(v->{Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(i,PICK_THEME);});
  Button exportButton=button("تصدير الثيم الحالي");content.addView(exportButton);exportButton.setOnClickListener(v->{Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("application/json").putExtra(Intent.EXTRA_TITLE,"MiMax-Island.mt1");startActivityForResult(i,CREATE_THEME);});
  Button extensions=button("إدارة الإضافات");content.addView(extensions);extensions.setOnClickListener(v->startActivity(new Intent(this,ExtensionManagerActivity.class)));
  Button stop=button("إيقاف الجزيرة");content.addView(stop);stop.setOnClickListener(v->{Intent i=new Intent(this,MeIslandService.class).setAction(MeIslandService.ACTION_STOP);startService(i);});
  status=new TextView(this);status.setTextColor(0xffb8d9ff);status.setPadding(0,dp(12),0,dp(12));content.addView(status);
  setContentView(scroll);applyPreview();
 }
 private void addText(String s,int size,boolean bold){TextView t=new TextView(this);t.setText(s);t.setTextColor(-1);t.setTextSize(size);if(bold)t.setTypeface(null,1);t.setPadding(0,dp(7),0,dp(4));content.addView(t);}
 private Button button(String s){Button b=new Button(this);b.setText(s);return b;}
 private Spinner spinner(String[] values,String selected){Spinner s=new Spinner(this);ArrayAdapter<String>a=new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,values);s.setAdapter(a);int idx=java.util.Arrays.asList(values).indexOf(selected);s.setSelection(Math.max(0,idx));return s;}
 private SeekBar seek(String name,int min,int max,int value){addText(name+": "+value,14,false);SeekBar s=new SeekBar(this);s.setMax(max-min);s.setProgress(value-min);s.setTag(name);s.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){public void onProgressChanged(SeekBar b,int p,boolean user){TextView last=(TextView)content.getChildAt(content.indexOfChild(b)-1);last.setText(name+": "+(p+min));}public void onStartTrackingTouch(SeekBar b){}public void onStopTrackingTouch(SeekBar b){}});content.addView(s);return s;}
 private String description(String id){return id.equals("ltin")?"pill / compact":id.equals("his")?"wide card / multi-row":"glass capsule / fluid";}
 private MeIslandThemeManager.Theme find(String id){for(MeIslandThemeManager.Theme t:manager.all())if(t.id.equals(id))return t;return editing;}
 private void applyPreview(){if(preview==null)return;int color=editing.style.equals("ltin")?0xff000000:(int)editing.background;preview.setBackground(new android.graphics.drawable.GradientDrawable(){ {setColor(color);setCornerRadius(dp(editing.cornerDp));setStroke(dp(1),(int)editing.accent);} });preview.setText(editing.style.toUpperCase()+"  •  "+editing.layout+"  •  "+editing.animation);}
 private void save(){
  String l=(String)layout.getSelectedItem(),a=(String)anim.getSelectedItem();
  editing=new MeIslandThemeManager.Theme(editing.id,editing.name,editing.style,l,a,editing.background,editing.accent,
   blur.getProgress(),radius.getProgress()+8,width.getProgress()+120,height.getProgress()+24,editing.expandedHeightDp,animation.getProgress()+100);
  try{manager.save(editing);manager.select(editing.id);manager.setBlurEnabled(blurSwitch.isChecked());manager.setLowPerformanceEnabled(lowPerformanceSwitch.isChecked());manager.setReducedMotionEnabled(reducedMotionSwitch.isChecked());getSharedPreferences("mimax_island_state",0).edit().putBoolean("privacy",privacySwitch.isChecked()).apply();
   Intent i=new Intent(this,MeIslandService.class).setAction(MeIslandService.ACTION_REFRESH);startService(i);status.setText("تم حفظ إعدادات الجزيرة وتطبيقها");applyPreview();
  }catch(Exception e){status.setText("تعذر الحفظ: "+e.getMessage());}
 }
 private void startTimer(){
  if(Build.VERSION.SDK_INT>=23&&!Settings.canDrawOverlays(this)){status.setText("امنح إذن الظهور فوق التطبيقات أولًا");startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,Uri.parse("package:"+getPackageName())));return;}
  Intent i=new Intent(this,MeIslandService.class).setAction(MeIslandService.ACTION_TIMER);i.putExtra(MeIslandService.EXTRA_DURATION,(long)(duration.getProgress()+1)*60000L);
  try{if(Build.VERSION.SDK_INT>=26)startForegroundService(i);else startService(i);status.setText("تم تشغيل المؤقت");}catch(Exception e){status.setText("تعذر تشغيل الجزيرة: "+e.getMessage());}
 }
 @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(result!=RESULT_OK||data==null||data.getData()==null)return;
  try{if(request==PICK_THEME){editing=manager.importTheme(data.getData());build();status.setText("تم استيراد الثيم: "+editing.name);}
   else if(request==CREATE_THEME){manager.exportTheme(data.getData());status.setText("تم تصدير الثيم");}}
  catch(Exception e){status.setText("فشل تنفيذ العملية: "+e.getMessage());}
 }
}
''')

manifest = BASE / "AndroidManifest.xml"
m = manifest.read_text()
if "com.benny.openlauncher.mimax.MeIslandNotificationListener" not in m:
    m = m.replace("</application>", '''        <service
            android:name="com.benny.openlauncher.mimax.MeIslandNotificationListener"
            android:label="Mi_Max Me Island notification activities"
            android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE"
            android:exported="true">
            <intent-filter>
                <action android:name="android.service.notification.NotificationListenerService" />
            </intent-filter>
        </service>
        <receiver
            android:name="com.benny.openlauncher.mimax.MeIslandBatteryReceiver"
            android:exported="false">
            <intent-filter>
                <action android:name="android.intent.action.ACTION_POWER_CONNECTED" />
            </intent-filter>
        </receiver>
    </application>''', 1)
manifest.write_text(m)

master = BASE / "res/xml/preferences_master.xml"
p = master.read_text()
if "mimax_island_settings" not in p:
    entry = '''    <PreferenceCategory android:title="Mi_Max">
        <Preference
            android:title="Mi_Max Me Island"
            android:summary="LTIN, HIS, ColorOS, live activities and .mt1 themes">
            <intent android:targetPackage="com.mimax.launcher"
                android:targetClass="com.benny.openlauncher.mimax.MeIslandSettingsActivity" />
        </Preference>
        <Preference
            android:title="Mi_Max Extensions"
            android:summary="Install and manage declarative extension packages">
            <intent android:targetPackage="com.mimax.launcher"
                android:targetClass="com.benny.openlauncher.mimax.ExtensionManagerActivity" />
        </Preference>
    </PreferenceCategory>

'''
    p = p.replace("</PreferenceScreen>", entry + "</PreferenceScreen>", 1)
master.write_text(p)

print("Extended Me Island engines, live notification activity bridge, timer, charging event, theme editor and .mt1 import/export.")


# Separate maintenance path that can reset broken imported packs.

(JAVA / "ExtensionRecoveryActivity.java").write_text(r'''package com.benny.openlauncher.mimax;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.*;
import java.io.File;
public final class ExtensionRecoveryActivity extends Activity {
 private LinearLayout root;
 private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
 @Override protected void onCreate(Bundle b){super.onCreate(b);root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(20),dp(20),dp(20),dp(20));root.setBackgroundColor(0xff101722);
  TextView title=new TextView(this);title.setText("Mi_Max Recovery");title.setTextSize(24);title.setTextColor(-1);root.addView(title);
  TextView note=new TextView(this);note.setText("Independent maintenance screen. It can reset imported visual packs without loading the normal launcher workspace.");note.setTextColor(0xffcbd5e1);note.setPadding(0,dp(12),0,dp(16));root.addView(note);
  Button reset=new Button(this);reset.setText("Reset Me Island to built-in HIS");reset.setOnClickListener(v->{new MeIslandThemeManager(this).removeAllImported();Toast.makeText(this,"Visual packs reset",Toast.LENGTH_SHORT).show();});root.addView(reset);
  Button clear=new Button(this);clear.setText("Remove all installed declarative extensions");clear.setOnClickListener(v->{File dir=new File(getFilesDir(),"mimax-extensions");delete(dir);Toast.makeText(this,"Extension storage cleared",Toast.LENGTH_SHORT).show();});root.addView(clear);
  Button manage=new Button(this);manage.setText("Open Extension Manager");manage.setOnClickListener(v->startActivity(new Intent(this,ExtensionManagerActivity.class)));root.addView(manage);
  Button island=new Button(this);island.setText("Open Me Island settings");island.setOnClickListener(v->startActivity(new Intent(this,MeIslandSettingsActivity.class)));root.addView(island);
  setContentView(root);
 }
 private void delete(File f){if(f.isDirectory()){File[] a=f.listFiles();if(a!=null)for(File x:a)delete(x);}if(f.exists())f.delete();}
}
''')

manifest = BASE / "AndroidManifest.xml"
m = manifest.read_text()
if "com.benny.openlauncher.mimax.ExtensionRecoveryActivity" not in m:
    m = m.replace("</application>", '''        <activity
            android:name="com.benny.openlauncher.mimax.ExtensionRecoveryActivity"
            android:exported="true"
            android:label="Mi_Max Recovery">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>''', 1)
manifest.write_text(m)


# Built-in offline .mt1 theme catalogue.

(JAVA / "MeIslandStoreActivity.java").write_text(r'''package com.benny.openlauncher.mimax;

import android.app.Activity;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.*;
import java.util.*;

public final class MeIslandStoreActivity extends Activity {
 private MeIslandThemeManager manager;
 private LinearLayout list;
 private TextView storeStatus;
 private final java.util.concurrent.ExecutorService worker=java.util.concurrent.Executors.newSingleThreadExecutor();
 private static final String CATALOG_URL="https://raw.githubusercontent.com/mmgg3yn-png/MI_Max/openlauncher-foundation/extensions/store/catalog.json";
 private static final String[][] PACKS={
  {"oneplus_split","OnePlus Split","OnePlus-inspired split activity card with spring geometry","custom","split","spring","4010806080","4293529600","34","20","224","40","124","360"},
  {"hyper_wide","Hyper Wide","Wide HyperIsland-style activity card","his","wide_card","morph","3994021149","4290316799","28","24","244","44","140","320"},
  {"coloros_glass","ColorOS Glass","Fluid translucent capsule with softer corners","coloros","fluid","morph","3425055540","4290638847","44","30","210","44","132","420"},
  {"ltin_compact","LTIN Compact","Compact dark pill with a spring expansion","ltin","pill","spring","4278190080","4294967295","12","30","174","34","96","240"}
 };
 private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
 @Override protected void onCreate(Bundle b){super.onCreate(b);manager=new MeIslandThemeManager(this);
  ScrollView scroll=new ScrollView(this);list=new LinearLayout(this);list.setOrientation(1);list.setPadding(dp(18),dp(18),dp(18),dp(24));list.setBackgroundColor(0xff101722);scroll.addView(list);
  TextView title=new TextView(this);title.setText("Me Island Theme Store");title.setTextColor(-1);title.setTextSize(24);list.addView(title);
  TextView note=new TextView(this);note.setText("Install declarative theme packs independently of the launcher APK. Each pack changes actual card geometry, layout and motion.");note.setTextColor(0xffc5d1df);note.setPadding(0,dp(8),0,dp(14));list.addView(note);
  Button importPack=new Button(this);importPack.setText("Import .mt1 from storage");importPack.setOnClickListener(v->startActivity(new android.content.Intent(this,MeIslandSettingsActivity.class)));list.addView(importPack);
  Button online=new Button(this);online.setText("Check online catalogue and updates");list.addView(online);online.setOnClickListener(v->loadOnlineCatalog());
  storeStatus=new TextView(this);storeStatus.setTextColor(0xffb8d9ff);storeStatus.setPadding(0,dp(6),0,dp(12));list.addView(storeStatus);
  for(String[] pack:PACKS)addPack(pack);
  setContentView(scroll);
 }
 private void loadOnlineCatalog(){
  storeStatus.setText("Checking secure Mi_Max theme catalogue…");
  worker.execute(()->{
   try{
    String raw=readUrl(CATALOG_URL,65536);
    org.json.JSONObject root=new org.json.JSONObject(raw);
    org.json.JSONArray themes=root.optJSONArray("themes");
    if(themes==null)throw new java.io.IOException("Catalogue has no themes array");
    int installed=0;
    for(int n=0;n<themes.length();n++){
     org.json.JSONObject item=themes.getJSONObject(n);
     String name=item.optString("name","Theme"),url=item.optString("url",""),expected=item.optString("sha256","").toLowerCase(java.util.Locale.ROOT);
     if(!url.startsWith("https://raw.githubusercontent.com/mmgg3yn-png/MI_Max/")||expected.length()!=64)continue;
     String manifest=readUrl(url,131072);
     String actual=sha256(manifest.getBytes(java.nio.charset.StandardCharsets.UTF_8));
     if(!actual.equals(expected))throw new SecurityException("Integrity check failed for "+name);
     manager.installJson(manifest,false);
     installed++;
    }
    final int count=installed;
    runOnUiThread(()->storeStatus.setText("Catalogue v"+root.optInt("version",1)+": installed/updated "+count+" packs. Select one from the local list to activate it."));
   }catch(Exception e){runOnUiThread(()->storeStatus.setText("Catalogue update failed: "+e.getMessage()));}
  });
 }
 private String readUrl(String address,int limit)throws Exception{
  java.net.HttpURLConnection c=(java.net.HttpURLConnection)new java.net.URL(address).openConnection();
  c.setConnectTimeout(12000);c.setReadTimeout(18000);c.setRequestProperty("Accept","application/json");
  int code=c.getResponseCode();if(code<200||code>=300){c.disconnect();throw new java.io.IOException("HTTP "+code);}
  try(java.io.InputStream in=c.getInputStream();java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream()){
   byte[] b=new byte[4096];int n,total=0;while((n=in.read(b))!=-1){total+=n;if(total>limit)throw new java.io.IOException("Remote theme file is too large");out.write(b,0,n);}
   return out.toString("UTF-8");
  }finally{c.disconnect();}
 }
 private String sha256(byte[] data)throws Exception{
  byte[] digest=java.security.MessageDigest.getInstance("SHA-256").digest(data);
  StringBuilder out=new StringBuilder();for(byte b:digest)out.append(String.format(java.util.Locale.ROOT,"%02x",b&255));return out.toString();
 }
 private void addPack(String[] p){
  LinearLayout card=new LinearLayout(this);card.setOrientation(1);card.setPadding(dp(12),dp(12),dp(12),dp(12));card.setBackgroundColor(0xff202b39);
  LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=dp(10);list.addView(card,lp);
  TextView title=new TextView(this);title.setText(p[1]);title.setTextColor(-1);title.setTextSize(17);card.addView(title);
  TextView desc=new TextView(this);desc.setText(p[2]+"\nEngine: "+p[3]+" • Layout: "+p[4]+" • Animation: "+p[5]);desc.setTextColor(0xffc0ccda);card.addView(desc);
  boolean installed=manager.findTheme(p[0])!=null;
  Button install=new Button(this);install.setText(installed?"Reinstall / Update pack":"Install theme pack");card.addView(install);
  install.setOnClickListener(v->{
   try{
    String json=new org.json.JSONObject().put("format","mimax-island-theme").put("id",p[0]).put("name",p[1]).put("style",p[3]).put("layout",p[4]).put("animation",p[5])
     .put("background",Long.parseLong(p[6])).put("accent",Long.parseLong(p[7])).put("blur",Integer.parseInt(p[8])).put("cornerDp",Integer.parseInt(p[9]))
     .put("widthDp",Integer.parseInt(p[10])).put("compactHeightDp",Integer.parseInt(p[11])).put("expandedHeightDp",Integer.parseInt(p[12])).put("animationMs",Integer.parseInt(p[13])).toString();
    manager.installJson(json);
    Toast.makeText(this,"Installed and applied "+p[1],Toast.LENGTH_SHORT).show();
    install.setText("Reinstall / Update pack");
   }catch(Exception e){Toast.makeText(this,"Could not install: "+e.getMessage(),Toast.LENGTH_LONG).show();}
  });
  Button remove=new Button(this);remove.setText("Remove installed pack");remove.setEnabled(installed);card.addView(remove);
  remove.setOnClickListener(v->{if(manager.remove(p[0])){Toast.makeText(this,"Pack removed",Toast.LENGTH_SHORT).show();remove.setEnabled(false);}else Toast.makeText(this,"Cannot remove a built-in engine",Toast.LENGTH_SHORT).show();});
 }
 @Override protected void onDestroy(){worker.shutdownNow();super.onDestroy();}
}
''')

manifest=BASE / "AndroidManifest.xml"
m=manifest.read_text()
if "com.benny.openlauncher.mimax.MeIslandStoreActivity" not in m:
    m=m.replace("</application>",'''        <activity android:name="com.benny.openlauncher.mimax.MeIslandStoreActivity" android:exported="false" android:label="Me Island Theme Store" />
    </application>''',1)
manifest.write_text(m)

settings=JAVA / "MeIslandSettingsActivity.java"
s=settings.read_text()
if "MeIslandStoreActivity" not in s:
    old='''  Button extensions=button("إدارة الإضافات");content.addView(extensions);extensions.setOnClickListener(v->startActivity(new Intent(this,ExtensionManagerActivity.class)));'''
    new='''  Button store=button("فتح متجر ثيمات الجزيرة");content.addView(store);store.setOnClickListener(v->startActivity(new Intent(this,MeIslandStoreActivity.class)));
  Button extensions=button("إدارة الإضافات");content.addView(extensions);extensions.setOnClickListener(v->startActivity(new Intent(this,ExtensionManagerActivity.class)));'''
    if old not in s: raise SystemExit("Missing MeIsland settings extension button anchor")
    settings.write_text(s.replace(old,new,1))
