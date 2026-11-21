package com.parentalguardian.child.permissions

import android.Manifest
import android.app.AppOpsManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.PowerManager
import android.os.Process
import android.provider.Settings
import androidx.core.content.ContextCompat

object PermissionHelper {
    private fun has(ctx: Context, p: String) =
        ContextCompat.checkSelfPermission(ctx, p) == PackageManager.PERMISSION_GRANTED

    fun hasFineLocation(ctx: Context) = has(ctx, Manifest.permission.ACCESS_FINE_LOCATION)

    fun hasBackgroundLocation(ctx: Context) =
        Build.VERSION.SDK_INT < 29 || has(ctx, Manifest.permission.ACCESS_BACKGROUND_LOCATION)

    fun hasNotifications(ctx: Context) =
        Build.VERSION.SDK_INT < 33 || has(ctx, Manifest.permission.POST_NOTIFICATIONS)

    @Suppress("DEPRECATION")
    fun hasUsageAccess(ctx: Context): Boolean {
        val ops = ctx.getSystemService(AppOpsManager::class.java)
        val mode = ops.checkOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS, Process.myUid(), ctx.packageName)
        return mode == AppOpsManager.MODE_ALLOWED
    }

    fun ignoringBatteryOptimizations(ctx: Context) =
        ctx.getSystemService(PowerManager::class.java).isIgnoringBatteryOptimizations(ctx.packageName)

    fun openUsageAccessSettings(ctx: Context) =
        ctx.startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))

    fun openBatterySettings(ctx: Context) =
        ctx.startActivity(
            Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        )

    fun requiredGranted(ctx: Context) =
        hasFineLocation(ctx) && hasBackgroundLocation(ctx) && hasNotifications(ctx) && hasUsageAccess(ctx)
}
