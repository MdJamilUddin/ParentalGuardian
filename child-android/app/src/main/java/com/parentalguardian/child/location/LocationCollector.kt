package com.parentalguardian.child.location

import android.annotation.SuppressLint
import android.content.Context
import android.os.Looper
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.parentalguardian.child.data.PendingStore
import com.parentalguardian.child.permissions.PermissionHelper
import org.json.JSONObject
import java.time.Instant

/** Battery-friendly: balanced accuracy, one update every ~5 minutes or 50 m of movement. */
object LocationCollector {
    private var callback: LocationCallback? = null

    @SuppressLint("MissingPermission")
    fun start(ctx: Context) {
        if (callback != null || !PermissionHelper.hasFineLocation(ctx)) return
        val app = ctx.applicationContext
        val pending = PendingStore(app)
        val request = LocationRequest.Builder(Priority.PRIORITY_BALANCED_POWER_ACCURACY, 5 * 60_000L)
            .setMinUpdateDistanceMeters(50f).build()
        callback = object : LocationCallback() {
            override fun onLocationResult(result: LocationResult) {
                result.locations.forEach {
                    pending.append(
                        JSONObject().put("t", "loc").put("lat", it.latitude).put("lng", it.longitude)
                            .put("accuracy_m", it.accuracy.toDouble())
                            .put("recorded_at", Instant.ofEpochMilli(it.time).toString())
                    )
                }
            }
        }
        LocationServices.getFusedLocationProviderClient(app)
            .requestLocationUpdates(request, callback!!, Looper.getMainLooper())
    }

    fun stop(ctx: Context) {
        callback?.let { LocationServices.getFusedLocationProviderClient(ctx.applicationContext).removeLocationUpdates(it) }
        callback = null
    }
}
