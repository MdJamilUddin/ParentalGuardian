package com.parentalguardian.parent.data

import com.parentalguardian.parent.BuildConfig
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

data class Device(val id: Int, val name: String, val revoked: Boolean, val lastSeen: String?)
data class Child(val id: Int, val name: String, val devices: List<Device>)
data class Loc(val lat: Double, val lng: Double, val accuracy: Double?, val at: String)
data class UsageItem(val pkg: String, val label: String?, val seconds: Int)
data class Battery(val level: Int, val charging: Boolean, val at: String)
data class PairingCode(val code: String, val expiresAt: String)
data class NotifPrefs(val offline: Boolean, val lowBattery: Boolean, val devices: Int)
data class PushTestResult(val sent: Int, val registered: Int, val configured: Boolean)

object Api {
    class ApiError(val code: Int, message: String) : Exception(message)

    private fun call(method: String, path: String, body: JSONObject?, token: String?): String {
        val conn = (URL(BuildConfig.BASE_URL + path).openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 15_000
            readTimeout = 30_000
            setRequestProperty("Accept", "application/json")
            if (token != null) setRequestProperty("Authorization", "Bearer $token")
            if (body != null) {
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
        }
        try {
            if (body != null) conn.outputStream.use { it.write(body.toString().toByteArray()) }
            val code = conn.responseCode
            val stream = if (code in 200..299) conn.inputStream else conn.errorStream
            val text = stream?.bufferedReader()?.readText().orEmpty()
            if (code !in 200..299) throw ApiError(code, text)
            return text.trim()
        } finally {
            conn.disconnect()
        }
    }

    private fun JSONObject.optStr(k: String): String? = if (isNull(k)) null else getString(k)
    private fun JSONObject.optDbl(k: String): Double? = if (isNull(k)) null else getDouble(k)

    fun login(email: String, password: String): String =
        JSONObject(call("POST", "/auth/login", JSONObject().put("email", email).put("password", password), null))
            .getString("access_token")

    fun register(email: String, name: String, password: String): String =
        JSONObject(
            call("POST", "/auth/register",
                JSONObject().put("email", email).put("name", name).put("password", password), null)
        ).getString("access_token")

    fun children(token: String): List<Child> {
        val arr = JSONArray(call("GET", "/children", null, token))
        return (0 until arr.length()).map { i ->
            val c = arr.getJSONObject(i)
            val ds = c.getJSONArray("devices")
            Child(c.getInt("id"), c.getString("name"), (0 until ds.length()).map { j ->
                val d = ds.getJSONObject(j)
                Device(d.getInt("id"), d.getString("name"), d.getBoolean("revoked"), d.optStr("last_seen"))
            })
        }
    }

    fun addChild(token: String, name: String) {
        call("POST", "/children", JSONObject().put("name", name), token)
    }

    fun pairingCode(token: String, childId: Int): PairingCode {
        val o = JSONObject(call("POST", "/children/$childId/pairing-code", null, token))
        return PairingCode(o.getString("code"), o.getString("expires_at"))
    }

    fun revokeDevice(token: String, deviceId: Int) {
        call("DELETE", "/devices/$deviceId", null, token)
    }

    private fun parseLoc(o: JSONObject) = Loc(o.getDouble("lat"), o.getDouble("lng"), o.optDbl("accuracy_m"), o.getString("recorded_at"))

    fun latestLocation(token: String, childId: Int): Loc? {
        val t = call("GET", "/children/$childId/location/latest", null, token)
        return if (t.isEmpty() || t == "null") null else parseLoc(JSONObject(t))
    }

    /** Oldest first, ready to draw as a path. */
    fun locations(token: String, childId: Int, hours: Int = 24): List<Loc> {
        val arr = JSONArray(call("GET", "/children/$childId/locations?hours=$hours", null, token))
        return (0 until arr.length()).map { parseLoc(arr.getJSONObject(it)) }.reversed()
    }

    fun usage(token: String, childId: Int, day: String): List<UsageItem> {
        val arr = JSONArray(call("GET", "/children/$childId/usage?day=$day", null, token))
        return (0 until arr.length()).map {
            val o = arr.getJSONObject(it)
            UsageItem(o.getString("package"), o.optStr("app_label"), o.getInt("seconds"))
        }
    }

    fun battery(token: String, childId: Int): Battery? {
        val t = call("GET", "/children/$childId/battery", null, token)
        if (t.isEmpty() || t == "null") return null
        val o = JSONObject(t)
        return Battery(o.getInt("level"), o.getBoolean("charging"), o.getString("recorded_at"))
    }

    // ---- push notifications
    fun registerPushToken(token: String, fcmToken: String) {
        call("PUT", "/me/push-token", JSONObject().put("token", fcmToken).put("platform", "android"), token)
    }

    fun unregisterPushToken(token: String, fcmToken: String) {
        call("POST", "/me/push-token/unregister", JSONObject().put("token", fcmToken), token)
    }

    private fun prefs(o: JSONObject) = NotifPrefs(o.getBoolean("offline"), o.getBoolean("low_battery"), o.getInt("devices"))

    fun notifPrefs(token: String): NotifPrefs = prefs(JSONObject(call("GET", "/me/notifications", null, token)))

    fun setNotifPrefs(token: String, offline: Boolean, lowBattery: Boolean): NotifPrefs =
        prefs(JSONObject(call("PUT", "/me/notifications",
            JSONObject().put("offline", offline).put("low_battery", lowBattery), token)))

    fun pushTest(token: String): PushTestResult {
        val o = JSONObject(call("POST", "/me/push-test", null, token))
        return PushTestResult(o.getInt("sent"), o.getInt("registered"), o.getBoolean("configured"))
    }
}
