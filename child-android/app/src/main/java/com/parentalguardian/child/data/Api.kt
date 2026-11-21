package com.parentalguardian.child.data

import com.parentalguardian.child.BuildConfig
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

object Api {
    class ApiError(val code: Int, message: String) : Exception(message)

    private fun post(path: String, body: JSONObject, token: String?): JSONObject {
        val conn = (URL(BuildConfig.BASE_URL + path).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 15_000
            readTimeout = 30_000
            doOutput = true
            setRequestProperty("Content-Type", "application/json")
            if (token != null) setRequestProperty("Authorization", "Bearer $token")
        }
        try {
            conn.outputStream.use { it.write(body.toString().toByteArray()) }
            val code = conn.responseCode
            val stream = if (code in 200..299) conn.inputStream else conn.errorStream
            val text = stream?.bufferedReader()?.readText().orEmpty()
            if (code !in 200..299) throw ApiError(code, text)
            return JSONObject(text)
        } finally {
            conn.disconnect()
        }
    }

    /** Redeems the pairing code and returns the device token. */
    fun pair(code: String, deviceName: String): String =
        post("/device/pair", JSONObject().put("code", code).put("device_name", deviceName), null)
            .getString("device_token")

    fun sync(token: String, payload: JSONObject) {
        post("/device/sync", payload, token)
    }
}
