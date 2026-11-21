# Parent Android app (Kotlin, Jetpack Compose)

Open the `parent-android` folder in Android Studio (Koala or newer). Requires Android 8.0+.

Set `BASE_URL` in `app/build.gradle.kts` (debug: `http://10.0.2.2:8000` for the emulator; release: your HTTPS URL).

## Screens
- Login / create account
- My children: add a child, see how many phones are connected
- Child detail (refreshes every minute): battery, map with the last 24 h path (OpenStreetMap),
  today's app usage, connected phones (disconnect), and "Add a phone" which shows a 6-digit pairing code

## Notes
- Login tokens last `ACCESS_TOKEN_MINUTES` (backend, default 60). When one expires the app returns to the login
  screen. For a smoother experience set `ACCESS_TOKEN_MINUTES=1440` (1 day) or add refresh tokens later.
- Map tiles come from openstreetmap.org, fine for development and small use. For a public release use a tile
  provider with a proper plan (MapTiler, Stadia, etc.) or switch to Google Maps with your own API key.
- Times are shown in the phone's local time; the server stores UTC.
