package com.parentalguardian.child.data

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/** Stores the device token encrypted with a key held in the Android Keystore. */
class TokenStore(context: Context) {
    private val prefs = EncryptedSharedPreferences.create(
        context.applicationContext,
        "guardian_secure",
        MasterKey.Builder(context.applicationContext)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build(),
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    var token: String?
        get() = prefs.getString("device_token", null)
        set(v) {
            prefs.edit().apply { if (v == null) remove("device_token") else putString("device_token", v) }.apply()
        }

    var lastSyncMillis: Long
        get() = prefs.getLong("last_sync", 0L)
        set(v) { prefs.edit().putLong("last_sync", v).apply() }

    val isPaired: Boolean get() = token != null
}
