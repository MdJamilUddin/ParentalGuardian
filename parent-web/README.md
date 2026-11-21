# Parent web dashboard

Plain HTML/JS, no build step: `dashboard/index.html`.

1. Set your backend address in `dashboard/config.js`.
2. Run the backend, then serve this folder, for example:
       cd parent-web/dashboard && python3 -m http.server 5173
   and open http://localhost:5173
3. The backend must allow the dashboard's address in `CORS_ORIGINS` (http://localhost:5173 is allowed by default).

Same features as the parent app: login, children, pairing codes, last 24 h map (OpenStreetMap),
battery, today's app usage, disconnect a phone. Refreshes every minute.

Security notes: the dashboard must be served over HTTPS in production (see `deployment/`). Names coming from the
child's phone are inserted as text, never HTML. The login token lasts `ACCESS_TOKEN_MINUTES` on the backend.
