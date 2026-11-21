# Child Android app (Kotlin, Jetpack Compose)

Open the `child-android` folder in Android Studio (Koala or newer); it creates the Gradle wrapper and syncs.
Requires Android 8.0+ (minSdk 26).

## Point it at your server
`app/build.gradle.kts` -> `BASE_URL`
- debug: `http://10.0.2.2:8000` (emulator -> your computer). On a real phone use your computer's LAN IP; you must also
  add that IP to `res/xml/network_security_config.xml` for cleartext, or use HTTPS.
- release: your HTTPS URL.

## What it does
- `data/` token (Keystore-encrypted), HTTP client, offline queue
- `permissions/` location, background location, notifications, usage access, battery
- `location/` fused location every ~5 min or 50 m
- `battery/` level + charging; `usage/` today's foreground time per app
- `sync/` foreground service with a permanent notification, WorkManager upload every 15 min,
  boot receiver. If the parent revokes the device the server returns 401 and the app returns to the pairing screen.

## Notes
- Permissions must be granted by the child/parent on the phone; Android does not allow silently enabling them.
- Usage "day" is the phone's local date. Use the same local date when the dashboards ask for usage.
- Google Play: keep the app disclosed and visible (it is), and describe location/usage collection in the
  Data safety form and the background-location declaration.
- Some phone brands (Xiaomi, Oppo, Vivo, Samsung) kill background apps; set battery to "Unrestricted"
  and enable autostart for reliable syncing.
