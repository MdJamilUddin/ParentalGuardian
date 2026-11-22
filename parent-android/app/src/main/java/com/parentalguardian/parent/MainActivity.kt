package com.parentalguardian.parent

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.ContextCompat
import com.parentalguardian.parent.data.TokenStore
import com.parentalguardian.parent.push.PushRegistrar
import com.parentalguardian.parent.ui.AuthScreen
import com.parentalguardian.parent.ui.ChildDetailScreen
import com.parentalguardian.parent.ui.ChildrenScreen

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MaterialTheme { Surface { App() } } }
    }
}

@Composable
private fun App() {
    val ctx = LocalContext.current
    val store = TokenStore(ctx)
    var token by remember { mutableStateOf(store.token) }
    // tapping a notification opens that child directly
    var childId by remember { mutableStateOf((ctx as? Activity)?.intent?.getStringExtra("child_id")?.toIntOrNull()) }

    val notifPermission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { }
    LaunchedEffect(token) {
        val t = token ?: return@LaunchedEffect
        if (Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(ctx, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) notifPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
        PushRegistrar.register(ctx, t)
    }

    val logout = {
        token?.let { PushRegistrar.unregister(ctx, it) }
        store.token = null; token = null; childId = null
    }
    val t = token
    when {
        t == null -> AuthScreen { store.token = it; token = it }
        childId == null -> ChildrenScreen(t, onOpen = { childId = it }, onLogout = logout)
        else -> {
            BackHandler { childId = null }
            ChildDetailScreen(t, childId!!, onBack = { childId = null }, onLogout = logout)
        }
    }
}
