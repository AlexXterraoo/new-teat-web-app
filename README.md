# RailVPN — Custom VPN Management Panel for Railway

A lightweight, self-hosted **VLESS + WebSocket + TLS** VPN panel built specifically for Railway (and any Docker host).

## ✨ Features

- 🛡 **VLESS + WS + TLS** outbound proxy (Xray-core inside the container)
- 👥 **Multi-user** with per-user traffic quota (auto-disable when exceeded)
- 📊 **Live traffic dashboard** — uplink/downlink refresh every 15s
- 📋 **One-click copy** VLESS subscription links (v2rayNG / NekoBox / Clash)
- 🌐 **Persian (RTL) UI** with dark mode
- 🔐 **Cookie-session login** — set `ADMIN_PASSWORD` env to secure it
- 🪶 **Tiny image** (Alpine + Python 3.12 + Xray, ~80 MB)
- 💾 **State persists** in a Railway Volume mounted at `/app/state.json`

## 🚀 Deploy to Railway

1. **Fork / push this repo to your GitHub.**
2. On [railway.com](https://railway.com):
   - **New Project → Deploy from GitHub repo** → pick this repo
   - Railway auto-detects the `Dockerfile` and builds.
3. **Set environment variables** (Variables tab):

   | Variable | Default | Notes |
   |---|---|---|
   | `PORT` | `8080` | Required — Railway forwards HTTP to this port |
   | `ADMIN_PASSWORD` | `admin` | **Change this!** Your login password |
   | `RAILWAY_PUBLIC_DOMAIN` | auto | Used to build the VLESS subscription URL |

4. **Add a Volume** (Settings → Volumes):
   - Mount path: `/app`
   - This persists `state.json` across redeploys.

5. **Generate a public domain** (Settings → Networking → Generate Domain).
   Open `https://<your-app>.up.railway.app` → log in with your password.

6. **Create users** in the dashboard → copy the VLESS link → import into **v2rayNG**, **NekoBox**, **Hiddify**, etc.

## 📲 Client setup

Paste the copied `vless://...` link into:
- **Android**: v2rayNG, Hiddify, NekoBox
- **iOS**: Streisand, V2Box, Shadowrocket
- **Windows**: Nekoray, v2rayN
- **macOS**: V2Box, V2RayXS

All clients support the `vless://` URI scheme natively.

## ⚠️ Important notes

- Railway provides **HTTPS for free** on the generated domain — TLS is handled by Railway's edge.
- The VLESS inbound listens on `8080` internally; Railway's reverse proxy terminates TLS, then forwards to `ws://127.0.0.1:8080/railvpn`.
- The subscription link in the panel hardcodes `port 443 + security=tls + sni=<your-domain>` because that's what Railway exposes publicly.
- **Free Railway tier** ($5/mo credit) is enough for personal use with a handful of users.
- ⚠️ **Reading the room**: Railway's ToS discourages heavy/proxy workloads. Heavy commercial use may get the workspace restricted — see your workspace dashboard for alerts.

## 🛠 Local dev

```bash
pip install -r requirements.txt
uvicorn app:app --reload --port 8080
```

Open http://localhost:8080.

## 📁 File structure

```
railvpn/
├── app.py              # FastAPI app — routes, auth, Xray management
├── config.json         # Xray VLESS+WS inbound template
├── Dockerfile          # Alpine + Xray + Python deps
├── requirements.txt    # FastAPI, Jinja2, httpx
├── railway.toml        # Railway deploy config
├── templates/
│   ├── login.html      # RTL Persian login page
│   └── dashboard.html  # User management + traffic
└── static/
    └── style.css       # Dark-mode teal theme
```

## 📜 License

MIT
