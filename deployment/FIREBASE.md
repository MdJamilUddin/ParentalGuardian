# Push notifications with Firebase (free)

What you get: the parent app receives a notification when
- a child's phone has not reported for 2 hours (once per outage), or
- its battery is 15% or lower and not charging (once per low period).

Each parent can switch the two alert types on or off (Alerts button in the parent app) and send a test notification.
Settings on the server: `STALE_AFTER_MINUTES` (120), `LOW_BATTERY_PERCENT` (15), `LOW_BATTERY_RESET_PERCENT` (30).

## 1. Create the Firebase project
1. Go to console.firebase.google.com, sign in with a Google account, **Create a project** (name it `ParentalGuardian`;
   Google Analytics can be off).
2. In the project, **Add app**, choose **Android**. Package name: `com.parentalguardian.parent`. Register it.
3. Download **google-services.json** and put it in `parent-android/app/` (next to `build.gradle.kts`).
   It is listed in `.gitignore`, so it stays on your computer. Without this file the app still builds, just without push.

## 2. Give the server permission to send
1. Firebase console, the gear icon, **Project settings**, **Service accounts**, **Generate new private key**.
   A JSON file downloads. **This is a secret** (never commit it or share it).
2. Convert it to one line (PowerShell, in the folder with the file; use your file name):

       [Convert]::ToBase64String([IO.File]::ReadAllBytes("your-key-file.json"))

3. In Render, backend service, **Environment**, add:
   - `FIREBASE_CREDENTIALS_JSON` = the long text from the previous step
   - `CRON_SECRET` = a random value (`py -c "import secrets;print(secrets.token_hex(24))"`)
   Save; Render redeploys.
   (On your own server: put the same two values in `deployment/.env` and add them to the backend `environment:` in the compose file.)

## 3. Test it
1. Update the project (new backend and app files), push to GitHub, let Render redeploy.
2. Run the parent app (`staging` variant), log in, allow notifications when Android asks.
3. Tap **Alerts**, then **Send a test notification**. A notification should appear within seconds.
   The dialog tells you what's wrong if not ("Push isn't set up on the server yet", "This phone isn't registered", ...).
4. Real alert tests: pair a child phone, turn it off or enable airplane mode for over 2 hours (or temporarily set
   `STALE_AFTER_MINUTES=5` on the server) and wait for the next check; on the child phone let the battery drop below 15%.

## 4. Make sure the checks run
The server checks for silent phones every 5 minutes while it is running (`ALERT_CHECK_SECONDS`). On a free
hosting plan that sleeps when idle, a sleeping server checks nothing. Use a free external scheduler (for example
cron-job.org) to call this every 5 minutes, which also wakes the server:

    POST https://YOUR-SERVICE.onrender.com/internal/check-alerts
    Header:  X-Cron-Secret: <your CRON_SECRET>

Low-battery alerts don't need this, they are sent right when the phone reports. On a paid always-on server or your own
VPS the built-in checker is enough.

## Troubleshooting
| Symptom | Check |
|---|---|
| "Push isn't set up on the server yet" | `FIREBASE_CREDENTIALS_JSON` missing or invalid; backend logs say "Firebase credentials are invalid" |
| "This phone isn't registered" | `google-services.json` missing before the build, notification permission denied, or not logged in |
| Test works, real alerts don't | child phone data (check the dashboard), `STALE_AFTER_MINUTES`, the scheduler above, the Alerts switches |
| Nothing shows while the app is open | Notification permission (Android 13+), the app's "Alerts" channel not muted |

Not included yet: alerts for entering or leaving places (geofences), push in the web dashboard, notification history.
