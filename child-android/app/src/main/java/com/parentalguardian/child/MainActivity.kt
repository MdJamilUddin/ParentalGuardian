package com.parentalguardian.child

import android.Manifest
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.parentalguardian.child.data.Api
import com.parentalguardian.child.data.TokenStore
import com.parentalguardian.child.permissions.PermissionHelper as P
import com.parentalguardian.child.sync.GuardianService
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.DateFormat
import java.util.Date

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MaterialTheme { Surface { Screen() } } }
    }
}

@Composable
private fun Screen() {
    val ctx: Context = LocalContext.current
    val activity = ctx as ComponentActivity
    val store = remember { TokenStore(ctx) }
    val scope = rememberCoroutineScope()
    var tick by remember { mutableIntStateOf(0) }

    DisposableEffect(Unit) {
        val obs = LifecycleEventObserver { _, e -> if (e == Lifecycle.Event.ON_RESUME) tick++ }
        activity.lifecycle.addObserver(obs)
        onDispose { activity.lifecycle.removeObserver(obs) }
    }

    val paired = remember(tick) { store.isPaired }
    val ready = remember(tick) { P.requiredGranted(ctx) }

    val basicLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { tick++ }
    val bgLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { tick++ }

    LaunchedEffect(tick, paired, ready) {
        if (paired && ready) ContextCompat.startForegroundService(ctx, Intent(ctx, GuardianService::class.java))
    }

    var code by remember { mutableStateOf("") }
    var deviceName by remember { mutableStateOf(Build.MODEL ?: "Child phone") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp).statusBarsPadding(),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        Text("Parental Guardian", style = MaterialTheme.typography.headlineMedium)
        Card {
            Text(
                "This app shares this phone's location, how long apps are used, and the battery level " +
                    "with your parent. A notification stays visible while it is active.",
                Modifier.padding(14.dp)
            )
        }

        if (!paired) {
            Text("Ask your parent for a 6-digit pairing code from their app, then enter it here.")
            OutlinedTextField(
                code, { code = it.filter(Char::isDigit).take(6) }, label = { Text("Pairing code") },
                singleLine = true, modifier = Modifier.fillMaxWidth()
            )
            OutlinedTextField(
                deviceName, { deviceName = it }, label = { Text("Device name") },
                singleLine = true, modifier = Modifier.fillMaxWidth()
            )
            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            Button(
                enabled = code.length == 6 && deviceName.isNotBlank() && !busy,
                onClick = {
                    scope.launch {
                        busy = true; error = null
                        try {
                            val t = withContext(Dispatchers.IO) { Api.pair(code, deviceName.trim()) }
                            store.token = t
                            tick++
                        } catch (e: Api.ApiError) {
                            error = if (e.code == 429) "Too many attempts. Wait a few minutes." else "That code is invalid or expired."
                        } catch (e: Exception) {
                            error = "Can't reach the server. Check your internet connection."
                        }
                        busy = false
                    }
                }
            ) { Text(if (busy) "Pairing..." else "Pair this phone") }
        } else {
            Text("Paired. Allow the following so everything works:", style = MaterialTheme.typography.titleMedium)

            PermRow("Location", P.hasFineLocation(ctx)) {
                val perms = mutableListOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION)
                if (Build.VERSION.SDK_INT >= 33) perms += Manifest.permission.POST_NOTIFICATIONS
                basicLauncher.launch(perms.toTypedArray())
            }
            PermRow("Location \"Allow all the time\"", P.hasBackgroundLocation(ctx), enabled = P.hasFineLocation(ctx)) {
                bgLauncher.launch(Manifest.permission.ACCESS_BACKGROUND_LOCATION)
            }
            PermRow("Notifications", P.hasNotifications(ctx)) {
                basicLauncher.launch(arrayOf(Manifest.permission.POST_NOTIFICATIONS))
            }
            PermRow("Usage access", P.hasUsageAccess(ctx)) { P.openUsageAccessSettings(ctx) }
            PermRow("Unrestricted battery (recommended)", P.ignoringBatteryOptimizations(ctx)) { P.openBatterySettings(ctx) }

            if (ready) {
                val last = store.lastSyncMillis
                Text(
                    "Protection is on. Last sync: " +
                        if (last == 0L) "waiting for first sync" else DateFormat.getDateTimeInstance().format(Date(last))
                )
            }
        }
    }
}

@Composable
private fun PermRow(label: String, granted: Boolean, enabled: Boolean = true, onGrant: () -> Unit) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Text((if (granted) "✔ " else "○ ") + label, Modifier.weight(1f))
        if (!granted) Button(onClick = onGrant, enabled = enabled) { Text("Allow") }
    }
}
