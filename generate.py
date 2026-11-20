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
        versionCode = 7
        versionName = "1.6"
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
    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />

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
            text = "公交强提醒助手（v1.6）\\n全天不限时 · 自由监听任意线路"
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

        val btnOverlayPerm = Button(this).apply {
            text = "3. 开启悬浮窗权限（亮屏玩手机时全屏霸屏）"
            setOnClickListener {
                val intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION).apply {
                    data = Uri.parse("package:$packageName")
                }
                startActivity(intent)
            }
        }

        val btnTest = Button(this).apply {
            text = "4. 5秒后测试（点完请立即锁屏）"
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
                    text = "4. 5秒后测试（点完请立即锁屏）"
                }
                testRunnable = task
                handler.postDelayed(task, 5000L)
            }
        }

        val btnStop = Button(this).apply {
            text = "5. 我出门了（停止响铃 / 取消测试）"
            setOnClickListener {
                testRunnable?.let { handler.removeCallbacks(it) }
                btnTest.isEnabled = true
                btnTest.text = "4. 5秒后测试（点完请立即锁屏）"
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
        layout.addView(btnOverlayPerm)
        layout.addView(btnTest)
        layout.addView(btnStop)
        layout.addView(statusView)
        layout.addView(logView)
        scroll.addView(layout)
        setContentView(scroll)
    }

    override fun onResume() {
        super.onResume()
        statusView.text = "监听状态：${AlarmConfig.getListenerStatus(this)}"
        logView.text = "最近捕获的通知：\\n${AlarmConfig.getLastLog(this)}"
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
import android.graphics.Color
import android.graphics.PixelFormat
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
import android.provider.Settings
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
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
    private var overlayView: View? = null
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
        showOverlay(appCtx, message, routeLabel)
    }

    private fun showOverlay(appCtx: Context, message: String, routeLabel: String) {
        if (!Settings.canDrawOverlays(appCtx)) return
        mainHandler.post {
            if (!isRinging || overlayView != null) return@post
            try {
                val wm = appCtx.getSystemService(Context.WINDOW_SERVICE) as WindowManager

                val root = LinearLayout(appCtx).apply {
                    orientation = LinearLayout.VERTICAL
                    gravity = Gravity.CENTER
                    setBackgroundColor(Color.parseColor("#B71C1C"))
                    setPadding(64, 64, 64, 64)
                }

                val title = TextView(appCtx).apply {
                    text = "🚌 ${routeLabel}快到了！"
                    textSize = 32f
                    setTextColor(Color.WHITE)
                    gravity = Gravity.CENTER
                }

                val detail = TextView(appCtx).apply {
                    text = message
                    textSize = 18f
                    setTextColor(Color.parseColor("#FFCDD2"))
                    gravity = Gravity.CENTER
                    setPadding(0, 24, 0, 96)
                }

                val stopBtn = Button(appCtx).apply {
                    text = "我出门了 · 停止响铃"
                    textSize = 22f
                    setTextColor(Color.parseColor("#B71C1C"))
                    setBackgroundColor(Color.WHITE)
                    setPadding(64, 48, 64, 48)
                    setOnClickListener { stop(appCtx) }
                }

                root.addView(title)
                root.addView(detail)
                root.addView(stopBtn)

                val params = WindowManager.LayoutParams(
                    WindowManager.LayoutParams.MATCH_PARENT,
                    WindowManager.LayoutParams.MATCH_PARENT,
                    WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                        WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON,
                    PixelFormat.TRANSLUCENT
                )
                wm.addView(root, params)
                overlayView = root
            } catch (e: Exception) {
                // 悬浮窗失败就靠全屏通知兜底，不让异常打断响铃
            }
        }
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
        val capturedOverlay = overlayView
        overlayView = null
        mainHandler.removeCallbacksAndMessages(null)
        if (capturedOverlay != null) {
            mainHandler.post {
                try {
                    val wm = capturedOverlay.context
                        .getSystemService(Context.WINDOW_SERVICE) as WindowManager
                    wm.removeView(capturedOverlay)
                } catch (e: Exception) {
                }
            }
        }

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
