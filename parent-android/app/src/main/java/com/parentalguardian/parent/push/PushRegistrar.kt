package com.parentalguardian.parent.push

import android.content.Context
import com.google.firebase.FirebaseApp
import com.google.firebase.messaging.FirebaseMessaging
import com.parentalguardian.parent.data.Api

/** Tells the server which phone should receive this parent's alerts. Does nothing if Firebase isn't set up. */
object PushRegistrar {
    private fun available(ctx: Context) = FirebaseApp.getApps(ctx).isNotEmpty()

    fun register(ctx: Context, jwt: String) {
        if (!available(ctx)) return
        FirebaseMessaging.getInstance().token.addOnSuccessListener { fcm ->
            Thread { runCatching { Api.registerPushToken(jwt, fcm) } }.start()
        }
    }

    /** Call on log out so the next person to log in on this phone doesn't inherit these alerts. */
    fun unregister(ctx: Context, jwt: String) {
        if (!available(ctx)) return
        val fm = FirebaseMessaging.getInstance()
        fm.token.addOnSuccessListener { fcm ->
            Thread {
                runCatching { Api.unregisterPushToken(jwt, fcm) }
                fm.deleteToken()
            }.start()
        }
    }
}
