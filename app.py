from __future__ import annotations

import json
import os
import secrets
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

APP_DIR = Path(__file__).parent
CONFIG_PATH = Path(os.getenv("XRAY_CONFIG", "/etc/xray/config.json"))
STATE_PATH = APP_DIR / "state.json"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
PANEL_PASSWORD = os.getenv("PANEL_PASSWORD", "")
SESSION_COOKIE = "railvpn_session"
SESSION_TOKEN = os.getenv("SESSION_TOKEN", secrets.token_urlsafe(32))
XRAY_API = "http://127.0.0.1:10085"

app = FastAPI(title="RailVPN", version="1.0")
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


def load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except Exception:
            pass
    return {"users": {}, "created_at": datetime.now(timezone.utc).isoformat()}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def reload_xray() -> None:
    try:
        subprocess.run(
            ["pkill", "-HUP", "xray"],
            capture_output=True,
            timeout=5,
        )
    except Exception:
        pass


def update_xray_config(state: dict[str, Any]) -> None:
    if not CONFIG_PATH.exists():
        return
    try:
        cfg = json.loads(CONFIG_PATH.read_text())
    except Exception:
        return
    clients = []
    for user_id, info in state.get("users", {}).items():
        if not info.get("disabled", False):
            clients.append({
                "id": user_id,
                "email": info.get("name", user_id[:8]),
                "flow": "",
            })
    for inbound in cfg.get("inbounds", []):
        if inbound.get("tag") == "vless-in":
            inbound["settings"]["clients"] = clients
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
    reload_xray()


def require_login(request: Request) -> bool:
    token = request.cookies.get(SESSION_COOKIE)
    return token == SESSION_TOKEN


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if not require_login(request):
        return RedirectResponse(url="/login", status_code=302)
    state = load_state()
    domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", request.headers.get("host", "your-domain.up.railway.app"))
    
    used_gb = 0.0
    total_gb = 100.0
    percent = 0.0
    sub_url = f"https://{domain}/"
    
    users = state.get("users", {})
    if users:
        first_user_id = list(users.keys())[0]
        info = users[first_user_id]
        used_bytes = info.get("used_bytes", 0)
        used_gb = used_bytes / (1024 ** 3)
        quota = info.get("quota_gb", 0)
        if quota > 0:
            total_gb = quota
            percent = min(round((used_gb / total_gb) * 100, 1), 100.0)
        sub_url = f"https://{domain}/sub/{first_user_id}"

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "state": state,
        "domain": domain,
        "used_traffic": f"{used_gb:.2f} GB",
        "total_traffic": f"{total_gb} GB",
        "traffic_percent": percent,
        "days_left": "20",
        "expire_date": "2026/09/15",
        "sub_url": sub_url,
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login")
async def login(request: Request, password: str = Form(...)):
    ok = password == ADMIN_PASSWORD
    if PANEL_PASSWORD and password != PANEL_PASSWORD:
        ok = False
    if not ok:
        return templates.TemplateResponse("login.html", {"request": request, "error": "رمز اشتباه است"}, status_code=401)
    resp = RedirectResponse(url="/", status_code=302)
    resp.set_cookie(SESSION_COOKIE, SESSION_TOKEN, httponly=True, max_age=86400)
    return resp


@app.get("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie(SESSION_COOKIE)
    return resp


class UserCreate(BaseModel):
    name: str
    quota_gb: float = 0


@app.post("/api/users")
async def create_user(data: UserCreate, request: Request):
    if not require_login(request):
        raise HTTPException(401, "Not authenticated")
    state = load_state()
    user_id = str(uuid.uuid4())
    state["users"][user_id] = {
        "name": data.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "quota_gb": data.quota_gb,
        "used_bytes": 0,
        "disabled": False,
    }
    save_state(state)
    update_xray_config(state)
    return {"id": user_id, "name": data.name}


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, request: Request):
    if not require_login(request):
        raise HTTPException(401, "Not authenticated")
    state = load_state()
    if user_id in state["users"]:
        del state["users"][user_id]
        save_state(state)
        update_xray_config(state)
        return {"ok": True}
    raise HTTPException(404, "User not found")


@app.post("/api/users/{user_id}/toggle")
async def toggle_user(user_id: str, request: Request):
    if not require_login(request):
        raise HTTPException(401, "Not authenticated")
    state = load_state()
    if user_id not in state["users"]:
        raise HTTPException(404, "User not found")
    state["users"][user_id]["disabled"] = not state["users"][user_id].get("disabled", False)
    save_state(state)
    update_xray_config(state)
    return {"disabled": state["users"][user_id]["disabled"]}


@app.get("/api/users/{user_id}/link")
async def user_link(user_id: str, request: Request):
    if not require_login(request):
        raise HTTPException(401, "Not authenticated")
    state = load_state()
    if user_id not in state["users"]:
        raise HTTPException(404, "User not found")
    domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", request.headers.get("host", "your-domain.up.railway.app"))
    name = state["users"][user_id]["name"]
    link = (
        f"vless://{user_id}@{domain}:443"
        f"?type=ws&path=%2Frailvpn&security=tls&sni={domain}"
        f"#{name}"
    )
    return {"link": link}


@app.get("/sub/{user_id}", response_class=Response)
async def subscription(user_id: str):
    state = load_state()
    if user_id not in state["users"]:
        raise HTTPException(404, "User not found")
    info = state["users"][user_id]
    domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "your-domain.up.railway.app")
    link = (
        f"vless://{user_id}@{domain}:443"
        f"?type=ws&path=%2Frailvpn&security=tls&sni={domain}"
        f"#{info['name']}"
    )
    return Response(content=link, media_type="text/plain")


@app.get("/api/stats")
async def stats(request: Request):
    if not require_login(request):
        raise HTTPException(401, "Not authenticated")
    state = load_state()
    out: dict[str, Any] = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for user_id, info in state.get("users", {}).items():
            email = info.get("name", user_id[:8])
            up = down = 0
            try:
                r = await client.get(f"{XRAY_API}/stats/user/{email}")
                if r.status_code == 200:
                    data = r.json()
                    up = data.get("uplink", 0)
                    down = data.get("downlink", 0)
            except Exception:
                pass
            total = up + down
            info["used_bytes"] = total
            out[user_id] = {
                "name": email,
                "uplink": up,
                "downlink": down,
                "total": total,
                "disabled": info.get("disabled", False),
                "quota_gb": info.get("quota_gb", 0),
            }
    save_state(state)

    for user_id, info in state.get("users", {}).items():
        quota_gb = info.get("quota_gb", 0)
        if quota_gb > 0 and info.get("used_bytes", 0) > quota_gb * 1024 ** 3:
            if not info.get("disabled", False):
                info["disabled"] = True
                out[user_id]["disabled"] = True
    save_state(state)
    update_xray_config(state)
    return out


@app.health if hasattr(app, "health") else app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}
