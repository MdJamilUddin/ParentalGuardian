package com.parentalguardian.parent

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import com.parentalguardian.parent.data.TokenStore
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
    val store = TokenStore(LocalContext.current)
    var token by remember { mutableStateOf(store.token) }
    var childId by remember { mutableStateOf<Int?>(null) }

    val logout = { store.token = null; token = null; childId = null }
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
