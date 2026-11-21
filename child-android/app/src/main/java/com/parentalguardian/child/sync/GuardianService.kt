package com.parentalguardian.child.sync

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import com.parentalguardian.child.location.LocationCollector

/** Foreground service. The notification is always visible: the child can see monitoring is active. */
class GuardianService : Service() {
    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(
            NotificationChannel("guardian", "Parental Guardian", NotificationManager.IMPORTANCE_LOW)
        )
        val notification = Notification.Builder(this, "guardian")
            .setContentTitle("Parental Guardian is active")
            .setContentText("Your parent can see this phone's location, app usage and battery level.")
            .setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setOngoing(true)
            .build()
        if (Build.VERSION.SDK_INT >= 29) {
            startForeground(1, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION)
        } else {
            startForeground(1, notification)
        }
        LocationCollector.start(this)
        SyncScheduler.schedule(this)
        SyncScheduler.syncNow(this)
        return START_STICKY
    }

    override fun onDestroy() {
        LocationCollector.stop(this)
        super.onDestroy()
    }
}
