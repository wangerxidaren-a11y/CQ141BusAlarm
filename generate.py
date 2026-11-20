from pathlib import Path

PROJECT_DIR = Path("CQ141BusAlarm")

FILES = {
    "README.md": """# 公交强提醒助手（小米 17 / 安卓极简版）

## 功能说明
- 监听指定公交软件（高德地图、车来了、百度地图）的通知栏消息。
- 全天不限时生效，支持在 App 主界面自由输入任意线路号（多条用逗号或空格隔开，例如 `141, 465`）。
- 检测到包含目标线路号的通知时，自动拉满系统闹钟音量、连续语音播报、循环震动并亮屏全屏弹窗。
""",
    "settings.gradle.kts": """pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "CQ141BusAlarm"
include(":app")
""",
    "build.gradle.kts": """plugins {
    id("com.android.application") version "8.5.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.24" apply false
}
""",
    "gradle.properties": """org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=false
kotlin.code.style=official
android.nonTransitiveRClass=true
""",
    "gradle/wrapper/gradle-wrapper.properties": """distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.7-bin.zip
networkTimeout=10000
validateDistributionUrl=true
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
""",
    "app/proguard-rules.pro": """# Keep notification listener service
-keep class com.erxi.cq141alarm.BusNotificationListener { *; }
""",
    "app/build.gradle.kts": """plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.erxi.cq141alarm"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.erxi.cq141alarm"
        minSdk = 26
        targetSdk = 35
        versionCode = 9
        versionName = "2.0.1"
    }

    signingConfigs {
        create("fixed") {
            val storePath = System.getenv("KEYSTORE_PATH")
            if (storePath != null) {
                storeFile = file(storePath)
                storePassword = System.getenv("KEYSTORE_PASSWORD")
                keyAlias = System.getenv("KEY_ALIAS")
                keyPassword = System.getenv("KEY_PASSWORD")
                storeType = "PKCS12"
            }
        }
    }

    buildTypes {
        debug {
            val fixed = signingConfigs.getByName("fixed")
            if (fixed.storeFile != null) {
                signingConfig = fixed
            }
        }
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            val fixed = signingConfigs.getByName("fixed")
            if (fixed.storeFile != null) {
                signingConfig = fixed
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    // 零第三方依赖，纯原生 Android Framework API
}
""",
    "app/src/main/res/values/strings.xml": """<resources>
    <string name="app_name">公交强提醒</string>
</resources>
""",
    "app/src/main/AndroidManifest.xml": """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.VIBRATE" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-permission android:name="android.permission.USE_FULL_SCREEN_INTENT" />
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_DATA_SYNC" />
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />

    <application
        android:allowBackup="true"
        android:icon="@android:drawable/ic_lock_idle_alarm"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:theme="@android:style/Theme.Material.Light.DarkActionBar">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <activity
            android:name=".AlarmAlertActivity"
            android:exported="false"
            android:launchMode="singleTop"
            android:showWhenLocked="true"
            android:turnScreenOn="true"
            android:excludeFromRecents="true"
            android:theme="@android:style/Theme.Material.NoActionBar.Fullscreen" />

        <service
            android:name=".BusNotificationListener"
            android:exported="true"
            android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE">
            <intent-filter>
                <action android:name="android.service.notification.NotificationListenerService" />
            </intent-filter>
        </service>

        <service
            android:name=".WatchService"
            android:exported="false"
            android:foregroundServiceType="dataSync" />

        <receiver
            android:name=".BootReceiver"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED" />
            </intent-filter>
        </receiver>
    </application>

</manifest>
""",
    "app/src/main/java/com/erxi/cq141alarm/AlarmConfig.kt": """package com.erxi.cq141alarm

import android.content.Context

object AlarmConfig {
    private const val PREFS_NAME = "bus_alarm_prefs"
    private const val KEY_KEYWORDS = "keywords"
    private const val KEY_LAST_LOG = "last_log"
    private const val KEY_ANY_ROUTE = "any_route"

    fun isAnyRoute(context: Context): Boolean {
        val prefs = context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getBoolean(KEY_ANY_ROUTE, false)
    }

    fun setAnyRoute(context: Context, enabled: Boolean) {
        val prefs = context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putBoolean(KEY_ANY_ROUTE, enabled).apply()
    }

    fun getKeywordsRaw(context: Context): String {
        val prefs = context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_KEYWORDS, "141") ?: "141"
    }

    fun setKeywordsRaw(context: Context, raw: String) {
        val prefs = context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_KEYWORDS, raw.trim()).apply()
    }

    fun getKeywordList(context: Context): List<String> {
        return getKeywordsRaw(context)
            .split(",", "，", " ", "\\n", "、")
            .map { it.trim() }
            .filter { it.isNotEmpty() }
    }

    fun getLastLog(context: Context): String {
        val prefs = context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val stored = prefs.getString(KEY_LAST_LOG, "") ?: ""
        return if (stored.isBlank()) "暂未收到高德/车来了/百度地图通知" else stored
    }

    fun setLastLog(context: Context, log: String) {
        val prefs = context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val old = prefs.getString(KEY_LAST_LOG, "") ?: ""
        val lines = (listOf(log) + old.split("\\n")).filter { it.isNotBlank() }.take(6)
        prefs.edit().putString(KEY_LAST_LOG, lines.joinToString("\\n")).apply()
    }

    private const val KEY_LISTENER_STATUS = "listener_status"

    fun getListenerStatus(context: Context): String {
        val prefs = context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_LISTENER_STATUS, "未知（还没连上过）") ?: "未知（还没连上过）"
    }

    fun setListenerStatus(context: Context, status: String) {
        val prefs = context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_LISTENER_STATUS, status).apply()
    }

    // ===== v2.0 自查盯车配置（默认值为 141 路 · 解放东路，开箱即用） =====

    private const val KEY_WATCH_ENABLED = "watch_enabled"
    private const val KEY_WATCH_CITY_ID = "watch_city_id"
    private const val KEY_WATCH_LINE_NO = "watch_line_no"
    private const val KEY_WATCH_LINE_ID = "watch_line_id"
    private const val KEY_WATCH_LINE_ID_ALT = "watch_line_id_alt"
    private const val KEY_WATCH_DIR_DESC = "watch_dir_desc"
    private const val KEY_WATCH_DIR_DESC_ALT = "watch_dir_desc_alt"
    private const val KEY_WATCH_STATION_NAME = "watch_station_name"
    private const val KEY_WATCH_STATION_ID = "watch_station_id"
    private const val KEY_WATCH_TARGET_ORDER = "watch_target_order"
    private const val KEY_WATCH_LEAD = "watch_lead_stops"
    private const val KEY_WATCH_START = "watch_start"
    private const val KEY_WATCH_END = "watch_end"
    private const val KEY_WATCH_STATUS = "watch_status"
    private const val KEY_WATCH_BOOST_UNTIL = "watch_boost_until"
    private const val KEY_WATCH_FIRED = "watch_fired"

    private fun wprefs(context: Context) =
        context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun isWatchEnabled(context: Context): Boolean =
        wprefs(context).getBoolean(KEY_WATCH_ENABLED, false)

    fun setWatchEnabled(context: Context, enabled: Boolean) {
        wprefs(context).edit().putBoolean(KEY_WATCH_ENABLED, enabled).apply()
    }

    fun getWatchCityId(context: Context): String =
        wprefs(context).getString(KEY_WATCH_CITY_ID, "003") ?: "003"

    fun getWatchLineNo(context: Context): String =
        wprefs(context).getString(KEY_WATCH_LINE_NO, "141") ?: "141"

    fun getWatchLineId(context: Context): String =
        wprefs(context).getString(KEY_WATCH_LINE_ID, "023-141-1") ?: "023-141-1"

    fun getWatchLineIdAlt(context: Context): String =
        wprefs(context).getString(KEY_WATCH_LINE_ID_ALT, "023-141-0") ?: "023-141-0"

    fun getWatchDirDesc(context: Context): String =
        wprefs(context).getString(KEY_WATCH_DIR_DESC, "道门口 → 重庆北站北广场") ?: "道门口 → 重庆北站北广场"

    fun getWatchDirDescAlt(context: Context): String =
        wprefs(context).getString(KEY_WATCH_DIR_DESC_ALT, "重庆北站北广场 → 道门口") ?: "重庆北站北广场 → 道门口"

    fun getWatchStationName(context: Context): String =
        wprefs(context).getString(KEY_WATCH_STATION_NAME, "解放东路") ?: "解放东路"

    fun getWatchStationId(context: Context): String =
        wprefs(context).getString(KEY_WATCH_STATION_ID, "023-7208") ?: "023-7208"

    fun getWatchTargetOrder(context: Context): Int =
        wprefs(context).getInt(KEY_WATCH_TARGET_ORDER, 3)

    fun getWatchLead(context: Context): Int =
        wprefs(context).getInt(KEY_WATCH_LEAD, 1)

    fun setWatchLead(context: Context, lead: Int) {
        wprefs(context).edit().putInt(KEY_WATCH_LEAD, lead).apply()
    }

    fun getWatchStart(context: Context): String =
        wprefs(context).getString(KEY_WATCH_START, "07:00") ?: "07:00"

    fun getWatchEnd(context: Context): String =
        wprefs(context).getString(KEY_WATCH_END, "09:00") ?: "09:00"

    fun saveWatchWindow(context: Context, start: String, end: String) {
        wprefs(context).edit()
            .putString(KEY_WATCH_START, start)
            .putString(KEY_WATCH_END, end)
            .apply()
    }

    fun saveWatchLineInput(context: Context, lineNo: String, stationName: String) {
        wprefs(context).edit()
            .putString(KEY_WATCH_LINE_NO, lineNo)
            .putString(KEY_WATCH_STATION_NAME, stationName)
            .apply()
    }

    fun saveWatchResolved(
        context: Context,
        lineId: String, lineIdAlt: String,
        dirDesc: String, dirDescAlt: String,
        stationId: String, targetOrder: Int
    ) {
        wprefs(context).edit()
            .putString(KEY_WATCH_LINE_ID, lineId)
            .putString(KEY_WATCH_LINE_ID_ALT, lineIdAlt)
            .putString(KEY_WATCH_DIR_DESC, dirDesc)
            .putString(KEY_WATCH_DIR_DESC_ALT, dirDescAlt)
            .putString(KEY_WATCH_STATION_ID, stationId)
            .putInt(KEY_WATCH_TARGET_ORDER, targetOrder)
            .apply()
    }

    fun swapWatchDirection(context: Context) {
        val p = wprefs(context)
        val e = p.edit()
        e.putString(KEY_WATCH_LINE_ID, p.getString(KEY_WATCH_LINE_ID_ALT, "023-141-0"))
        e.putString(KEY_WATCH_LINE_ID_ALT, p.getString(KEY_WATCH_LINE_ID, "023-141-1"))
        e.putString(KEY_WATCH_DIR_DESC, p.getString(KEY_WATCH_DIR_DESC_ALT, ""))
        e.putString(KEY_WATCH_DIR_DESC_ALT, p.getString(KEY_WATCH_DIR_DESC, ""))
        e.apply()
    }

    fun getWatchStatus(context: Context): String =
        wprefs(context).getString(KEY_WATCH_STATUS, "尚未开始盯车") ?: "尚未开始盯车"

    fun setWatchStatus(context: Context, status: String) {
        wprefs(context).edit().putString(KEY_WATCH_STATUS, status).apply()
    }

    fun getWatchBoostUntil(context: Context): Long =
        wprefs(context).getLong(KEY_WATCH_BOOST_UNTIL, 0L)

    fun setWatchBoostUntil(context: Context, until: Long) {
        wprefs(context).edit().putLong(KEY_WATCH_BOOST_UNTIL, until).apply()
    }

    private const val KEY_WATCH_DIR_INDEX = "watch_dir_index"

    fun getWatchDirIndex(context: Context): Int =
        wprefs(context).getInt(KEY_WATCH_DIR_INDEX, 1)

    fun setWatchDirIndex(context: Context, idx: Int) {
        wprefs(context).edit().putInt(KEY_WATCH_DIR_INDEX, idx).apply()
    }

    fun getWatchFired(context: Context): String =
        wprefs(context).getString(KEY_WATCH_FIRED, "") ?: ""

    fun setWatchFired(context: Context, marker: String) {
        wprefs(context).edit().putString(KEY_WATCH_FIRED, marker).apply()
    }
}
""",
    "app/src/main/java/com/erxi/cq141alarm/MainActivity.kt": """package com.erxi.cq141alarm

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.view.Gravity
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Switch
import android.widget.TextView
import android.widget.Toast

class MainActivity : Activity() {

    private val handler = Handler(Looper.getMainLooper())
    private var testRunnable: Runnable? = null
    private lateinit var logView: TextView
    private lateinit var statusView: TextView
    private lateinit var lineInput: EditText
    private lateinit var stationInput: EditText
    private lateinit var startInput: EditText
    private lateinit var endInput: EditText
    private lateinit var leadLabel: TextView
    private lateinit var btnDirection: Button
    private lateinit var watchStatusView: TextView
    private lateinit var switchWatch: Switch

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        requestPostNotificationsIfNeeded()

        val scroll = ScrollView(this)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(56, 48, 56, 48)
        }

        val info = TextView(this).apply {
            text = "公交强提醒助手（v2.0.1）\\n自查盯车 + 通知监听双保险"
            textSize = 18f
            gravity = Gravity.CENTER
            setPadding(0, 0, 0, 32)
        }

        val routeLabel = TextView(this).apply {
            text = "监听线路关键词（多条用逗号或空格隔开）："
            textSize = 14f
            setTextColor(Color.DKGRAY)
            setPadding(0, 0, 0, 8)
        }

        val routeInput = EditText(this).apply {
            setText(AlarmConfig.getKeywordsRaw(this@MainActivity))
            hint = "例如：141, 465"
            textSize = 16f
        }

        val btnSaveRoutes = Button(this).apply {
            text = "保存监听线路"
            setOnClickListener {
                val input = routeInput.text.toString().trim()
                if (input.isEmpty()) {
                    Toast.makeText(this@MainActivity, "请至少输入一个线路号", Toast.LENGTH_SHORT).show()
                } else {
                    AlarmConfig.setKeywordsRaw(this@MainActivity, input)
                    val list = AlarmConfig.getKeywordList(this@MainActivity).joinToString("、")
                    Toast.makeText(this@MainActivity, "已保存监听：$list", Toast.LENGTH_SHORT).show()
                }
            }
        }

        val anyRouteSwitch = Switch(this).apply {
            text = "任意线路模式（这三个软件来任何线路都提醒）"
            textSize = 15f
            isChecked = AlarmConfig.isAnyRoute(this@MainActivity)
            setPadding(0, 24, 0, 8)
            setOnCheckedChangeListener { _, checked ->
                AlarmConfig.setAnyRoute(this@MainActivity, checked)
                Toast.makeText(
                    this@MainActivity,
                    if (checked) "已开启任意线路模式" else "已关闭任意线路模式，按线路关键词提醒",
                    Toast.LENGTH_SHORT
                ).show()
            }
        }

        val btnNotifyListener = Button(this).apply {
            text = "1. 开启“通知读取权限”"
            setOnClickListener {
                startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
            }
        }

        val btnFullScreenPerm = Button(this).apply {
            text = "2. 开启全屏闹钟弹窗权限"
            setOnClickListener {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
                    val intent = Intent(Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT).apply {
                        data = Uri.parse("package:$packageName")
                    }
                    startActivity(intent)
                } else {
                    Toast.makeText(this@MainActivity, "当前系统默认支持全屏弹窗", Toast.LENGTH_SHORT).show()
                }
            }
        }

        val btnTest = Button(this).apply {
            text = "3. 5秒后测试（点完请立即锁屏）"
            setOnClickListener {
                testRunnable?.let { handler.removeCallbacks(it) }

                val firstKeyword = AlarmConfig.getKeywordList(this@MainActivity).firstOrNull() ?: "141"
                val label = if (firstKeyword.endsWith("路")) firstKeyword else "${firstKeyword}路"

                Toast.makeText(this@MainActivity, "5秒后触发，请立即按电源键锁屏测试", Toast.LENGTH_SHORT).show()
                isEnabled = false
                text = "倒计时 5 秒，请立即锁屏..."

                val task = Runnable {
                    AlarmPlayer.start(this@MainActivity, "【锁屏实测】${label}距您还有 2 站，请立即出门！", label)
                    isEnabled = true
                    text = "3. 5秒后测试（点完请立即锁屏）"
                }
                testRunnable = task
                handler.postDelayed(task, 5000L)
            }
        }

        val btnStop = Button(this).apply {
            text = "4. 我出门了（停止响铃 / 取消测试）"
            setOnClickListener {
                testRunnable?.let { handler.removeCallbacks(it) }
                btnTest.isEnabled = true
                btnTest.text = "3. 5秒后测试（点完请立即锁屏）"
                AlarmPlayer.stop(this@MainActivity)
            }
        }

        statusView = TextView(this).apply {
            textSize = 13f
            setTextColor(Color.DKGRAY)
            setPadding(0, 32, 0, 4)
        }

        logView = TextView(this).apply {
            textSize = 13f
            setTextColor(Color.GRAY)
            setPadding(0, 4, 0, 16)
        }

        layout.addView(info)
        layout.addView(routeLabel)
        layout.addView(routeInput)
        layout.addView(btnSaveRoutes)
        layout.addView(anyRouteSwitch)
        layout.addView(btnNotifyListener)
        layout.addView(btnFullScreenPerm)
        layout.addView(btnTest)
        layout.addView(btnStop)

        // ===== v2.0 自查盯车 =====
        val watchTitle = TextView(this).apply {
            text = "自查盯车（软件自己查车，不依赖别的 App 通知）"
            textSize = 16f
            setTextColor(Color.BLACK)
            setPadding(0, 40, 0, 8)
        }

        lineInput = EditText(this).apply {
            hint = "线路号（如：141）"
            setText(AlarmConfig.getWatchLineNo(this@MainActivity))
            setSingleLine(true)
        }

        stationInput = EditText(this).apply {
            hint = "上车站名（如：解放东路）"
            setText(AlarmConfig.getWatchStationName(this@MainActivity))
            setSingleLine(true)
        }

        btnDirection = Button(this).apply {
            text = "方向：" + AlarmConfig.getWatchDirDesc(this@MainActivity) + "（点此切换）"
            setOnClickListener {
                val next = if (AlarmConfig.getWatchDirIndex(this@MainActivity) == 0) 1 else 0
                AlarmConfig.setWatchDirIndex(this@MainActivity, next)
                resolveWatch()
            }
        }

        val btnResolve = Button(this).apply {
            text = "查找并保存线路站点"
            setOnClickListener { resolveWatch() }
        }

        leadLabel = TextView(this).apply {
            text = "提前 " + AlarmConfig.getWatchLead(this@MainActivity) + " 站提醒"
            textSize = 15f
            gravity = Gravity.CENTER
        }
        val btnLeadMinus = Button(this).apply {
            text = "－"
            setOnClickListener {
                val v = (AlarmConfig.getWatchLead(this@MainActivity) - 1).coerceIn(0, 5)
                AlarmConfig.setWatchLead(this@MainActivity, v)
                leadLabel.text = "提前 " + v + " 站提醒"
            }
        }
        val btnLeadPlus = Button(this).apply {
            text = "＋"
            setOnClickListener {
                val v = (AlarmConfig.getWatchLead(this@MainActivity) + 1).coerceIn(0, 5)
                AlarmConfig.setWatchLead(this@MainActivity, v)
                leadLabel.text = "提前 " + v + " 站提醒"
            }
        }
        val leadRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            addView(btnLeadMinus)
            addView(leadLabel, LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f))
            addView(btnLeadPlus)
        }

        startInput = EditText(this).apply {
            hint = "开始 07:00"
            setText(AlarmConfig.getWatchStart(this@MainActivity))
            setSingleLine(true)
        }
        endInput = EditText(this).apply {
            hint = "结束 09:00"
            setText(AlarmConfig.getWatchEnd(this@MainActivity))
            setSingleLine(true)
        }
        val windowRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            addView(startInput, LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f))
            addView(endInput, LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f))
        }

        switchWatch = Switch(this).apply {
            text = "自查盯车开关（打开就盯，每 30 秒查一次）"
            textSize = 15f
            setPadding(0, 16, 0, 16)
            isChecked = AlarmConfig.isWatchEnabled(this@MainActivity)
        }
        switchWatch.setOnCheckedChangeListener { _, checked ->
            if (checked) {
                if (!saveWatchWindow()) {
                    AlarmConfig.setWatchEnabled(this@MainActivity, false)
                    return@setOnCheckedChangeListener
                }
                AlarmConfig.setWatchEnabled(this@MainActivity, true)
                // 手动打开 = 立刻开盯，最长连盯 12 小时；时段只管每天自动恢复
                AlarmConfig.setWatchBoostUntil(this@MainActivity, System.currentTimeMillis() + 12 * 60 * 60 * 1000L)
                WatchService.start(this@MainActivity)
                Toast.makeText(this@MainActivity, "自查盯车已开启，立刻开始盯", Toast.LENGTH_SHORT).show()
            } else {
                AlarmConfig.setWatchEnabled(this@MainActivity, false)
                WatchService.stop(this@MainActivity)
                Toast.makeText(this@MainActivity, "自查盯车已关闭", Toast.LENGTH_SHORT).show()
            }
        }

        val btnBoost = Button(this).apply {
            text = "立即盯车 45 分钟（测试用）"
            setOnClickListener {
                if (!saveWatchWindow()) return@setOnClickListener
                AlarmConfig.setWatchEnabled(this@MainActivity, true)
                switchWatch.isChecked = true
                AlarmConfig.setWatchBoostUntil(this@MainActivity, System.currentTimeMillis() + 45 * 60 * 1000L)
                WatchService.start(this@MainActivity)
                Toast.makeText(this@MainActivity, "开始盯车 45 分钟，下拉看盯车状态", Toast.LENGTH_LONG).show()
            }
        }

        watchStatusView = TextView(this).apply {
            textSize = 13f
            setTextColor(Color.DKGRAY)
            setPadding(0, 8, 0, 16)
        }

        layout.addView(watchTitle)
        layout.addView(lineInput)
        layout.addView(stationInput)
        layout.addView(btnDirection)
        layout.addView(btnResolve)
        layout.addView(leadRow)
        layout.addView(windowRow)
        layout.addView(switchWatch)
        layout.addView(btnBoost)
        layout.addView(watchStatusView)
        layout.addView(statusView)
        layout.addView(logView)
        scroll.addView(layout)
        setContentView(scroll)
    }

    private fun saveWatchWindow(): Boolean {
        fun parse(s: String): String? {
            val t = s.replace("：", ":").replace(" ", "").trim()
            val p = t.split(":")
            if (p.size != 2) return null
            val h = p[0].toIntOrNull() ?: return null
            val m = p[1].toIntOrNull() ?: return null
            if (h !in 0..23 || m !in 0..59) return null
            return h.toString().padStart(2, '0') + ":" + m.toString().padStart(2, '0')
        }
        val s = parse(startInput.text.toString())
        val e = parse(endInput.text.toString())
        if (s == null || e == null) {
            Toast.makeText(this, "时段格式不对，填如 8:30", Toast.LENGTH_LONG).show()
            return false
        }
        AlarmConfig.saveWatchWindow(this, s, e)
        startInput.setText(s)
        endInput.setText(e)
        return true
    }

    private fun resolveWatch() {
        val lineNo = lineInput.text.toString().trim()
        val stationName = stationInput.text.toString().trim()
        if (lineNo.isEmpty() || stationName.isEmpty()) {
            Toast.makeText(this, "先填线路号和上车站名", Toast.LENGTH_LONG).show()
            return
        }
        AlarmConfig.saveWatchLineInput(this, lineNo, stationName)
        watchStatusView.text = "盯车状态：正在查找 $lineNo 路 · $stationName …"
        Thread {
            try {
                val cityId = AlarmConfig.getWatchCityId(this)
                val search = ChelaileApi.searchLines(cityId, lineNo)
                val lines = search.optJSONObject("result")?.optJSONArray("lines")
                    ?: throw IllegalStateException("没查到线路")
                val dirIds = mutableListOf<String>()
                val dirDescs = mutableListOf<String>()
                for (i in 0 until lines.length()) {
                    val l = lines.getJSONObject(i)
                    if (!l.optString("name").contains(lineNo)) continue
                    dirIds.add(l.optString("lineId"))
                    dirDescs.add(l.optString("startSn") + " → " + l.optString("endSn"))
                }
                if (dirIds.isEmpty()) throw IllegalStateException("没查到 $lineNo 路")
                val idx = AlarmConfig.getWatchDirIndex(this).coerceIn(0, dirIds.size - 1)
                val chosenId = dirIds[idx]
                val chosenDesc = dirDescs[idx]
                val altId = dirIds.getOrNull(1 - idx) ?: chosenId
                val altDesc = dirDescs.getOrNull(1 - idx) ?: chosenDesc
                val detail = ChelaileApi.lineDetail(cityId, chosenId)
                val stations = detail.optJSONArray("stations")
                    ?: throw IllegalStateException("线路无站点数据")
                var stationId = ""
                var order = -1
                for (i in 0 until stations.length()) {
                    val st = stations.getJSONObject(i)
                    if (st.optString("sn") == stationName) {
                        stationId = st.optString("sId")
                        order = st.optInt("order", -1)
                        break
                    }
                }
                if (order < 0) throw IllegalStateException("这个方向上没找到站：" + stationName)
                AlarmConfig.saveWatchResolved(this, chosenId, altId, chosenDesc, altDesc, stationId, order)
                runOnUiThread {
                    btnDirection.text = "方向：" + chosenDesc + "（点此切换）"
                    watchStatusView.text = "盯车状态：已保存 " + lineNo + "路 · " + chosenDesc +
                        " · " + stationName + "（第 " + order + " 站）"
                    Toast.makeText(this, "已保存，可以开盯车开关了", Toast.LENGTH_LONG).show()
                }
            } catch (e: Exception) {
                runOnUiThread {
                    watchStatusView.text = "盯车状态：查找失败：" + (e.message ?: "未知错误")
                }
            }
        }.start()
    }

    override fun onResume() {
        super.onResume()
        statusView.text = "监听状态：${AlarmConfig.getListenerStatus(this)}"
        logView.text = "最近捕获的通知：\\n${AlarmConfig.getLastLog(this)}"
        if (::watchStatusView.isInitialized) {
            watchStatusView.text = "盯车状态：" + AlarmConfig.getWatchStatus(this)
        }
    }

    private fun requestPostNotificationsIfNeeded() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1001)
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        testRunnable?.let { handler.removeCallbacks(it) }
    }
}
""",
    "app/src/main/java/com/erxi/cq141alarm/AlarmAlertActivity.kt": """package com.erxi.cq141alarm

import android.app.Activity
import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.view.Gravity
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

class AlarmAlertActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
        }
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        val busRoute = intent.getStringExtra("bus_route") ?: "公交"
        val busMsg = intent.getStringExtra("bus_msg") ?: "${busRoute}快到了！"

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(Color.parseColor("#B71C1C"))
            setPadding(64, 64, 64, 64)
        }

        val title = TextView(this).apply {
            text = "🚌 ${busRoute}快到了！"
            textSize = 32f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
        }

        val detail = TextView(this).apply {
            text = busMsg
            textSize = 18f
            setTextColor(Color.parseColor("#FFCDD2"))
            gravity = Gravity.CENTER
            setPadding(0, 24, 0, 96)
        }

        val stopBtn = Button(this).apply {
            text = "我出门了 · 停止响铃"
            textSize = 22f
            setTextColor(Color.parseColor("#B71C1C"))
            setBackgroundColor(Color.WHITE)
            setPadding(64, 48, 64, 48)
            setOnClickListener {
                AlarmPlayer.stop(this@AlarmAlertActivity)
                finish()
            }
        }

        root.addView(title)
        root.addView(detail)
        root.addView(stopBtn)
        setContentView(root)
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        // 必须点击“停止响铃”按钮退出，防止误触返回键
    }
}
""",
    "app/src/main/java/com/erxi/cq141alarm/AlarmPlayer.kt": """package com.erxi.cq141alarm

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.media.AudioAttributes
import android.media.AudioManager
import android.media.MediaPlayer
import android.media.RingtoneManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import java.util.Locale

object AlarmPlayer {

    enum class AlertMode {
        TTS_VOICE,
        CUSTOM_MP3
    }

    private val MODE = AlertMode.TTS_VOICE
    private const val CHANNEL_ID = "bus_141_alarm_channel"
    private const val NOTIF_ID = 14101

    private val mainHandler = Handler(Looper.getMainLooper())
    private var mediaPlayer: MediaPlayer? = null
    private var tts: TextToSpeech? = null
    private var vibrator: Vibrator? = null
    private var currentSpeechText: String = "公交快到了，快出门！"

    @Volatile var isRinging: Boolean = false
        private set

    fun start(context: Context, message: String = "公交即将到站", routeLabel: String = "公交") {
        if (isRinging) return
        isRinging = true
        currentSpeechText = "${routeLabel}快到了，快出门！"

        val appCtx = context.applicationContext

        val audioManager = appCtx.getSystemService(Context.AUDIO_SERVICE) as AudioManager
        val maxAlarmVol = audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM)
        audioManager.setStreamVolume(AudioManager.STREAM_ALARM, maxAlarmVol, 0)

        when (MODE) {
            AlertMode.TTS_VOICE -> startTtsLoop(appCtx)
            AlertMode.CUSTOM_MP3 -> startMp3Loop(appCtx)
        }

        vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            (appCtx.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager).defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            appCtx.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        }
        vibrator?.vibrate(VibrationEffect.createWaveform(longArrayOf(0, 800, 300), 0))

        showFullScreenAlarm(appCtx, message, routeLabel)
    }

    private fun startMp3Loop(appCtx: Context) {
        val rawResId = appCtx.resources.getIdentifier("bus_alarm", "raw", appCtx.packageName)

        mediaPlayer = MediaPlayer().apply {
            setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build()
            )
            if (rawResId != 0) {
                appCtx.resources.openRawResourceFd(rawResId).use { afd ->
                    setDataSource(afd.fileDescriptor, afd.startOffset, afd.length)
                }
            } else {
                val fallbackUri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
                    ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_RINGTONE)
                setDataSource(appCtx, fallbackUri)
            }
            isLooping = true
            prepare()
            start()
        }
    }

    private fun startTtsLoop(appCtx: Context) {
        val alarmAttrs = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_ALARM)
            .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
            .build()

        val params = Bundle().apply {
            putInt(TextToSpeech.Engine.KEY_PARAM_STREAM, AudioManager.STREAM_ALARM)
            putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, 1.0f)
        }

        tts = TextToSpeech(appCtx) { status ->
            if (status == TextToSpeech.SUCCESS && isRinging) {
                tts?.apply {
                    language = Locale.CHINA
                    setSpeechRate(1.1f)
                    setAudioAttributes(alarmAttrs)
                    setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                        override fun onStart(utteranceId: String?) {}
                        override fun onError(utteranceId: String?) {}
                        override fun onDone(utteranceId: String?) {
                            if (isRinging) {
                                mainHandler.postDelayed({
                                    if (isRinging) {
                                        tts?.speak(currentSpeechText, TextToSpeech.QUEUE_FLUSH, params, "bus_alarm")
                                    }
                                }, 600L)
                            }
                        }
                    })
                    speak(currentSpeechText, TextToSpeech.QUEUE_FLUSH, params, "bus_alarm")
                }
            } else if (isRinging) {
                startMp3Loop(appCtx)
            }
        }
    }

    private fun showFullScreenAlarm(context: Context, message: String, routeLabel: String) {
        val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        val channel = NotificationChannel(
            CHANNEL_ID,
            "公交强提醒闹钟",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            lockscreenVisibility = Notification.VISIBILITY_PUBLIC
            setSound(null, null)
        }
        nm.createNotificationChannel(channel)

        val fullScreenIntent = Intent(context, AlarmAlertActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_NO_USER_ACTION
            putExtra("bus_msg", message)
            putExtra("bus_route", routeLabel)
        }
        val fullScreenPendingIntent = PendingIntent.getActivity(
            context,
            0,
            fullScreenIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = Notification.Builder(context, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setContentTitle("🚌 ${routeLabel}快到了")
            .setContentText(message)
            .setCategory(Notification.CATEGORY_ALARM)
            .setOngoing(true)
            .setFullScreenIntent(fullScreenPendingIntent, true)
            .setContentIntent(fullScreenPendingIntent)
            .build()

        nm.notify(NOTIF_ID, notification)
    }

    fun stop(context: Context? = null) {
        isRinging = false
        mainHandler.removeCallbacksAndMessages(null)

        mediaPlayer?.apply {
            if (isPlaying) stop()
            release()
        }
        mediaPlayer = null

        tts?.apply {
            stop()
            shutdown()
        }
        tts = null

        vibrator?.cancel()
        vibrator = null

        context?.applicationContext?.let {
            val nm = it.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            nm.cancel(NOTIF_ID)
        }
    }
}
""",
    "app/src/main/java/com/erxi/cq141alarm/ChelaileApi.kt": """package com.erxi.cq141alarm

import android.util.Base64
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.security.MessageDigest
import javax.crypto.Cipher
import javax.crypto.spec.SecretKeySpec

/**
 * 车来了上游接口（微信小程序同款）：参数签名 + AES-256-ECB 解密。
 * 协议来自开源社区实现；参数顺序对签名敏感，勿调整顺序。
 */
object ChelaileApi {

    private const val BASE = "https://web.chelaile.net.cn/api/bus/"
    private const val SALT = "qwihrnbtmj"
    private const val AES_KEY = "FF32AE65FBFD19414EAAFF6291A54B42"
    private const val UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0xf254160a) UnifiedPCWindowsWechat(0xf254160a) XWEB/18055"

    private val DEFAULT_PARAMS: List<Pair<String, String>> = listOf(
        "s" to "h5",
        "wxs" to "wx_app",
        "sign" to "1",
        "h5RealData" to "1",
        "v" to "3.11.28",
        "src" to "weixinapp_cx",
        "ctm_mp" to "mp_wx",
        "vc" to "2",
        "favoriteGray" to "1",
        "gpstype" to "wgs",
        "geo_type" to "wgs",
        "scene" to "1256"
    )

    private fun sign(params: List<Pair<String, String>>): String {
        val sb = StringBuilder()
        params.forEachIndexed { i, p ->
            if (i > 0) sb.append('&')
            sb.append('"').append(p.first).append('"').append('=').append('"').append(p.second).append('"')
        }
        sb.append(SALT)
        val digest = MessageDigest.getInstance("MD5").digest(sb.toString().toByteArray(Charsets.UTF_8))
        return digest.joinToString("") { "%02x".format(it.toInt() and 0xFF) }
    }

    private fun decrypt(cipherTextB64: String): String {
        val cipher = Cipher.getInstance("AES/ECB/PKCS5Padding")
        cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(AES_KEY.toByteArray(Charsets.US_ASCII), "AES"))
        val plain = cipher.doFinal(Base64.decode(cipherTextB64, Base64.DEFAULT))
        return String(plain, Charsets.UTF_8)
    }

    private fun extractJson(raw: String): JSONObject {
        val start = raw.indexOf('{')
        require(start >= 0) { "上游返回不是 JSON" }
        var depth = 0
        var inStr = false
        var escape = false
        for (i in start until raw.length) {
            val ch = raw[i]
            if (inStr) {
                if (escape) escape = false
                else if (ch == '\\\\') escape = true
                else if (ch == '"') inStr = false
                continue
            }
            when (ch) {
                '"' -> inStr = true
                '{' -> depth++
                '}' -> {
                    depth--
                    if (depth == 0) return JSONObject(raw.substring(start, i + 1))
                }
            }
        }
        throw IllegalStateException("上游 JSON 被截断")
    }

    fun get(endpoint: String, cityId: String, extra: List<Pair<String, String>>): JSONObject {
        val merged = LinkedHashMap<String, String>()
        DEFAULT_PARAMS.forEach { merged[it.first] = it.second }
        if (cityId.isNotEmpty()) {
            merged["cityId"] = cityId
            merged["localCityId"] = cityId
        }
        extra.forEach { merged[it.first] = it.second }
        val params = merged.entries.map { it.key to it.value }
        val all = params + ("cryptoSign" to sign(params))
        val query = all.joinToString("&") {
            URLEncoder.encode(it.first, "UTF-8") + "=" + URLEncoder.encode(it.second, "UTF-8")
        }
        val conn = URL(BASE + endpoint + "?" + query).openConnection() as HttpURLConnection
        conn.requestMethod = "GET"
        conn.connectTimeout = 15000
        conn.readTimeout = 15000
        conn.setRequestProperty("User-Agent", UA)
        conn.setRequestProperty("xweb_xhr", "1")
        conn.setRequestProperty("Content-Type", "text")
        conn.setRequestProperty("Accept", "*/*")
        conn.setRequestProperty("Sec-Fetch-Site", "cross-site")
        conn.setRequestProperty("Sec-Fetch-Mode", "cors")
        conn.setRequestProperty("Sec-Fetch-Dest", "empty")
        conn.setRequestProperty("Referer", "https://servicewechat.com/wx71d589ea01ce3321/814/page-frame.html")
        conn.setRequestProperty("Accept-Language", "zh-CN,zh;q=0.9")
        val raw = conn.inputStream.bufferedReader(Charsets.UTF_8).readText()
        conn.disconnect()
        val envelope = extractJson(raw)
        val jsonr = envelope.optJSONObject("jsonr") ?: throw IllegalStateException("上游信封异常")
        val status = jsonr.optString("status", "")
        if (status.isNotEmpty() && status !in setOf("00", "0000", "0")) {
            throw IllegalStateException("上游状态 $status：" + jsonr.optString("errmsg"))
        }
        val data = jsonr.optJSONObject("data") ?: JSONObject()
        val enc = data.optString("encryptResult", "")
        return if (enc.isNotEmpty()) JSONObject(decrypt(enc)) else data
    }

    fun searchLines(cityId: String, keyword: String): JSONObject =
        get(
            "query!nSearch.action", cityId, listOf(
                "cityId" to cityId, "localCityId" to cityId,
                "key" to keyword, "supportPhyStn" to "true"
            )
        )

    fun lineDetail(cityId: String, lineId: String): JSONObject =
        get(
            "line!encryptedLineDetail.action", cityId, listOf(
                "cityId" to cityId, "localCityId" to cityId, "lineId" to lineId,
                "lat" to "", "lng" to "", "geo_lat" to "", "geo_lng" to ""
            )
        )

    fun busDetail(cityId: String, lineId: String, targetOrder: Int, stationId: String): JSONObject =
        get(
            "line!encryptedBusDetail.action", cityId, listOf(
                "cshow" to "busDetail", "specail" to "0", "specialType" to "undefined",
                "cityId" to cityId, "localCityId" to cityId, "lineId" to lineId,
                "targetOrder" to targetOrder.toString(), "specialTargetOrder" to targetOrder.toString(),
                "stationId" to stationId,
                "lat" to "", "lng" to "", "geo_lat" to "", "geo_lng" to "",
                "userId" to "", "h5Id" to "", "unionId" to "", "accountId" to "", "secret" to ""
            )
        )
}
""",
    "app/src/main/java/com/erxi/cq141alarm/WatchService.kt": """package com.erxi.cq141alarm

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale

/** v2.0 自查盯车：时段内每 30 秒直查车来了实时数据，车到站前触发强提醒。 */
class WatchService : Service() {

    private val handler = Handler(Looper.getMainLooper())
    private var running = false

    private val tick = object : Runnable {
        override fun run() {
            if (!AlarmConfig.isWatchEnabled(this@WatchService)) {
                stopSelf()
                return
            }
            val boosted = System.currentTimeMillis() < AlarmConfig.getWatchBoostUntil(this@WatchService)
            if (boosted || inWindow()) {
                poll()
            } else {
                AlarmConfig.setWatchStatus(
                    this@WatchService,
                    "不在盯车时段（" + AlarmConfig.getWatchStart(this@WatchService) + "–" +
                        AlarmConfig.getWatchEnd(this@WatchService) + "），待机中"
                )
            }
            handler.postDelayed(this, 30000)
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "盯车服务", NotificationManager.IMPORTANCE_LOW)
        )
        val notif = Notification.Builder(this, CHANNEL_ID)
            .setContentTitle("公交强提醒 · 盯车中")
            .setContentText(AlarmConfig.getWatchLineNo(this) + "路 · " + AlarmConfig.getWatchStationName(this) + "（自查实时数据）")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setOngoing(true)
            .build()
        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(NOTIF_ID, notif, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        } else {
            startForeground(NOTIF_ID, notif)
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (!running) {
            running = true
            handler.post(tick)
        }
        return START_STICKY
    }

    override fun onDestroy() {
        running = false
        handler.removeCallbacks(tick)
        super.onDestroy()
    }

    private fun inWindow(): Boolean {
        fun parse(s: String): Int {
            val parts = s.split(":")
            return (parts.getOrNull(0)?.toIntOrNull() ?: 0) * 60 +
                (parts.getOrNull(1)?.toIntOrNull() ?: 0)
        }
        val now = Calendar.getInstance()
        val cur = now.get(Calendar.HOUR_OF_DAY) * 60 + now.get(Calendar.MINUTE)
        val start = parse(AlarmConfig.getWatchStart(this))
        val end = parse(AlarmConfig.getWatchEnd(this))
        return if (end > start) cur in start until end else cur >= start || cur < end
    }

    private fun poll() {
        Thread {
            val ctx = this@WatchService
            val timeStr = SimpleDateFormat("HH:mm:ss", Locale.CHINA).format(Date())
            try {
                val data = ChelaileApi.busDetail(
                    AlarmConfig.getWatchCityId(ctx),
                    AlarmConfig.getWatchLineId(ctx),
                    AlarmConfig.getWatchTargetOrder(ctx),
                    AlarmConfig.getWatchStationId(ctx)
                )
                val buses = data.optJSONArray("buses")
                val target = AlarmConfig.getWatchTargetOrder(ctx)
                var nearestOrder = -1
                var nearestBusId = ""
                var nearestTravelSec = -1
                var total = 0
                if (buses != null) {
                    total = buses.length()
                    for (i in 0 until buses.length()) {
                        val b = buses.getJSONObject(i)
                        if (b.optInt("distanceToWaitStn", -1) < 0) continue
                        val order = b.optInt("order", -1)
                        if (order > nearestOrder) {
                            nearestOrder = order
                            nearestBusId = b.optString("busId", "")
                            val travels = b.optJSONArray("travels")
                            nearestTravelSec = if (travels != null && travels.length() > 0) {
                                travels.getJSONObject(0).optInt("travelTime", -1)
                            } else {
                                -1
                            }
                        }
                    }
                }
                if (nearestOrder < 0) {
                    AlarmConfig.setWatchStatus(
                        ctx,
                        "[$timeStr] 暂无开往" + AlarmConfig.getWatchStationName(ctx) + "的车（在路 $total 辆）"
                    )
                    return@Thread
                }
                val stopsAway = target - nearestOrder
                val etaText = if (nearestTravelSec > 0) {
                    "，约 " + Math.round(nearestTravelSec / 60.0) + " 分钟"
                } else {
                    ""
                }
                AlarmConfig.setWatchStatus(ctx, "[$timeStr] 最近一辆 $nearestBusId：还剩 $stopsAway 站$etaText")
                val lead = AlarmConfig.getWatchLead(ctx)
                if (stopsAway in 0..lead) {
                    val day = SimpleDateFormat("yyyyMMdd", Locale.CHINA).format(Date())
                    val marker = nearestBusId + "@" + day
                    if (AlarmConfig.getWatchFired(ctx) != marker && !AlarmPlayer.isRinging) {
                        AlarmConfig.setWatchFired(ctx, marker)
                        val lineNo = AlarmConfig.getWatchLineNo(ctx)
                        AlarmPlayer.start(ctx, lineNo + "路快到了，快出门！", lineNo + "路")
                        AlarmConfig.setWatchStatus(ctx, "[$timeStr] 已触发提醒：$nearestBusId 还剩 $stopsAway 站")
                    }
                }
            } catch (e: Exception) {
                AlarmConfig.setWatchStatus(ctx, "[$timeStr] 查询失败：" + (e.message ?: "网络异常"))
            }
        }.start()
    }

    companion object {
        private const val CHANNEL_ID = "watch_service"
        private const val NOTIF_ID = 2

        fun start(context: Context) {
            val intent = Intent(context, WatchService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, WatchService::class.java))
        }
    }
}

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED && AlarmConfig.isWatchEnabled(context)) {
            WatchService.start(context)
        }
    }
}
""",
    "app/src/main/java/com/erxi/cq141alarm/BusNotificationListener.kt": """package com.erxi.cq141alarm

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class BusNotificationListener : NotificationListenerService() {

    companion object {
        private val TARGET_PACKAGES = setOf(
            "com.chelaile.lite",       // 车来了
            "com.autonavi.minimap",    // 高德地图
            "com.baidu.BaiduMap"       // 百度地图
        )
        private const val COOLDOWN_MS = 3 * 60 * 1000L
        private var lastTriggerTime = 0L
    }

    override fun onListenerConnected() {
        super.onListenerConnected()
        val timeStr = SimpleDateFormat("HH:mm:ss", Locale.CHINA).format(Date())
        AlarmConfig.setListenerStatus(this, "已连接 · $timeStr")
    }

    override fun onListenerDisconnected() {
        super.onListenerDisconnected()
        val timeStr = SimpleDateFormat("HH:mm:ss", Locale.CHINA).format(Date())
        AlarmConfig.setListenerStatus(this, "已断开 · $timeStr")
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        sbn ?: return
        if (TARGET_PACKAGES.isNotEmpty() && sbn.packageName !in TARGET_PACKAGES) return

        val extras = sbn.notification.extras
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString().orEmpty()
        val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString().orEmpty()
        val bigText = extras.getCharSequence(Notification.EXTRA_BIG_TEXT)?.toString().orEmpty()
        val ticker = sbn.notification.tickerText?.toString().orEmpty()
        val content = listOf(title, text, bigText, ticker)
            .filter { it.isNotBlank() }
            .distinct()
            .joinToString(" ")
            .trim()

        val timeStr = SimpleDateFormat("HH:mm:ss", Locale.CHINA).format(Date())
        val appName = when (sbn.packageName) {
            "com.autonavi.minimap" -> "高德"
            "com.chelaile.lite" -> "车来了"
            else -> "百度"
        }

        if (content.isBlank()) {
            AlarmConfig.setLastLog(this, "[$timeStr] $appName 发了一条通知（无文字内容，未触发）")
            return
        }

        AlarmConfig.setLastLog(this, "[$timeStr] $appName：$content")

        val label: String = if (AlarmConfig.isAnyRoute(this)) {
            extractRouteLabel(content)
        } else {
            val keywords = AlarmConfig.getKeywordList(this)
            val matched = keywords.firstOrNull { content.contains(it, ignoreCase = true) } ?: return
            if (matched.endsWith("路")) matched else "${matched}路"
        }

        val now = System.currentTimeMillis()
        if (now - lastTriggerTime > COOLDOWN_MS) {
            lastTriggerTime = now
            AlarmPlayer.start(this, content, label)
        }
    }

    private fun extractRouteLabel(content: String): String {
        val numRoute = Regex("(\\\\d{1,4})\\\\s*路").find(content)
        if (numRoute != null) return "${numRoute.groupValues[1]}路"
        val namedLine = Regex("([A-Za-z]?\\\\d{1,4}线)").find(content)
        if (namedLine != null) return namedLine.groupValues[1]
        return "公交"
    }
}
"""
}


def main():
    for rel_path, content in FILES.items():
        target = PROJECT_DIR / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
