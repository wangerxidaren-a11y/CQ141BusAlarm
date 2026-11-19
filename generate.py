from pathlib import Path

PROJECT_DIR = Path("CQ141BusAlarm")

FILES = {
    "README.md": """# 重庆 141 路强提醒助手（小米 17 / 安卓极简版）

## 功能说明
- 监听指定公交软件（车来了、高德地图、百度地图）的通知栏消息。
- 工作日早高峰（06:30–09:30）检测到包含关键词 `141` 时，自动：
  1. 强制将系统闹钟音量拉满；
  2. 通过系统闹钟通道（`USAGE_ALARM`，静音/勿扰也能响）连续语音播报“141路快到了，快出门！”（可切换为自定义 MP3）；
  3. 持续循环震动；
  4. 自动亮屏并弹出全屏大红关闭页面，无需解锁即可一键停止。
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
        versionCode = 2
        versionName = "1.1"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
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
    <string name="app_name">141路强提醒</string>
</resources>
""",
    "app/src/main/AndroidManifest.xml": """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.VIBRATE" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-permission android:name="android.permission.USE_FULL_SCREEN_INTENT" />

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
    "app/src/main/java/com/erxi/cq141alarm/MainActivity.kt": """package com.erxi.cq141alarm

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast

class MainActivity : Activity() {

    private val handler = Handler(Looper.getMainLooper())
    private var testRunnable: Runnable? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        requestPostNotificationsIfNeeded()

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(64, 64, 64, 64)
        }

        val info = TextView(this).apply {
            text = "重庆 141 路强提醒助手\\n生效时间：全天不限时"
            textSize = 18f
            gravity = Gravity.CENTER
            setPadding(0, 0, 0, 48)
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

                Toast.makeText(this@MainActivity, "5秒后触发，请立即按电源键锁屏测试", Toast.LENGTH_SHORT).show()
                isEnabled = false
                text = "倒计时 5 秒，请立即锁屏..."

                val task = Runnable {
                    AlarmPlayer.start(this@MainActivity, "【锁屏实测】重庆 141 路距您还有 2 站，请立即出门！")
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

        layout.addView(info)
        layout.addView(btnNotifyListener)
        layout.addView(btnFullScreenPerm)
        layout.addView(btnTest)
        layout.addView(btnStop)
        setContentView(layout)
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

        val busMsg = intent.getStringExtra("bus_msg") ?: "重庆 141 路快到了！"

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(Color.parseColor("#B71C1C"))
            setPadding(64, 64, 64, 64)
        }

        val title = TextView(this).apply {
            text = "🚌 141 路快到了！"
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
        TTS_VOICE,   // 连续语音播报
        CUSTOM_MP3   // 循环播放 res/raw/bus_alarm.mp3
    }

    // 切换提醒方式：TTS_VOICE（语音喊话）或 CUSTOM_MP3（自定义音频）
    private val MODE = AlertMode.TTS_VOICE
    private const val SPEECH_TEXT = "141路快到了，快出门！"

    private const val CHANNEL_ID = "bus_141_alarm_channel"
    private const val NOTIF_ID = 14101

    private val mainHandler = Handler(Looper.getMainLooper())
    private var mediaPlayer: MediaPlayer? = null
    private var tts: TextToSpeech? = null
    private var vibrator: Vibrator? = null

    @Volatile var isRinging: Boolean = false
        private set

    fun start(context: Context, message: String = "重庆 141 路即将到站") {
        if (isRinging) return
        isRinging = true

        val appCtx = context.applicationContext

        // 1. 拉满系统闹钟音量
        val audioManager = appCtx.getSystemService(Context.AUDIO_SERVICE) as AudioManager
        val maxAlarmVol = audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM)
        audioManager.setStreamVolume(AudioManager.STREAM_ALARM, maxAlarmVol, 0)

        // 2. 按所选模式播放声音
        when (MODE) {
            AlertMode.TTS_VOICE -> startTtsLoop(appCtx)
            AlertMode.CUSTOM_MP3 -> startMp3Loop(appCtx)
        }

        // 3. 持续循环震动
        vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            (appCtx.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager).defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            appCtx.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        }
        vibrator?.vibrate(VibrationEffect.createWaveform(longArrayOf(0, 800, 300), 0))

        // 4. 弹出锁屏全屏提醒界面
        showFullScreenAlarm(appCtx, message)
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
                                        tts?.speak(SPEECH_TEXT, TextToSpeech.QUEUE_FLUSH, params, "bus_141")
                                    }
                                }, 600L)
                            }
                        }
                    })
                    speak(SPEECH_TEXT, TextToSpeech.QUEUE_FLUSH, params, "bus_141")
                }
            } else if (isRinging) {
                startMp3Loop(appCtx)
            }
        }
    }

    private fun showFullScreenAlarm(context: Context, message: String) {
        val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        val channel = NotificationChannel(
            CHANNEL_ID,
            "141路强提醒闹钟",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            lockscreenVisibility = Notification.VISIBILITY_PUBLIC
            setSound(null, null)
        }
        nm.createNotificationChannel(channel)

        val fullScreenIntent = Intent(context, AlarmAlertActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_NO_USER_ACTION
            putExtra("bus_msg", message)
        }
        val fullScreenPendingIntent = PendingIntent.getActivity(
            context,
            0,
            fullScreenIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = Notification.Builder(context, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setContentTitle("🚌 重庆 141 路快到了")
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
    "app/src/main/java/com/erxi/cq141alarm/BusNotificationListener.kt": """package com.erxi.cq141alarm

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification

class BusNotificationListener : NotificationListenerService() {

    companion object {
        private val TARGET_PACKAGES = setOf(
            "com.chelaile.lite",       // 车来了
            "com.autonavi.minimap",    // 高德地图
            "com.baidu.BaiduMap"       // 百度地图
        )
        private const val KEYWORD = "141"
        private const val COOLDOWN_MS = 3 * 60 * 1000L
        private var lastTriggerTime = 0L
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        sbn ?: return
        if (TARGET_PACKAGES.isNotEmpty() && sbn.packageName !in TARGET_PACKAGES) return

        val extras = sbn.notification.extras
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString().orEmpty()
        val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString().orEmpty()
        val bigText = extras.getCharSequence(Notification.EXTRA_BIG_TEXT)?.toString().orEmpty()
        val content = "$title $text $bigText".trim()

        val now = System.currentTimeMillis()
        if (content.contains(KEYWORD) && (now - lastTriggerTime > COOLDOWN_MS)) {
            lastTriggerTime = now
            AlarmPlayer.start(this, content)
        }
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
