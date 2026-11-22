package com.parentalguardian.parent

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager

class GuardianApp : Application() {
    override fun onCreate() {
        super.onCreate()
        val channel = NotificationChannel("alerts", "Alerts", NotificationManager.IMPORTANCE_HIGH).apply {
            description = "Phone offline and low battery alerts"
        }
        getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }
}
