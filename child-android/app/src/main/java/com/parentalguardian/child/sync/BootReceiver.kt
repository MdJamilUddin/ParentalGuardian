package com.parentalguardian.child.sync

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.core.content.ContextCompat
import com.parentalguardian.child.data.TokenStore
import com.parentalguardian.child.permissions.PermissionHelper

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(ctx: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED &&
            TokenStore(ctx).isPaired && PermissionHelper.requiredGranted(ctx)
        ) {
            ContextCompat.startForegroundService(ctx, Intent(ctx, GuardianService::class.java))
        }
    }
}
