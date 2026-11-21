package com.parentalguardian.parent.ui

import android.graphics.Color
import android.view.MotionEvent
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import com.parentalguardian.parent.data.Loc
import org.osmdroid.config.Configuration
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Marker
import org.osmdroid.views.overlay.Polyline
import java.io.File

/** OpenStreetMap view: path of the last 24 h plus a marker at the latest position. */
@Composable
fun LocationMap(history: List<Loc>, latest: Loc, modifier: Modifier = Modifier) {
    val ctx = LocalContext.current
    val state = remember { booleanArrayOf(false) } // [0] = already centred once
    val map = remember {
        Configuration.getInstance().apply {
            load(ctx, ctx.getSharedPreferences("osmdroid", 0))
            userAgentValue = ctx.packageName
            osmdroidBasePath = File(ctx.cacheDir, "osm")
            osmdroidTileCache = File(ctx.cacheDir, "osm/tiles")
        }
        MapView(ctx).apply {
            setTileSource(TileSourceFactory.MAPNIK)
            setMultiTouchControls(true)
            controller.setZoom(16.0)
            // let the map handle drags inside a scrolling page
            setOnTouchListener { v, e ->
                when (e.action) {
                    MotionEvent.ACTION_DOWN -> v.parent.requestDisallowInterceptTouchEvent(true)
                    MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> v.parent.requestDisallowInterceptTouchEvent(false)
                }
                false
            }
        }
    }
    DisposableEffect(Unit) {
        map.onResume()
        onDispose { map.onPause(); map.onDetach() }
    }
    AndroidView(factory = { map }, modifier = modifier, update = { m ->
        m.overlays.clear()
        val here = GeoPoint(latest.lat, latest.lng)
        if (history.size > 1) {
            m.overlays.add(Polyline().apply {
                setPoints(history.map { GeoPoint(it.lat, it.lng) })
                outlinePaint.color = Color.parseColor("#1E6FD9")
                outlinePaint.strokeWidth = 8f
            })
        }
        m.overlays.add(Marker(m).apply {
            position = here
            setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM)
            title = "Last known location"
        })
        if (!state[0]) { m.controller.setCenter(here); state[0] = true }
        m.invalidate()
    })
}
